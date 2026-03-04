from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from sqlalchemy.orm import Session

from ..schema import Address
from ..schema import Brand
from ..schema import Cart
from ..schema import CartItem
from ..schema import Category
from ..schema import City
from ..schema import Conversation
from ..schema import Group
from ..schema import HumanActivity
from ..schema import Inventory
from ..schema import Message
from ..schema import Order
from ..schema import OrderItem
from ..schema import Payment
from ..schema import Product
from ..schema import ProductCategory
from ..schema import ProductVariant
from ..schema import RecommendItems
from ..schema import Review
from ..schema import User
from ..schema import UserAttribute
from ..schema import VariantInventory


class Repository(ABC):
    """Abstract repository interface declaring CRUD operations for all models.

    Each concrete controller implements these methods for a particular resource
    type (e.g. User, Product). Methods follow a consistent naming scheme and
    operate on SQLAlchemy `Session` objects.
    """
    # Conversation
    @abstractmethod
    def insert_conversation(self, session: Session, model: Conversation) -> Conversation:
        """Insert a Conversation and return the created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_conversation(self, session: Session, model: Conversation) -> Conversation | None:
        """Update a Conversation and return the updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_conversation(self, session: Session, id: str) -> Conversation | None:
        """Delete a Conversation by id and return the deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_conversation_by_id(self, session: Session, id: str) -> Conversation | None:
        """Get a Conversation by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_conversations(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Conversation] | None:
        """Get Conversations with optional filters; return list or None."""
        raise NotImplementedError()

    # Message
    @abstractmethod
    def insert_message(self, session: Session, model: Message) -> Message:
        """Insert a Message and return the created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_message(self, session: Session, model: Message) -> Message | None:
        """Update a Message and return the updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_message(self, session: Session, id: str) -> Message | None:
        """Delete a Message by id and return the deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_message_by_id(self, session: Session, id: str) -> Message | None:
        """Get a Message by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_messages(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Message] | None:
        """Get Messages with optional filters; return list or None."""
        raise NotImplementedError()

    # RecommendItems
    @abstractmethod
    def insert_recommend_items(self, session: Session, model: RecommendItems) -> RecommendItems:
        """Insert RecommendItems and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_recommend_items(self, session: Session, model: RecommendItems) -> RecommendItems | None:
        """Update RecommendItems and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_recommend_items(self, session: Session, id: str) -> RecommendItems | None:
        """Delete RecommendItems by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_recommend_items_by_id(self, session: Session, id: str) -> RecommendItems | None:
        """Get RecommendItems by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_recommend_items(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[RecommendItems] | None:
        """Get RecommendItems with optional filters; return list or None."""
        raise NotImplementedError()

    # User
    @abstractmethod
    def insert_user(self, session: Session, model: User) -> User:
        """Insert a User and return the created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_user(self, session: Session, model: User) -> User | None:
        """Update a User and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_user(self, session: Session, id: str) -> User | None:
        """Delete a User by id and return the deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_id(self, session: Session, id: str) -> User | None:
        """Get a User by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_users(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[User] | None:
        """Get Users with optional filters; return list or None."""
        raise NotImplementedError()

    # UserAttribute
    @abstractmethod
    def insert_user_attribute(self, session: Session, model: UserAttribute) -> UserAttribute:
        """Insert a UserAttribute and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_user_attribute(self, session: Session, model: UserAttribute) -> UserAttribute | None:
        """Update a UserAttribute and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_user_attribute(self, session: Session, id: str) -> UserAttribute | None:
        """Delete a UserAttribute by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_user_attribute_by_id(self, session: Session, id: str) -> UserAttribute | None:
        """Get a UserAttribute by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_user_attributes(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[UserAttribute] | None:
        """Get UserAttributes with optional filters; return list or None."""
        raise NotImplementedError()

    # HumanActivity
    @abstractmethod
    def insert_human_activity(self, session: Session, model: HumanActivity) -> HumanActivity:
        """Insert a HumanActivity and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_human_activity(self, session: Session, model: HumanActivity) -> HumanActivity | None:
        """Update a HumanActivity and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_human_activity(self, session: Session, id: str) -> HumanActivity | None:
        """Delete a HumanActivity by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_human_activity_by_id(self, session: Session, id: str) -> HumanActivity | None:
        """Get a HumanActivity by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_human_activities(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[HumanActivity] | None:
        """Get HumanActivitys with optional filters; return list or None."""
        raise NotImplementedError()

    # Product
    @abstractmethod
    def insert_product(self, session: Session, model: Product) -> Product:
        """Insert a Product and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_product(self, session: Session, model: Product) -> Product | None:
        """Update a Product and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_product(self, session: Session, id: str) -> Product | None:
        """Delete a Product by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_product_by_id(self, session: Session, id: str) -> Product | None:
        """Get a Product by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_products(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Product] | None:
        """Get Products with optional filters; return list or None."""
        raise NotImplementedError()

    # ProductCategory
    @abstractmethod
    def insert_product_category(self, session: Session, model: ProductCategory) -> ProductCategory:
        """Insert a ProductCategory and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_product_category(self, session: Session, model: ProductCategory) -> ProductCategory | None:
        """Update a ProductCategory and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_product_category(self, session: Session, id: str) -> ProductCategory | None:
        """Delete a ProductCategory by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_product_category_by_id(self, session: Session, id: str) -> ProductCategory | None:
        """Get a ProductCategory by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_product_categories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[ProductCategory] | None:
        """Get ProductCategories with optional filters; return list or None."""
        raise NotImplementedError()

    # Category
    @abstractmethod
    def insert_category(self, session: Session, model: Category) -> Category:
        """Insert a Category and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_category(self, session: Session, model: Category) -> Category | None:
        """Update a Category and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_category(self, session: Session, id: str) -> Category | None:
        """Delete a Category by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_category_by_id(self, session: Session, id: str) -> Category | None:
        """Get a Category by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_categories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Category] | None:
        """Get Categories with optional filters; return list or None."""
        raise NotImplementedError()

    # Group
    @abstractmethod
    def insert_group(self, session: Session, model: Group) -> Group:
        """Insert a Group and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_group(self, session: Session, model: Group) -> Group | None:
        """Update a Group and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_group(self, session: Session, id: str) -> Group | None:
        """Delete a Group by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_group_by_id(self, session: Session, id: str) -> Group | None:
        """Get a Group by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_groups(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Group] | None:
        """Get Groups with optional filters; return list or None."""
        raise NotImplementedError()

    # Order
    @abstractmethod
    def insert_order(self, session: Session, model: Order) -> Order:
        """Insert an Order and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_order(self, session: Session, model: Order) -> Order | None:
        """Update an Order and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_order(self, session: Session, id: str) -> Order | None:
        """Delete an Order by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_order_by_id(self, session: Session, id: str) -> Order | None:
        """Get an Order by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_orders(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Order] | None:
        """Get Orders with optional filters; return list or None."""
        raise NotImplementedError()

    # OrderItem
    @abstractmethod
    def insert_order_item(self, session: Session, model: OrderItem) -> OrderItem:
        """Insert an OrderItem and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_order_item(self, session: Session, model: OrderItem) -> OrderItem | None:
        """Update an OrderItem and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_order_item(self, session: Session, id: str) -> OrderItem | None:
        """Delete an OrderItem by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_order_item_by_id(self, session: Session, id: str) -> OrderItem | None:
        """Get an OrderItem by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_order_items(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[OrderItem] | None:
        """Get OrderItems with optional filters; return list or None."""
        raise NotImplementedError()

    # Cart
    @abstractmethod
    def insert_cart(self, session: Session, model: Cart) -> Cart:
        """Insert a Cart and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_cart(self, session: Session, model: Cart) -> Cart | None:
        """Update a Cart and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_cart(self, session: Session, id: str) -> Cart | None:
        """Delete a Cart by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_cart_by_id(self, session: Session, id: str) -> Cart | None:
        """Get a Cart by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_carts(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Cart] | None:
        """Get Carts with optional filters; return list or None."""
        raise NotImplementedError()

    # CartItem
    @abstractmethod
    def insert_cart_item(self, session: Session, model: CartItem) -> CartItem:
        """Insert a CartItem and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_cart_item(self, session: Session, model: CartItem) -> CartItem | None:
        """Update a CartItem and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_cart_item(self, session: Session, id: str) -> CartItem | None:
        """Delete a CartItem by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_cart_item_by_id(self, session: Session, id: str) -> CartItem | None:
        """Get a CartItem by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_cart_items(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[CartItem] | None:
        """Get CartItems with optional filters; return list or None."""
        raise NotImplementedError()

    # Payment
    @abstractmethod
    def insert_payment(self, session: Session, model: Payment) -> Payment:
        """Insert a Payment and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_payment(self, session: Session, model: Payment) -> Payment | None:
        """Update a Payment and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_payment(self, session: Session, id: str) -> Payment | None:
        """Delete a Payment by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_payment_by_id(self, session: Session, id: str) -> Payment | None:
        """Get a Payment by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_payments(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Payment] | None:
        """Get Payments with optional filters; return list or None."""
        raise NotImplementedError()

    # Review
    @abstractmethod
    def insert_review(self, session: Session, model: Review) -> Review:
        """Insert a Review and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_review(self, session: Session, model: Review) -> Review | None:
        """Update a Review and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_review(self, session: Session, id: str) -> Review | None:
        """Delete a Review by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_review_by_id(self, session: Session, id: str) -> Review | None:
        """Get a Review by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_reviews(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Review] | None:
        """Get Reviews with optional filters; return list or None."""
        raise NotImplementedError()

    # Address
    @abstractmethod
    def insert_address(self, session: Session, model: Address) -> Address:
        """Insert an Address and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_address(self, session: Session, model: Address) -> Address | None:
        """Update an Address and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_address(self, session: Session, id: str) -> Address | None:
        """Delete an Address by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_address_by_id(self, session: Session, id: str) -> Address | None:
        """Get an Address by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_addresses(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Address] | None:
        """Get Addresses with optional filters; return list or None."""
        raise NotImplementedError()

    @abstractmethod
    def insert_city(self, session: Session, model: City) -> City:
        """Insert a City and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_city(self, session: Session, model: City) -> City | None:
        """Update a City and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_city(self, session: Session, id: str) -> City | None:
        """Delete a City by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_city_by_id(self, session: Session, id: str) -> City | None:
        """Get a City by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_cities(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[City] | None:
        """Get Cities with optional filters; return list or None."""
        raise NotImplementedError(
        )

    # Brand
    @abstractmethod
    def insert_brand(self, session: Session, model: Brand) -> Brand:
        """Insert a Brand and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_brand(self, session: Session, model: Brand) -> Brand | None:
        """Update a Brand and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_brand(self, session: Session, id: str) -> Brand | None:
        """Delete a Brand by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_brand_by_id(self, session: Session, id: str) -> Brand | None:
        """Get a Brand by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_brands(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Brand] | None:
        """Get Brands with optional filters; return list or None."""
        raise NotImplementedError()

    # ProductVariant
    @abstractmethod
    def insert_product_variant(self, session: Session, model: ProductVariant) -> ProductVariant:
        """Insert a ProductVariant and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_product_variant(self, session: Session, model: ProductVariant) -> ProductVariant | None:
        """Update a ProductVariant and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_product_variant(self, session: Session, id: str) -> ProductVariant | None:
        """Delete a ProductVariant by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_product_variant_by_id(self, session: Session, id: str) -> ProductVariant | None:
        """Get a ProductVariant by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_product_variants(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[ProductVariant] | None:
        """Get ProductVariants with optional filters; return list or None."""
        raise NotImplementedError()

    # Inventory
    @abstractmethod
    def insert_inventory(self, session: Session, model: Inventory) -> Inventory:
        """Insert an Inventory and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_inventory(self, session: Session, model: Inventory) -> Inventory | None:
        """Update an Inventory and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_inventory(self, session: Session, id: str) -> Inventory | None:
        """Delete an Inventory by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_inventory_by_id(self, session: Session, id: str) -> Inventory | None:
        """Get an Inventory by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_inventories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Inventory] | None:
        """Get Inventories with optional filters; return list or None."""
        raise NotImplementedError()

    # VariantInventory
    @abstractmethod
    def insert_variant_inventory(self, session: Session, model: VariantInventory) -> VariantInventory:
        """Insert a VariantInventory and return created schema."""
        raise NotImplementedError()

    @abstractmethod
    def update_variant_inventory(self, session: Session, model: VariantInventory) -> VariantInventory | None:
        """Update a VariantInventory and return updated schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def delete_variant_inventory(self, session: Session, id: str) -> VariantInventory | None:
        """Delete a VariantInventory by id and return deleted schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_variant_inventory_by_id(self, session: Session, id: str) -> VariantInventory | None:
        """Get a VariantInventory by id; return schema or None."""
        raise NotImplementedError()

    @abstractmethod
    def get_variant_inventories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[VariantInventory] | None:
        """Get VariantInventories with optional filters; return list or None."""
        raise NotImplementedError()
