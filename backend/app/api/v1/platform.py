from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.domain_models import Address, Delivery, DeliveryPartner, MenuItem, Notification, Order, OrderItem, Parcel, ParcelTracking, Restaurant, RestaurantCategory, SupportTicket
from app.models import User

router = APIRouter(prefix="/api/v1", tags=["platform"])

class AddressIn(BaseModel):
    label: str = "Home"; line1: str; city: str; postal_code: str | None = None
class ParcelIn(BaseModel):
    pickup_address_id: str; drop_address_id: str; package_type: str; weight_kg: Decimal = Field(gt=0); dimensions: str | None = None; delivery_speed: str = "STANDARD"
class MenuItemIn(BaseModel):
    name: str; price: Decimal = Field(gt=0); description: str | None = None; category_id: str | None = None; image_url: str | None = None; is_veg: bool = True; preparation_minutes: int = Field(default=20, ge=1)
class OrderItemIn(BaseModel):
    menu_item_id: str; quantity: int = Field(gt=0, le=50)
class FoodOrderIn(BaseModel):
    restaurant_id: str; delivery_address_id: str; items: list[OrderItemIn]
class StatusIn(BaseModel): status: str

@router.post("/addresses", status_code=201)
def add_address(data: AddressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = Address(user_id=user.id, **data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/addresses")
def addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Address).where(Address.user_id == user.id)).all()

@router.post("/parcels/quote")
def parcel_quote(data: ParcelIn):
    base = Decimal("50.00"); weight_fee = max(Decimal("0"), data.weight_kg - 1) * Decimal("12.00"); speed_fee = Decimal("40.00") if data.delivery_speed.upper() == "EXPRESS" else Decimal("0")
    return {"estimated_price": base + weight_fee + speed_fee, "currency": "INR"}

@router.post("/parcels", status_code=201)
def create_parcel(data: ParcelIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    price = Decimal("50.00") + max(Decimal("0"), data.weight_kg - 1) * Decimal("12.00")
    parcel = Parcel(customer_id=user.id, status="BOOKED", price=price, **data.model_dump()); db.add(parcel); db.flush(); db.add(ParcelTracking(parcel_id=parcel.id, status="BOOKED", note="Parcel booking created")); db.commit(); db.refresh(parcel); return parcel

@router.get("/parcels")
def list_parcels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Parcel).where(Parcel.customer_id == user.id).order_by(Parcel.created_at.desc())).all()

@router.get("/parcels/{parcel_id}/tracking")
def parcel_tracking(parcel_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    parcel = db.scalar(select(Parcel).where(Parcel.id == parcel_id, Parcel.customer_id == user.id))
    if not parcel: raise HTTPException(404, "Parcel not found")
    return db.scalars(select(ParcelTracking).where(ParcelTracking.parcel_id == parcel_id).order_by(ParcelTracking.created_at)).all()

@router.get("/restaurants")
def restaurants(db: Session = Depends(get_db)):
    return db.scalars(select(Restaurant).where(Restaurant.is_approved.is_(True))).all()

@router.get("/restaurants/{restaurant_id}/menu")
def menu(restaurant_id: str, db: Session = Depends(get_db)):
    return db.scalars(select(MenuItem).where(MenuItem.restaurant_id == restaurant_id, MenuItem.is_available.is_(True))).all()

@router.post("/restaurants/{restaurant_id}/menu", status_code=201)
def add_menu_item(restaurant_id: str, data: MenuItemIn, user: User = Depends(require_roles("RESTAURANT_OWNER", "RESTAURANT_STAFF")), db: Session = Depends(get_db)):
    restaurant = db.scalar(select(Restaurant).where(Restaurant.id == restaurant_id, Restaurant.owner_id == user.id))
    if not restaurant: raise HTTPException(403, "Restaurant access denied")
    obj = MenuItem(restaurant_id=restaurant_id, **data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.post("/orders", status_code=201)
def create_food_order(data: FoodOrderIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = []
    total = Decimal("0")
    for item in data.items:
        menu_item = db.scalar(select(MenuItem).where(MenuItem.id == item.menu_item_id, MenuItem.restaurant_id == data.restaurant_id, MenuItem.is_available.is_(True)))
        if not menu_item: raise HTTPException(400, "Menu item unavailable")
        total += menu_item.price * item.quantity; items.append((menu_item, item.quantity))
    order = Order(customer_id=user.id, restaurant_id=data.restaurant_id, delivery_address_id=data.delivery_address_id, order_type="FOOD_ORDER", status="NEW", total_amount=total); db.add(order); db.flush()
    for menu_item, quantity in items: db.add(OrderItem(order_id=order.id, menu_item_id=menu_item.id, name=menu_item.name, quantity=quantity, unit_price=menu_item.price))
    db.commit(); db.refresh(order); return order

@router.get("/orders")
def orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Order).where(Order.customer_id == user.id).order_by(Order.created_at.desc())).all()

@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: str, data: StatusIn, user: User = Depends(require_roles("RESTAURANT_OWNER", "RESTAURANT_STAFF", "ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order: raise HTTPException(404, "Order not found")
    allowed = {"NEW", "ACCEPTED", "PREPARING", "READY_FOR_PICKUP", "PICKED_UP", "COMPLETED"}
    if data.status not in allowed: raise HTTPException(422, "Invalid order status")
    order.status = data.status; db.commit(); return order

@router.get("/deliveries")
def deliveries(user: User = Depends(require_roles("DELIVERY_PARTNER", "ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    partner = db.scalar(select(DeliveryPartner).where(DeliveryPartner.user_id == user.id))
    if not partner: return []
    return db.scalars(select(Delivery).where(Delivery.partner_id == partner.id)).all()

@router.patch("/deliveries/{delivery_id}/status")
def delivery_status(delivery_id: str, data: StatusIn, user: User = Depends(require_roles("DELIVERY_PARTNER", "ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    delivery = db.get(Delivery, delivery_id)
    if not delivery: raise HTTPException(404, "Delivery not found")
    if data.status not in {"ASSIGNED", "ACCEPTED", "REACHED_PICKUP", "PICKED_UP", "IN_TRANSIT", "REACHED_DROP", "DELIVERED"}: raise HTTPException(422, "Invalid delivery status")
    delivery.status = data.status; db.commit(); return delivery

@router.get("/notifications")
def notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())).all()

@router.post("/support", status_code=201)
def support_ticket(subject: str, description: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = SupportTicket(user_id=user.id, subject=subject, description=description); db.add(ticket); db.commit(); db.refresh(ticket); return ticket

@router.get("/admin/dashboard")
def admin_dashboard(user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    return {"users": db.scalar(select(func.count(User.id))), "orders": db.scalar(select(func.count(Order.id))), "revenue": db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0))), "parcels": db.scalar(select(func.count(Parcel.id)))}
