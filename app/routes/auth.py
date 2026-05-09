from flask import Blueprint, request, jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, get_jwt_identity)
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

#register auth
@auth_bp.route("/register", methods=['POST'])
def register():
    data= request.get_json()
    
    #validating fieds
    required= ['name', 'email', 'password', 'phone']
    for field in required:
        if not data.get(field):
            return jsonify({'error':f'{field} is required'}), 400
    
    #checking for already existing mails
    if User.query.filter_by(email= data['email']).first():
        return jsonify({"error": "Email already registered"}), 409
    
    #creating new user
    user= User(
        name= data['name'],
        email= data['email'],
        phone= data['phone'],
        role= data.get('role', 'student')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    #generating tokens
    access_token= create_access_token(identity=str(user.id))
    refresh_token= create_refresh_token(identity=str(user.id))
    
    return jsonify({
        "message": "Registered successfully",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 201
    
    
#login auth
@auth_bp.route('/login', methods=['POST'])
def login():
    data= request.get_json()
    if not data.get('email') or not data.get('password'):
        return jsonify({'error':'Email and password are required'}), 400
    
    user= User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return({'error':'Invalid credentials'}),401
    
    access_token= create_access_token(identity=str(user.id))
    refresh_token= create_refresh_token(identity=str(user.id))
    
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200
 
    
#generating refresh token
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id= get_jwt_identity()
    new_access_token= create_access_token(identity=user_id)
    
    return jsonify({
        "access_token": new_access_token
    }), 200

    
#getting curr user
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": user.to_dict()
    }), 200