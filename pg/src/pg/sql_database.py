from __future__ import annotations

from contextlib import contextmanager
from functools import cached_property

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from .controller import AddressController
from .controller import BrandController
from .controller import CartController
from .controller import CartItemController
from .controller import CategoryController
from .controller import CityController
from .controller import ConversationController
from .controller import GroupController
from .controller import HumanActivityController
from .controller import InventoryController
from .controller import MessageController
from .controller import OrderController
from .controller import OrderItemController
from .controller import PaymentController
from .controller import PolicyRuleController
from .controller import ProductCategoryController
from .controller import ProductController
from .controller import ProductVariantController
from .controller import RecommendItemsController
from .controller import ReviewController
from .controller import UserAttributeController
from .controller import UserAuthenticationController
from .controller import UserController
from .controller import VariantInventoryController
from .models import Base


class SQLDatabase(
    UserController,
    UserAttributeController,
    MessageController,
    ConversationController,
    RecommendItemsController,
    HumanActivityController,
    ProductController,
    ProductCategoryController,
    CategoryController,
    GroupController,
    CityController,
    UserAuthenticationController,
    PolicyRuleController,
    OrderController,
    OrderItemController,
    CartController,
    CartItemController,
    PaymentController,
    ReviewController,
    AddressController,
    BrandController,
    InventoryController,
    ProductVariantController,
    VariantInventoryController,
):
    @cached_property
    def sessionmaker(self) -> sessionmaker:
        """Create and return a SQLAlchemy `sessionmaker` bound to the DB engine.

        This method lazily constructs the engine and creates all ORM tables.
        """
        engine = create_engine(
            f'postgresql+psycopg2://{self.username}:{self.password}@{self.host}/{self.db}',
        )
        Base.metadata.create_all(engine)
        return sessionmaker(autoflush=False, bind=engine)

    def __init__(self, username, password, host, db):
        """Initialize the database connector with connection parameters.

        Args:
            username: DB username.
            password: DB password.
            host: Hostname or address of the DB server.
            db: Database name.
        """
        self.username = username
        self.password = password
        self.host = host
        self.db = db

    @contextmanager
    def get_session(self):
        """Context manager that yields a SQLAlchemy `Session`.

        Ensures the session is closed after use.
        """
        session = None
        try:
            session: Session = self.sessionmaker()
            yield session
        finally:
            if session:
                session.close()  # type: ignore

    async def check_health(self) -> bool:
        """Asynchronously check database connectivity by acquiring a session.

        Returns:
            True when a session can be created (DB reachable), otherwise False.
        """
        try:
            with self.get_session() as _:
                return True
            return False
        except Exception as e:
            raise e
