from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import decode_token
from app.extensions import socketio, db
from app.models.user import User

#connection event
socketio.on('connect')
def handle_connect():
    print("client connected")
    emit('connected', {'message':'Connected to canto server'})
    
#disconnect event
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    
#join room event
@socketio.on("join")
def handle_join(data):
    try:
        token = data.get("token")
        if not token:
            emit("error", {"message": "Token required"})
            return

        # strip Bearer prefix if someone accidentally includes it
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        # decode token
        from flask import current_app
        decoded = decode_token(token)

        # in newer flask-jwt-extended "sub" is the identity
        user_id = decoded.get("sub")
        if not user_id:
            emit("error", {"message": "Invalid token structure"})
            return

        user = User.query.get(int(user_id))
        if not user:
            emit("error", {"message": "User not found"})
            return

        if user.role == "owner":
            join_room("owner_room")
            emit("joined", {"message": "Joined owner room", "room": "owner_room"})
            print(f"Owner {user.name} joined owner_room")

        elif user.role == "student":
            room_name = f"student_{user.id}"
            join_room(room_name)
            emit("joined", {"message": "Joined your room", "room": room_name})
            print(f"Student {user.name} joined {room_name}")

    except Exception as e:
        print(f"Join error: {str(e)}")  # this will print exact error in terminal
        emit("error", {"message": f"Error: {str(e)}"})


@socketio.on("leave")
def handle_leave(data):
    try:
        token = data.get("token")
        if not token:
            return

        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        decoded = decode_token(token)
        user_id = decoded.get("sub")
        user = User.query.get(int(user_id))

        if not user:
            return

        if user.role == "owner":
            leave_room("owner_room")
            print(f"Owner {user.name} left owner_room")
        elif user.role == "student":
            room_name = f"student_{user.id}"
            leave_room(room_name)
            print(f"Student {user.name} left {room_name}")
    
    except Exception as e:
        print(f"Leave error: {str(e)}")