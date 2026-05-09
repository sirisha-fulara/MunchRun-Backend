from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.slot import TimeSlot
from app.middleware.auth_middleware import owner_required

slot_bp= Blueprint('slots', __name__)

#getting all active slots
@slot_bp.route('/', methods=['GET'])
def get_slots():
    slots= TimeSlot.query.filter_by(is_active=True).all()
    return jsonify({
        'slots': [slot.to_dict() for slot in slots]
    }), 200
    

#adding a slot
@slot_bp.route('/', methods=['POST'])
@owner_required
def add_slot():
    data= request.get_json()
    if not data.get("slot_time"):
        return jsonify({'error':"slot_time is required"}), 400
    
    existing= TimeSlot.query.filter_by(slot_time= data['slot_time']).first()
    if existing:
        return jsonify({'error':'slot alredy exists'}), 409
    
    slot= TimeSlot(
        slot_time= data['slot_time'],
        max_orders= data.get('max_orders', 20)
    )
    
    db.session.add(slot)
    db.session.commit()
    
    return jsonify({
        'message':'Slot created successfully',
        'slot': slot.to_dict()
    }), 201
    

#update slot cpcity
@slot_bp.route('/<int:slot_id>', methods=['PUT'])
@owner_required
def update_slot(slot_id):
    slot= TimeSlot.query.get(slot_id)
    if not slot:
        return jsonify({'error':'Slot not found'}), 404
    
    data= request.get_json()
    
    if 'max_orders' in data:
        slot.max_orders= data['max_orders']
    
    if 'is_active' in data:
        slot.is_active= data['is_active']
        
    db.session.commit()
    
    return jsonify({
        "message": "Slot updated",
        "slot": slot.to_dict()
    }), 200


#delete slot
@slot_bp.route('/<int:slot_id>', methods=['DELETE'])
@owner_required
def delete_slot(slot_id):
    slot= TimeSlot.query.get(slot_id)
    
    if not slot:
        return jsonify({'error':'Slot not found'}), 404
    
    db.session.delete(slot)
    db.session.commit()
    
    return jsonify({
        'message':'Slot deleted successfully'
    }), 200