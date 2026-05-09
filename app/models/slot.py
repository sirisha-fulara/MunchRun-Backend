from app.extensions import db

class TimeSlot(db.Model):
    __tablename__ = "time_slots"

    id= db.Column(db.Integer, primary_key=True)
    slot_time= db.Column(db.String(20), nullable=False)
    max_orders= db.Column(db.Integer, default=20)
    current_orders= db.Column(db.Integer, default=0)
    is_active= db.Column(db.Boolean, default=True)

    orders = db.relationship("Order", backref="time_slot", lazy=True)

    def is_full(self):
        return self.current_orders >= self.max_orders

    def to_dict(self):
        return {
            "id": self.id,
            "slot_time": self.slot_time,
            "max_orders": self.max_orders,
            "current_orders": self.current_orders,
            "is_full": self.is_full(),
            "is_active": self.is_active
        }