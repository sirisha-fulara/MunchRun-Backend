from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.slot import TimeSlot
from app.models.menu import MenuItem
from app.middleware.auth_middleware import owner_required

admin_bp = Blueprint("admin", __name__)

#get all orders
@admin_bp.route("/users", methods=["GET"])
@owner_required
def get_all_users():
    users = User.query.filter_by(role="student").all()

    return jsonify({
        "total": len(users),
        "users": [user.to_dict() for user in users]
    }), 200
    
#get single user
@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@owner_required
def get_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # get their order history too
    orders = Order.query.filter_by(
        student_id=user_id
    ).order_by(Order.created_at.desc()).limit(10).all()

    return jsonify({
        "user": user.to_dict(),
        "recent_orders": [order.to_dict() for order in orders],
        "total_orders": Order.query.filter_by(student_id=user_id).count()
    }), 200
    

#canten stats
@admin_bp.route("/stats", methods=["GET"])
@owner_required
def get_stats():
    from datetime import date, datetime

    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # today's numbers
    orders_today = Order.query.filter(
        Order.created_at >= start_of_day,
        Order.created_at <= end_of_day
    ).count()

    revenue_today = db.session.query(
        db.func.coalesce(db.func.sum(Order.total_price), 0)
    ).filter(
        Order.created_at >= start_of_day,
        Order.created_at <= end_of_day,
        Order.status != "cancelled"
    ).scalar()

    pending_orders = Order.query.filter(
        Order.status.in_(["pending", "confirmed", "preparing"])
    ).count()

    ready_orders = Order.query.filter_by(status="ready").count()

    total_students = User.query.filter_by(role="student").count()

    total_menu_items = MenuItem.query.filter_by(is_available=True).count()

    return jsonify({
        "today": {
            "orders": orders_today,
            "revenue": float(revenue_today),
        },
        "right_now": {
            "pending_orders": pending_orders,
            "ready_for_pickup": ready_orders,
        },
        "total": {
            "students_registered": total_students,
            "menu_items_available": total_menu_items
        }
    }), 200
    

#reset slot counts at end of day
@admin_bp.route("/slots/reset", methods=["PATCH"])
@owner_required
def reset_slots():
    slots = TimeSlot.query.all()

    for slot in slots:
        slot.current_orders = 0

    db.session.commit()

    return jsonify({
        "message": f"Reset {len(slots)} slots successfully",
        "slots": [slot.to_dict() for slot in slots]
    }), 200
    

#order filters
@admin_bp.route("/orders", methods=["GET"])
@owner_required
def get_all_orders():
    status = request.args.get("status")      # ?status=pending
    date_str = request.args.get("date")      # ?date=2026-05-02

    query = Order.query

    if status:
        query = query.filter_by(status=status)

    if date_str:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start = datetime.combine(filter_date, datetime.min.time())
            end = datetime.combine(filter_date, datetime.max.time())
            query = query.filter(
                Order.created_at >= start,
                Order.created_at <= end
            )
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    orders = query.order_by(Order.created_at.desc()).all()

    return jsonify({
        "total": len(orders),
        "orders": [order.to_dict() for order in orders]
    }), 200