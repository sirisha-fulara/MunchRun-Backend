from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db, socketio
from app.models.order import Order, OrderItem
from app.models.menu import MenuItem
from app.models.slot import TimeSlot
from app.models.user import User
from app.middleware.auth_middleware import student_required, owner_required

orders_bp = Blueprint("orders", __name__)

#placing order
@orders_bp.route("/", methods=["POST"])
@student_required
def place_order():
    data = request.get_json()
    user_id = get_jwt_identity()

    if not data.get("slot_id"):
        return jsonify({"error": "slot_id is required"}), 400
    if not data.get("items") or len(data["items"]) == 0:
        return jsonify({"error": "Order must have at least one item"}), 400

    slot = TimeSlot.query.get(data["slot_id"])
    if not slot:
        return jsonify({"error": "Slot not found"}), 404
    if not slot.is_active:
        return jsonify({"error": "Slot is not active"}), 400
    if slot.is_full():
        return jsonify({"error": "Slot is full. Please choose another slot"}), 400

    total_price = 0
    order_items_data = []

    for item_data in data["items"]:
        if not item_data.get("menu_item_id") or not item_data.get("quantity"):
            return jsonify({"error": "Each item needs menu_item_id and quantity"}), 400

        menu_item = MenuItem.query.get(item_data["menu_item_id"])

        if not menu_item:
            return jsonify({
                "error": f"Menu item {item_data['menu_item_id']} not found"
            }), 404

        if not menu_item.is_available:
            return jsonify({
                "error": f"{menu_item.name} is currently unavailable"
            }), 400

        quantity = int(item_data["quantity"])
        if quantity <= 0:
            return jsonify({"error": "Quantity must be at least 1"}), 400

        total_price += float(menu_item.price) * quantity
        order_items_data.append({
            "menu_item_id": menu_item.id,
            "quantity": quantity,
            "price_at_order": float(menu_item.price)
        })

    try:
        # create order first
        order = Order(
            student_id=int(user_id),
            slot_id=slot.id,
            total_price=round(total_price, 2),
            status="pending"
        )
        db.session.add(order)
        db.session.flush()  # get order.id

        # create ALL order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_data["menu_item_id"],
                quantity=item_data["quantity"],
                price_at_order=item_data["price_at_order"]
            )
            db.session.add(order_item)

        # increment slot count
        slot.current_orders += 1

        # commit everything together
        db.session.commit()

        # refresh order to load items relationship
        db.session.refresh(order)

        socketio.emit("new_order", order.to_dict(), room="owner_room")

        return jsonify({
            "message": "Order placed successfully",
            "order": order.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Order error: {str(e)}")
        return jsonify({"error": "Failed to place order"}), 500

#getting orders 
@orders_bp.route("/my-orders", methods=["GET"])
@student_required
def my_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(
        student_id=int(user_id)
    ).order_by(Order.created_at.desc()).all()

    return jsonify({
        "orders": [order.to_dict() for order in orders]
    }), 200


#getting single order
@orders_bp.route("/<int:order_id>", methods=["GET"])
@student_required
def get_order(order_id):
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    if user.role == "student" and order.student_id != int(user_id):
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "order": order.to_dict()
    }), 200
    
    
#getting all incoming orders
@orders_bp.route("/incoming", methods=["GET"])
@owner_required
def incoming_orders():
    # get all active orders
    orders = Order.query.filter(
        Order.status.in_(["pending", "confirmed", "preparing", "ready"])
    ).order_by(Order.created_at.asc()).all()

    return jsonify({
        "orders": [order.to_dict() for order in orders]
    }), 200
    
    
@orders_bp.route("/<int:order_id>/status", methods=["PATCH"])
@owner_required
def update_status(order_id):
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json()
    allowed_statuses = ["pending", "confirmed", "preparing", "ready", "picked_up", "cancelled"]

    if not data.get("status"):
        return jsonify({"error": "status is required"}), 400

    if data["status"] not in allowed_statuses:
        return jsonify({
            "error": f"status must be one of {allowed_statuses}"
        }), 400

    old_status = order.status
    order.status = data["status"]

    # if order is picked up or cancelled — free up the slot
    if data["status"] in ["picked_up", "cancelled"] and old_status not in ["picked_up", "cancelled"]:
        slot = TimeSlot.query.get(order.slot_id)
        if slot and slot.current_orders > 0:
            slot.current_orders -= 1

    db.session.commit()

    socketio.emit(
        "order_status_update",
        {
            "order_id": order.id,
            "status": order.status,
            "message": get_status_message(order.status)
        },
        room=f"student_{order.student_id}"
    )

    return jsonify({
        "message": "Order status updated",
        "order": order.to_dict()
    }), 200
    

#cancel order
@orders_bp.route("/<int:order_id>/cancel", methods=["PATCH"])
@student_required
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    # can only cancel own order
    if order.student_id != int(user_id):
        return jsonify({"error": "Unauthorized"}), 403

    # can only cancel if still pending
    if order.status != "pending":
        return jsonify({
            "error": f"Cannot cancel order that is already {order.status}"
        }), 400

    order.status = "cancelled"

    # free up the slot
    slot = TimeSlot.query.get(order.slot_id)
    if slot and slot.current_orders > 0:
        slot.current_orders -= 1

    db.session.commit()

    return jsonify({
        "message": "Order cancelled successfully",
        "order": order.to_dict()
    }), 200
    

#daily summary for owner
@orders_bp.route("/summary", methods=["GET"])
@owner_required
def daily_summary():
    from sqlalchemy import func
    from datetime import date

    today= date.today()
    total_orders= Order.query.filter(
        db.func.date(Order.created_at)==today
    ).count()
    
    revenue= db.session.execute(
        db.text(""" 
            select coalesce(sum(total_price), 0)
            from orders
            where date(created_at)= :today
            and status!='cancelled'
                """),
        {'today': today}
    ).scalar()
    
    #orders by status
    status_counts = db.session.execute(
        db.text("""
            SELECT status, COUNT(*)
            FROM orders
            WHERE DATE(created_at) = :today
            GROUP BY status
        """),
        {"today": today}
    ).fetchall()
    
    # most ordered items today
    popular_items = db.session.execute(
        db.text("""
            SELECT m.name, SUM(oi.quantity) as total_qty
            FROM order_items oi
            JOIN menu_items m ON oi.menu_item_id = m.id
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) = :today
            AND o.status != 'cancelled'
            GROUP BY m.name
            ORDER BY total_qty DESC
            LIMIT 5
        """),
        {"today": today}
    ).fetchall()
    
    return jsonify({
        "date": str(today),
        "total_orders": total_orders,
        "total_revenue": float(revenue),
        "status_breakdown": {row[0]: row[1] for row in status_counts},
        "popular_items": [
            {"name": row[0], "quantity_sold": row[1]}
            for row in popular_items
        ]
    }), 200


#get status mesage
def get_status_message(status):
    messages = {
        "confirmed": "Your order has been confirmed!",
        "preparing": "Your food is being prepared 🍳",
        "ready": "Your order is ready for pickup! 🎉",
        "picked_up": "Enjoy your meal! 😊"
    }
    return messages.get(status, "Order status updated")