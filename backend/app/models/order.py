from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Order(Base):
    """Demo order. No payment is taken and nothing is delivered."""

    __tablename__ = "orders"

    # Random UUID so order ids cannot be guessed or enumerated.
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    customer_name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(300))
    delivery_slot: Mapped[str] = mapped_column(String(20))
    payment_method: Mapped[str] = mapped_column(String(30), default="cash_on_delivery_demo")
    total_paise: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="placed_demo")
    # Set when the customer was logged in; guest checkout leaves it empty.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.id"
    )


class OrderItem(Base):
    """Snapshot of what was bought: name, unit and price are copied so later price changes
    never alter a past order."""

    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[int]
    unit_price_paise: Mapped[int]
    line_total_paise: Mapped[int]

    order: Mapped[Order] = relationship(back_populates="items")
