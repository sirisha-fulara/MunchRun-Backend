python -c "
from app import create_app
from app.extensions import db
from app.models.slot import TimeSlot
from app.models.order import Order

app = create_app()
with app.app_context():
    slots = TimeSlot.query.all()
    for slot in slots:
        # count only active orders for this slot
        active_orders = Order.query.filter(
            Order.slot_id == slot.id,
            Order.status.in_(['pending', 'confirmed', 'preparing', 'ready'])
        ).count()
        slot.current_orders = active_orders
        print(f'Slot {slot.slot_time}: {active_orders} active orders')
    db.session.commit()
    print('All slots updated!')
"