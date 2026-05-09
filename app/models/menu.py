from app.extensions import db
from datetime import datetime

class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id= db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(100), nullable=False)
    description= db.Column(db.String(255), nullable=True)
    price= db.Column(db.Numeric(10, 2), nullable=False)
    category= db.Column(db.String(50), nullable=False)  # breakfast, lunch, snacks, drinks
    is_available= db.Column(db.Boolean, default=True)
    image_url= db.Column(db.String(255), nullable=True)
    created_at= db.Column(db.DateTime, default=datetime.now)

    order_items = db.relationship("OrderItem", backref="menu_item", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "category": self.category,
            "is_available": self.is_available,
            "image_url": self.image_url
        }