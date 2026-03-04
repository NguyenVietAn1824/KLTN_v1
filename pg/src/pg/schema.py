from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

from base import BaseModel
from pydantic import ConfigDict
from pydantic import Field

PayloadType = TypeVar('PayloadType', bound=BaseModel)


class RoleType(str, Enum):
    """Enum of user roles available in the system."""
    USER = 'user'
    ADMIN = 'admin'
    STAFF = 'staff'


class UserStatusType(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    BLOCKED = 'blocked'


class ActionType(str, Enum):
    """Enum of possible user actions that can be logged."""
    BUY = 'BUY'
    ADD_TO_CARD = 'ADD_TO_CARD'
    CLICK = 'CLICK'
    SHARE = 'SHARE'
    FEEDBACK = 'FEEDBACK'


class GenderType(str, Enum):
    """Enum of supported gender values for a user."""

    MALE = 'male'
    FEMALE = 'female'


class PolicyRuleType(str, Enum):
    SPONSORED = 'SPONSORED'
    DIVERSITY = 'DIVERSITY'
    UX_FATIGUE = 'UX_FATIGUE'


class RecommendType(str, Enum):
    CONTENT = 'content'
    COLLABORATIVE = 'collaborative'


class ProductStatus(str, Enum):
    PENDING = 'pending'
    VERIFIED = 'verified'
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class StatusCart(str, Enum):
    """Enum of possible cart statuses."""
    ACTIVE = 'Active'
    ORDERED = 'Ordered'
    ABANDONED = 'Abandoned'


class VariantStatus(str, Enum):
    """Enum of product variant statuses."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    OUT_OF_STOCK = 'out_of_stock'


class Identified(BaseModel):
    """Base schema that provides an `id` field for identifiable resources.

    Attributes:
        id: Unique identifier of the resource.
    """

    id: str


class Dated(BaseModel):
    """Mixin schema providing common timestamp fields.

    Attributes:
        createdAt: Creation timestamp.
        updatedAt: Last updated timestamp.
        deletedAt: Deletion timestamp (soft delete).
    """

    createdAt: datetime | None = None
    updatedAt: datetime | None = None
    deletedAt: datetime | None = None


class DatabaseSchema(Identified, Dated):
    """Base schema for all database-backed resources.

    Combines `Identified` and `Dated` and configures Pydantic model behavior
    to allow creation from ORM objects.
    """

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class Conversation(DatabaseSchema):
    """Schema for a conversation between a user and the assistant.

    Attributes:
        user_id: Identifier of the user who started the conversation.
        title: Optional human-readable title for the conversation.
        summary: Summary of the conversation.
    """

    user_id: str
    title: str
    summary: str
    is_confirming: bool = False


class Message(DatabaseSchema):
    """Schema for a single question/answer message in a conversation.

    Attributes:
        conversation_id: Identifier of the parent conversation.
        question: User message text.
        answer: Assistant response text.
    """

    conversation_id: str
    question: str
    answer: str
    additional_info: Optional[dict] = None


class RecommendItems(DatabaseSchema):
    """Schema linking a message to a recommended product.

    Attributes:
        message_id: Identifier of the message that produced the recommendation.
        product_id: Identifier of the recommended product.
    """

    message_id: str
    product_id: str
    type_recommend: RecommendType


class UserAuthentication(DatabaseSchema):
    """Schema for user authentication data.

    Attributes:
        user_id: Identifier of the user.
        username: Name of the user.
        password: Hashed password string for authentication.
        social_id: Optional social login identifier.
        mfa_enabled: Whether multi-factor authentication is enabled.
    """

    user_id: str
    username: str
    password: str
    social_id: Optional[str] | None = None
    mfa_enabled: bool = False


class User(DatabaseSchema):
    """Schema representing an application user.

    Attributes:
        address_id: Identifier of the user's address.
        full_name: Full name of the user.
        email: Email address.
        dob: Date of birth as ISO date string.
        phone: Phone number.
        gender: Gender of the user.
        avt_url: URL to the user's avatar image.
        last_active: Last activation timestamp.
        role: Role assigned to the user.
        status: Status of the user account.
    """

    address_id: Optional[str] | None = None
    full_name: Optional[str] | None = None
    email: str
    dob: datetime | None = None
    phone: Optional[str] | None = None
    gender: Optional[GenderType] | None = None
    avt_url: Optional[str] | None = None
    last_active: datetime
    role: RoleType
    status: Optional[UserStatusType] | None = None


class UserAttribute(DatabaseSchema):
    """Schema for storing summarized attributes or profile data for a user.

    Attributes:
        user_id: Identifier of the user these attributes belong to.
        summarize_attribute: Serialized summary of user attributes.
    """

    user_id: str
    summarize_attribute: str


class HumanActivity(DatabaseSchema):
    """Schema capturing user interactions with products or messages.

    Attributes:
        message_id: Optional identifier of an associated message.
        product_variant_id: Identifier of the product variant involved.
        user_id: Identifier of the user who performed the action.
        action_type: Type of action performed (e.g. BUY, CLICK).
        quantity: Optional numeric quantity related to the action.
    """

    message_id: Optional[str] | None = None
    user_id: str
    product_variant_id: str
    action_type: ActionType
    quantity: Optional[int] | None = None
    search_keyword: Optional[str] | None = None


class Product(DatabaseSchema):
    """Schema describing a product available in the catalog.

    Attributes:
        name: Product name.
        description (Optional): Detailed product description.
        origin (Optional): Country or place of origin.
        thumbnail_url (Optional): URL to the product's thumbnail image.
        image_urls (Optional): List of URLs to additional product images.
        status: Current status of the product.
        brand_id (Optional): Optional identifier of the associated brand.
    """

    name: str
    description: str
    origin: Optional[str] | None = None
    thumbnail_url: Optional[str] | None = None
    image_urls: Optional[list[str]] | None = None
    status: Optional[ProductStatus] | None = None
    brand_id: Optional[str] | None = None


class ProductVariant(DatabaseSchema):
    """Schema for product variants (size, color combinations).

    Attributes:
        product_id: Identifier of the parent product.
        sku: Stock Keeping Unit code.
        barcode: Optional barcode.
        status: Variant availability status.
        price: Variant price.
        image_url: Optional variant-specific image.
        weight_g: Weight in grams.
        attributes: JSONB attributes (size, color, etc.).
    """

    product_id: str
    sku: str
    barcode: Optional[str] = None
    status: VariantStatus = VariantStatus.ACTIVE
    price: float
    image_url: Optional[str] = None
    weight_g: Optional[float] = None
    attributes: Optional[dict] = None


class Inventory(DatabaseSchema):
    """Schema for warehouses/inventory locations.

    Attributes:
        name: Warehouse name.
        code: Unique warehouse code (e.g., KHO_Q1, KHO_MB).
        address_id: Optional address identifier.
        contact_name: Contact person name.
        contact_phone: Contact phone number.
        is_active: Whether warehouse is active.
        priority: Priority for routing/fulfillment.
    """

    name: str
    code: str
    address_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True
    priority: int = 0


class VariantInventory(DatabaseSchema):
    """Schema for variant stock in specific inventory locations.

    Attributes:
        inventory_id: Identifier of the warehouse.
        product_variant_id: Identifier of the product variant.
        stock_on_hand: Actual stock quantity available.
        stock_reserved: Stock reserved for pending orders.
        reorder_point: Threshold for low stock alert.
        last_stocktake_at: Last inventory check timestamp.
    """

    inventory_id: str
    product_variant_id: str
    stock_on_hand: int = 0
    stock_reserved: int = 0
    reorder_point: int = 0
    last_stocktake_at: Optional[datetime] = None


class Brand(DatabaseSchema):
    """Schema for brands/sellers.

    Attributes:
        name: Brand name.
        description: Optional brand description.
        logo_url: Optional URL to brand logo.
        contact_name: Optional contact person name.
        contact_phone: Optional contact phone number.
        address_id: Optional address identifier.
        join_date: Optional date the brand joined the platform.
        last_active: Optional last active timestamp.
        is_verified: Whether the brand is verified.
        meta_title: Optional SEO meta title.
        meta_description: Optional SEO meta description.
    """

    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address_id: Optional[str] = None
    join_date: Optional[datetime] = None
    last_active: Optional[datetime] = None
    is_verified: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class City(DatabaseSchema):

    """Schema for cities belonging to user addresses.
    Attributes:
        name: City name.
        code: City code.
        is_active: Whether the city is active.
    """

    name: str
    code: Optional[str] = None
    is_active: bool = True


class Address(DatabaseSchema):
    """Schema for user addresses.

    Attributes:
        city_id: Identifier of the city.
        region: Region or district within the city.
        country_code: Country code.
        ward: Ward or local administrative unit.
    """

    city_id: Optional[str] | None = None
    region: Optional[str] | None = None
    country_code: Optional[str] | None = None
    ward: Optional[str] | None = None
    detail: Optional[str] | None = None


class ProductCategory(DatabaseSchema):
    """Schema representing the many-to-many relation between products and categories.

    Attributes:
        product_id: Identifier of the product.
        category_id: Identifier of the category.
    """

    product_id: str
    category_id: str


class Category(DatabaseSchema):
    """Schema for product categories.

    Attributes:
        name: Category name from `CategoryType` enum.
        group_id: Identifier of the parent group.
        description: Human readable description of the category.
    """

    group_id: str
    name: str
    description: str


class Group(DatabaseSchema):
    """Schema for grouping categories into higher-level collections.

    Attributes:
        name: Group name
        slug (Optional): URL-friendly slug for the group
        icon_url (Optional): URL to an icon representing the group
        meta_title (Optional): SEO meta title for the group page
        meta_description (Optional): SEO meta description for the group page
    """

    name: str
    slug: Optional[str] | None = None
    icon_url: Optional[str] | None = None
    meta_title: Optional[str] | None = None
    meta_description: Optional[str] | None = None


class PolicyRule(DatabaseSchema):
    """Schema for policy filtering rules.

    Attributes:
        type: Type of rule (SPONSORED, DIVERSITY, UX_FATIGUE, etc.)
        priority: Priority level for rule execution (higher = executed later)
        enabled: Whether the rule is currently active
        start_time: Optional start time for rule activation
        end_time: Optional end time for rule deactivation
        payload: JSON payload containing rule-specific configuration
    """

    type: PolicyRuleType
    priority: Annotated[int, Field(ge=0, le=100)]
    enabled: bool
    start_time: datetime | None
    end_time: datetime | None
    payload: dict


class Order(DatabaseSchema):
    """Schema representing customer orders.

    Attributes:
        - user_id: FK to customer.
        - total_price: Total order value (after discount, before shipping fee).
        - order_status: Order status (Pending, Shipping, Completed, Cancelled).
        - shipping_fee: Shipping cost.
        - subtotal_price: Total before discount/shipping.
        - discount_total: Total discount amount.
        - currency: Currency code (e.g., "VND").
        - payment_status: Payment status (unpaid/paid/refunded) - not solely from payments table.
        - address_id: FK to address.
        - cancel_reason: Cancellation reason (nullable).
    """
    user_id: str
    address_id: str
    total_price: float
    order_status: str
    shipping_fee: float
    subtotal_price: float
    discount_total: float
    currency: str
    payment_status: str
    cancel_reason: Optional[str] | None = None


class OrderItem(DatabaseSchema):
    """Schema representing items within an order.

    Attributes:
        - order_id: FK to order.
        - product_variant_id: FK to product variant.
        - quantity: Quantity purchased.
        - unit_price: Sale price at purchase time (for price history tracking).
    """
    order_id: str
    product_variant_id: str
    quantity: int
    unit_price: float


class Cart(DatabaseSchema):
    """Schema representing customer shopping carts.

    Attributes:
        - user_id: FK to users.
        - status: Cart status (Active, Ordered, Abandoned).
        - total_price: Estimated total price.
        - total_quantity: Total number of items.
    """
    user_id: str
    status: StatusCart
    total_price: float
    total_quantity: int


class CartItem(DatabaseSchema):
    """Schema representing items in a customer's shopping cart.

    Attributes:
        - cart_id: FK to carts.
        - product_variant_id: FK to product_variants.
        - unit_price: Current price.
        - is_selected: Selected for checkout.
    """
    cart_id: str
    product_variant_id: str
    unit_price: float
    is_selected: bool


class Payment(DatabaseSchema):
    """Schema representing payment transactions.

    Attributes:
        - order_id: FK to order.
        - amount: Actual payment amount.
        - payment_method: Payment method (COD, Banking, Momo, Visa, etc.).
        - currency: Currency code (VND, USD).
        - status: Payment status (Pending, Paid, Failed, Refunded).
        - transaction_code: Transaction code from payment gateway.
        - payment_provider: Payment provider (Momo, VnPay, Stripe).
    """
    order_id: str
    amount: float
    payment_method: str
    currency: str
    status: str
    transaction_code: str
    payment_provider: str


class Review(DatabaseSchema):
    """Schema representing customer product reviews.

    Attributes:
        - user_id: FK to users table.
        - product_variant_id: FK to specific product variant (e.g., customer complaining size L is too small).
        - rating: Rating score (1-5 stars).
        - comment: Detailed review comment.
    """
    user_id: str
    product_variant_id: str
    rating: int
    comment: Optional[str] | None = None


class SponsoredPayload(BaseModel):
    """Payload schema for SPONSORED rules.

    Attributes:
        brand_id (str): Brand to boost to target position.
        position (int): Target position (0-based index).
    """
    brand_id: str
    position: int


class DiversityPayload(BaseModel):
    """Payload schema for DIVERSITY rules.

    Attributes:
        max_per_seller (int): Maximum items allowed per seller.
    """
    max_per_seller: int


class UXFatiguePayload(BaseModel):
    """Payload schema for UX_FATIGUE rules.

    Attributes:
        brand_ids (List[str]): List of brand IDs to block/remove.
    """
    brand_ids: List[str]


class TypedPolicyRule(PolicyRule, Generic[PayloadType]):
    """Generic typed rule with validated payload.

    Use with specific payload types for type safety:
    - TypedRule[SponsoredPayload] for SPONSORED rules
    - TypedRule[DiversityPayload] for DIVERSITY rules
    - TypedRule[UXFatiguePayload] for UX_FATIGUE rules

    Type Parameters:
        PayloadType: The specific payload schema for this rule.
    """
    payload: PayloadType


# Type aliases for convenience
SponsoredRule = TypedPolicyRule[SponsoredPayload]
DiversityRule = TypedPolicyRule[DiversityPayload]
UXFatigueRule = TypedPolicyRule[UXFatiguePayload]
