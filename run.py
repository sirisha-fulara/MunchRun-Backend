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
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=False, host="0.0.0.0", port=port)