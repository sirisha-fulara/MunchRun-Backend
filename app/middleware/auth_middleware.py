from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from app.models.user import User

def student_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id= get_jwt_identity()
        user= User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user.role!='student':
            return jsonify({'error': 'Student access only'}), 403
        return fn(*args, **kwargs)
    return wrapper

def owner_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id= get_jwt_identity()
        user= User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user.role!='owner':
            return jsonify({'error': 'Owner access only'}), 403
        return fn(*args, **kwargs)
    return wrapper
        
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id= get_jwt_identity()
        user= User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return fn(*args, **kwargs)
    return wrapper