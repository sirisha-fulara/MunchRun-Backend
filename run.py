# from app import create_app
# from app.extensions import socketio

# app= create_app()

# if(__name__=='__main__'):
#     socketio.run(app, debug=True, port=5000)

# Run this once to create all tables
# you can run it from python shell or add temporarily to run.py

from app import create_app
from app.extensions import socketio, db

app = create_app()

@app.route('/')
def health():
    return({'status':'backend running'}),200

with app.app_context():
    from app.models.user import User
    from app.models.slot import TimeSlot
    from app.models.menu import MenuItem
    from app.models.order import Order, OrderItem
    
    db.create_all()
    print("Tables created!")

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)