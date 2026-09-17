import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, Index
from .database import Base, utcnow


def uid(): return str(uuid.uuid4())

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String(36), primary_key=True, default=uid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = Column(String(32)); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Franchise(Base):
    __tablename__ = "franchises"
    id = Column(String(36), primary_key=True, default=uid)
    name = Column(String(160), nullable=False); code = Column(String(40), unique=True, nullable=False, index=True)
    service_area = Column(String(255)); is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(String(36), primary_key=True, default=uid)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    franchise_id = Column(String(36), ForeignKey("franchises.id"), nullable=True, index=True)
    name = Column(String(160), nullable=False); address = Column(String(255)); is_open = Column(Boolean, default=False, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class RestaurantCategory(Base):
    __tablename__ = "restaurant_categories"
    id = Column(String(36), primary_key=True, default=uid); restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(String(36), primary_key=True, default=uid); restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("restaurant_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(160), nullable=False); description = Column(Text); price = Column(Numeric(12,2), nullable=False)
    image_url = Column(String(500)); is_veg = Column(Boolean, default=True, nullable=False); is_available = Column(Boolean, default=True, nullable=False)
    preparation_minutes = Column(Integer, default=20, nullable=False)

class Address(Base):
    __tablename__ = "addresses"
    id = Column(String(36), primary_key=True, default=uid); user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(50)); line1 = Column(String(255), nullable=False); city = Column(String(100), nullable=False); postal_code = Column(String(20)); latitude = Column(Numeric(10,7)); longitude = Column(Numeric(10,7))

class Order(Base):
    __tablename__ = "orders"
    id = Column(String(36), primary_key=True, default=uid); customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"), nullable=True, index=True); order_type = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True); total_amount = Column(Numeric(12,2), nullable=False); delivery_address_id = Column(String(36), ForeignKey("addresses.id")); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False); updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(String(36), primary_key=True, default=uid); order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True); menu_item_id = Column(String(36), ForeignKey("menu_items.id"), nullable=True); name = Column(String(160), nullable=False); quantity = Column(Integer, nullable=False); unit_price = Column(Numeric(12,2), nullable=False)

class Parcel(Base):
    __tablename__ = "parcels"
    id = Column(String(36), primary_key=True, default=uid); customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True); pickup_address_id = Column(String(36), ForeignKey("addresses.id")); drop_address_id = Column(String(36), ForeignKey("addresses.id")); package_type = Column(String(80), nullable=False); weight_kg = Column(Numeric(10,2), nullable=False); dimensions = Column(String(100)); delivery_speed = Column(String(30), nullable=False); price = Column(Numeric(12,2), nullable=False); status = Column(String(32), nullable=False, index=True); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class ParcelTracking(Base):
    __tablename__ = "parcel_tracking"
    id = Column(String(36), primary_key=True, default=uid); parcel_id = Column(String(36), ForeignKey("parcels.id", ondelete="CASCADE"), nullable=False, index=True); status = Column(String(32), nullable=False); note = Column(String(255)); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"
    id = Column(String(36), primary_key=True, default=uid); user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False); is_online = Column(Boolean, default=False, nullable=False); vehicle_type = Column(String(50)); document_status = Column(String(30), default="PENDING"); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(String(36), primary_key=True, default=uid); order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True); parcel_id = Column(String(36), ForeignKey("parcels.id", ondelete="CASCADE"), nullable=True, index=True); partner_id = Column(String(36), ForeignKey("delivery_partners.id"), nullable=True, index=True); status = Column(String(32), nullable=False, index=True); proof_of_delivery = Column(String(500)); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=uid); order_id = Column(String(36), ForeignKey("orders.id"), nullable=True); parcel_id = Column(String(36), ForeignKey("parcels.id"), nullable=True); amount = Column(Numeric(12,2), nullable=False); status = Column(String(30), default="PENDING", nullable=False); transaction_id = Column(String(120)); refund_status = Column(String(30)); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, default=uid); user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True); title = Column(String(160), nullable=False); body = Column(Text, nullable=False); is_read = Column(Boolean, default=False, nullable=False); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(String(36), primary_key=True, default=uid); user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True); subject = Column(String(160), nullable=False); description = Column(Text, nullable=False); status = Column(String(30), default="OPEN", nullable=False); created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
