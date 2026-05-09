from app.extensions import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = "orders"

    id= db.Column(db.Integer, primary_key=True)
    student_id= db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_id= db.Column(db.Integer, db.ForeignKey("time_slots.id"), nullable=False)
    status= db.Column(db.String(30), default="pending")
    # pending ,confirmed, preparing, ready, picked_up
    total_price= db.Column(db.Numeric(10, 2), nullable=False)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "slot_id": self.slot_id,
            "status": self.status,
            "total_price": float(self.total_price),
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = "order_items"

    id= db.Column(db.Integer, primary_key=True)
    order_id= db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id= db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity= db.Column(db.Integer, nullable=False)
    price_at_order= db.Column(db.Numeric(10, 2), nullable=False)
    # store price at time of order and menu price can change later

    def to_dict(self):
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "menu_item_name": self.menu_item.name,
            "quantity": self.quantity,
            "price_at_order": float(self.price_at_order)
        }