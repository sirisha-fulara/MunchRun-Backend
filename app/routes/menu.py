from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.menu import MenuItem
from app.middleware.auth_middleware import owner_required, login_required

menu_bp = Blueprint("menu", __name__)

#getting all menu items
@menu_bp.route('/', methods=['GET'])
def get_menu():
    category= request.args.get('category')
    if category:
        items= MenuItem.query.filter_by(
            category=category,
            is_available= True
        ).all()
    else:
        items= MenuItem.query.filter_by(is_available=True).all()
    
    if not items:
        return jsonify({
            "message": "No items found",
            "items": []
        }), 200

    return jsonify({
        "items": [item.to_dict() for item in items]
    }), 200
    

#getting single item
@menu_bp.route('/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    item= MenuItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    return jsonify({
        'item': item.to_dict()
    }), 200
   
 
#getting all catgories 
@menu_bp.route('/categories', methods=['GET'])
def get_categories():
    categories= db.session.execute(db.text('SELECT DISTINCT category FROM menu_items')).fetchall()
    
    return jsonify({
        "categories": [row[0] for row in categories]
    }), 200
    

@menu_bp.route('/', methods=['POST'])
@owner_required
def add_menu_item():
    data= request.get_json()
    
    #validatinf fields
    required= ['name', 'price', 'category']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f"{field} is required"}), 400
    
    #validating categories 
    allowed_categories = ["breakfast", "lunch", "snacks", "drinks"]
    if data["category"] not in allowed_categories:
        return jsonify({
            "error": f"category must be one of {allowed_categories}"
        }), 400
    
    #validate price   
    try:
        price = float(data["price"])
        if price <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "price must be a positive number"}), 400
        
    item= MenuItem(
        name= data['name'],
        description= data.get('description', ""),
        price= price,
        category= data['category'],
        image_url= data.get('image_url', ""),
        is_available= True
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({
        "message": "Menu item added successfully",
        "item": item.to_dict()
    }), 201


#updating menu
@menu_bp.route("/<int:item_id>", methods=["PUT"])
@owner_required
def update_menu_item(item_id):
    item = MenuItem.query.get(item_id)

    if not item:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json()

    # only update fields that are provided
    if "name" in data:
        item.name = data["name"]
    if "description" in data:
        item.description = data["description"]
    if "price" in data:
        try:
            price = float(data["price"])
            if price <= 0:
                raise ValueError
            item.price = price
        except (ValueError, TypeError):
            return jsonify({"error": "price must be a positive number"}), 400
    if "category" in data:
        allowed_categories = ["breakfast", "lunch", "snacks", "drinks"]
        if data["category"] not in allowed_categories:
            return jsonify({
                "error": f"category must be one of {allowed_categories}"
            }), 400
        item.category = data["category"]
    if "image_url" in data:
        item.image_url = data["image_url"]

    db.session.commit()

    return jsonify({
        "message": "Menu item updated successfully",
        "item": item.to_dict()
    }), 200


#availabitlity check
@menu_bp.route("/<int:item_id>/toggle", methods=["PATCH"])
@owner_required
def toggle_availability(item_id):
    item = MenuItem.query.get(item_id)

    if not item:
        return jsonify({"error": "Item not found"}), 404

    # flip availability
    item.is_available = not item.is_available
    db.session.commit()

    status = "available" if item.is_available else "unavailable"

    return jsonify({
        "message": f"{item.name} marked as {status}",
        "item": item.to_dict()
    }), 200
    
#deleting menu item
@menu_bp.route("/<int:item_id>", methods=["DELETE"])
@owner_required
def delete_menu_item(item_id):
    item = MenuItem.query.get(item_id)

    if not item:
        return jsonify({"error": "Item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "message": f"{item.name} deleted successfully"
    }), 200