from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy ORM models."""


class Dated(Base):
    __abstract__ = True
    """Mixin adding common timestamp columns to ORM models.

    Columns:
        createdAt: Timestamp when the row was created.
        updatedAt: Timestamp when the row was last updated.
        deletedAt: Nullable timestamp used for soft deletes.
    """

    createdAt: Mapped[datetime] = mapped_column(insert_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(onupdate=func.now(), nullable=True)
    deletedAt: Mapped[datetime] = mapped_column(nullable=True)


class Identified(Base):

    __abstract__ = True
    """Mixin providing a string primary key column named `id`."""

    id: Mapped[str] = mapped_column(primary_key=True, index=True)


class Conversation(Identified, Dated):

    __tablename__ =  'conversation'
    """ORM model for a conversation.

    Columns:
        user_id: Foreign key to the `user` table.
        title: Title of the conversation.
        summary: Summary of the conversation.
    """

    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    title: Mapped[str]
    summary: Mapped[str]
    is_confirming: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text('false'),
    )


class Message(Identified, Dated):

    __tablename__ = 'message'
    """ORM model for messages in a conversation.

    Columns:
        conversation_id: Foreign key to the `conversation` table.
        question: The user's question text.
        answer: The assistant's answer text.
    """

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey('conversation.id', ondelete='CASCADE'),
        nullable=False,
    )

    question: Mapped[str]
    answer: Mapped[str]
    additional_info: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )


class RecommendItems(Identified, Dated):

    __tablename__ = 'recommend_items'
    """ORM model linking messages to recommended product."""

    message_id: Mapped[str] = mapped_column(
        ForeignKey('message.id', ondelete='CASCADE'),
        nullable=False,
    )

    product_id: Mapped[str] = mapped_column(
        ForeignKey('product.id', ondelete='CASCADE'),
        nullable=False,
    )

    type_recommend: Mapped[str] = mapped_column(
        nullable=False,
    )


class User(Identified, Dated):

    __tablename__ = 'user'
    """ORM model representing an application user.

    Columns capture personal information and role metadata.
    """
    address_id: Mapped[str] = mapped_column(
        ForeignKey('addresses.id', ondelete='SET NULL'),
        nullable=True,
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    email: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
    )
    dob: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    gender: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    avt_url: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    role: Mapped[str] = mapped_column(
        nullable=False,
    )
    status: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )


class UserAuthentication(Identified, Dated):

    __tablename__ = 'user_authentications'
    """ORM model for user authentication data.

    Columns:
        username: Email of the user (used for login, must match user.email).
        password: Hashed password string for authentication.
    """
    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )
    password: Mapped[str] = mapped_column(
        nullable=False,
    )
    social_id: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text('false'),
    )


class UserAttribute(Identified, Dated):

    __tablename__ = 'user_attributes'
    """ORM model storing summarized attributes for user."""

    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )

    summarize_attribute: Mapped[str] = mapped_column(
        nullable=True,
    )


class HumanActivity(Identified, Dated):

    __tablename__ = 'human_activities'
    """ORM model capturing user actions for analytics and logs.
    Columns:
        message_id: Optional identifier of an associated message.
        product_variant_id: Identifier of the product variant involved.
        user_id: Identifier of the user who performed the action.
        action_type: Type of action performed (e.g. BUY, CLICK).
        quantity: Optional numeric quantity related to the action.
        search_keyword: Optional search keyword used by the user.
    """

    message_id: Mapped[str] = mapped_column(
        ForeignKey('message.id', ondelete='CASCADE'),
        nullable=True,
    )

    product_variant_id: Mapped[str] = mapped_column(
        ForeignKey('product_variants.id', ondelete='CASCADE'),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )

    action_type: Mapped[str] = mapped_column(
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=True,
    )
    search_keyword: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )


class Product(Identified, Dated):

    __tablename__ = 'product'
    """ORM model for a catalog product."""

    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        nullable=False,
    )
    origin: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    image_urls: Mapped[Optional[list[str]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    status: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    brand_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey('brands.id', ondelete='SET NULL'),
        nullable=True,
    )


class ProductVariant(Identified, Dated):

    __tablename__ = 'product_variants'
    """ORM model for product variants (size, color combinations)."""

    product_id: Mapped[str] = mapped_column(
        ForeignKey('product.id', ondelete='CASCADE'),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        nullable=False, default='active',
    )
    price: Mapped[float] = mapped_column(
        nullable=False,
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    weight_g: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    attributes: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )


class Inventory(Identified, Dated):

    __tablename__ = 'inventories'
    """ORM model for warehouses/inventory locations."""

    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        nullable=False, unique=True,
    )
    address_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey('addresses.id', ondelete='SET NULL'),
        nullable=True,
    )
    contact_name: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
    priority: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )


class VariantInventory(Identified, Dated):

    __tablename__ = 'variant_inventories'
    """ORM model for variant stock in specific inventory locations."""

    inventory_id: Mapped[str] = mapped_column(
        ForeignKey('inventories.id', ondelete='CASCADE'),
        nullable=False,
    )
    product_variant_id: Mapped[str] = mapped_column(
        ForeignKey('product_variants.id', ondelete='CASCADE'),
        nullable=False,
    )
    stock_on_hand: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    stock_reserved: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    reorder_point: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    last_stocktake_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )


class Brand(Identified, Dated):

    __tablename__ = 'brands'
    """ORM model for brands/sellers."""

    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    contact_name: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    address_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey('addresses.id', ondelete='SET NULL'),
        nullable=True,
    )
    join_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    last_active: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        default=False,
    )
    meta_title: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )


class City(Identified, Dated):

    __tablename__ = 'city'
    """ORM model for city belonging to user addresses."""

    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    code: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text('true'),
    )


class Address(Identified, Dated):

    __tablename__ = 'addresses'
    """ORM model for user addresses."""

    city_id: Mapped[str] = mapped_column(
        ForeignKey('city.id', ondelete='SET NULL'),
        nullable=True,
    )
    region: Mapped[str] = mapped_column(
        nullable=True,
    )

    country_code: Mapped[str] = mapped_column(
        nullable=True,
    )
    ward: Mapped[str] = mapped_column(
        nullable=True,
    )

    detail: Mapped[str] = mapped_column(
        nullable=False,
    )


class ProductCategory(Identified, Dated):

    __tablename__ = 'product_categories'
    """ORM model representing product to category assignments."""

    product_id: Mapped[str] = mapped_column(
        ForeignKey('product.id', ondelete='CASCADE'),
        nullable=False,
    )

    category_id: Mapped[str] = mapped_column(
        ForeignKey('category.id', ondelete='CASCADE'),
        nullable=False,
    )


class Category(Identified, Dated):

    __tablename__ = 'category'
    """ORM model for a product category."""

    group_id: Mapped[str] = mapped_column(
        ForeignKey('group.id', ondelete='CASCADE'),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        nullable=False,
    )


class Group(Identified, Dated):

    __tablename__ = 'group'
    """ORM model grouping category into higher-level collections."""

    name: Mapped[str] = mapped_column(
        nullable=False,
    )

    slug: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    icon_url: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    meta_title: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        nullable=True,
    )


class PolicyRule(Identified, Dated):

    __tablename__ = 'policy_rule'
    """ORM model for policy filtering rules.

    Columns:
        type: Type of rule (SPONSORED, DIVERSITY, UX_FATIGUE, etc.)
        priority: Priority level for rule execution (higher = executed later)
        enabled: Whether the rule is currently active
        start_time: Optional start time for rule activation
        end_time: Optional end time for rule deactivation
        payload: JSON payload containing rule-specific configuration
    """

    type: Mapped[str] = mapped_column(nullable=False)
    priority: Mapped[int] = mapped_column(nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Order(Identified, Dated):

    __tablename__ = 'orders'
    """ORM model for user orders.
    Columns:
        - user_id: FK to customer.
        - total_price: Total order value (after discount, before shipping fee).
        - order_status: Status (Pending, Shipping, Completed, Cancelled).
        - shipping_fee: Shipping cost.
        - subtotal_price: Total before discount/shipping.
        - discount_total: Total discount amount.
        - currency: Currency code (e.g., "VND").
        - payment_status: Payment status (unpaid/paid/refunded) - not solely from payments table.
        - address_id: FK to address.
        - cancel_reason: Reason for cancellation (nullable).
    """
    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    address_id: Mapped[str] = mapped_column(
        ForeignKey('addresses.id', ondelete='SET NULL'),
        nullable=True,
    )
    total_price: Mapped[float] = mapped_column(nullable=False)
    order_status: Mapped[str] = mapped_column(nullable=False)
    shipping_fee: Mapped[float] = mapped_column(nullable=False)
    subtotal_price: Mapped[float] = mapped_column(nullable=False)
    discount_total: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False, default='VND')
    payment_status: Mapped[str] = mapped_column(nullable=False)

    cancel_reason: Mapped[Optional[str]] = mapped_column(nullable=True)


class OrderItem(Identified, Dated):

    __tablename__ = 'order_items'
    """ORM model for items in an order.

    Columns:
        - order_id: FK to order.
        - product_variant_id: FK to product variant.
        - quantity: Quantity purchased.
        - unit_price: Sale price at purchase time (for price history tracking).
    """
    order_id: Mapped[str] = mapped_column(
        ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False,
    )
    product_variant_id: Mapped[str] = mapped_column(
        ForeignKey('product_variants.id', ondelete='CASCADE'),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(nullable=False)


class Cart(Identified, Dated):
    __tablename__ = 'carts'

    """ORM model for user shopping carts.

    Columns:
        - user_id: FK to user.
        - status: Cart status (Active, Ordered, Abandoned).
        - total_price: Estimated total price.
        - total_quantity: Total number of items.
    """
    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(nullable=False, default='Active')
    total_price: Mapped[float] = mapped_column(nullable=False, default=0.0)
    total_quantity: Mapped[int] = mapped_column(nullable=False, default=0)


class CartItem(Identified, Dated):
    __tablename__ = 'cart_items'
    """ORM model for items in a shopping cart.

    Columns:
        - cart_id: FK to carts.
        - product_variant_id: FK to product_variants.
        - unit_price: Current price.
        - is_selected: Selected for checkout.
    """
    cart_id: Mapped[str] = mapped_column(
        ForeignKey('carts.id', ondelete='CASCADE'),
        nullable=False,
    )
    product_variant_id: Mapped[str] = mapped_column(
        ForeignKey('product_variants.id', ondelete='CASCADE'),
        nullable=False,
    )
    unit_price: Mapped[float] = mapped_column(nullable=False)
    is_selected: Mapped[bool] = mapped_column(nullable=False, default=False)


class Payment(Identified, Dated):
    __tablename__ = 'payments'
    """ORM model for payment transactions.

    Columns:
        - order_id: FK to order.
        - amount: Actual payment amount.
        - payment_method: Payment method (COD, Banking, Momo, Visa, etc.).
        - currency: Currency code (VND, USD).
        - status: Payment status (Pending, Paid, Failed, Refunded).
        - transaction_code: Transaction code from payment gateway.
        - payment_provider: Payment provider (Momo, VnPay, Stripe).
    """
    order_id: Mapped[str] = mapped_column(
        ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(nullable=False)
    payment_method: Mapped[str] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    transaction_code: Mapped[str] = mapped_column(nullable=False)
    payment_provider: Mapped[str] = mapped_column(nullable=False)


class Review(Identified, Dated):
    __tablename__ = 'reviews'
    """ORM model for product reviews.

    Columns:
        - user_id: FK to user.
        - product_variant_id: FK to product variant.
        - rating: Rating from 1 to 5 stars.
        - comment: Detailed comment.
    """
    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    product_variant_id: Mapped[str] = mapped_column(
        ForeignKey('product_variants.id', ondelete='CASCADE'),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(nullable=True)
