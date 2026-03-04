from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from pg import SQLDatabase
from pg.schema import ActionType
from pg.schema import Category as CategoryModel
from pg.schema import City as CityModel
from pg.schema import Conversation as ConversationModel
from pg.schema import GenderType
from pg.schema import Group as GroupModel
from pg.schema import HumanActivityLog as HumanActivityLogModel
from pg.schema import Message as MessageModel
from pg.schema import Product as ProductModel
from pg.schema import ProductCategory as ProductCategoryModel
from pg.schema import RecommendItems as RecommendItemsModel
from pg.schema import RoleType
from pg.schema import User as UserModel
from pg.schema import UserAttribute as UserAttributeModel


load_dotenv()


username = os.getenv('POSTGRES__USERNAME')
password = os.getenv('POSTGRES__PASSWORD')
database = os.getenv('POSTGRES__DB')
host = os.getenv('POSTGRES__HOST')


class TestPostgres:
    """Create test data for all models.

    This class sets up engine and session, ensures tables exist and inserts
    one sample row per model in a foreign-key-safe order.
    """

    def __init__(self) -> None:
        self.user = username
        self.password = password
        self.host = host
        self.database = database

        self.db = SQLDatabase(self.user, self.password, self.host, self.database)

    def test_all_models(self) -> None:
        """Insert and perform basic CRUD for every schema in an FK-safe order.

        Steps:
        - insert all sample rows in an order that satisfies foreign keys
        - fetch each by id and via list endpoints
        - perform a simple update for a subset of models
        - delete rows in reverse order and ensure they're removed
        """
        # generate ids
        group_id = str(uuid4())
        category_id = str(uuid4())
        city_id = str(uuid4())
        user_id = str(uuid4())
        conversation_id = str(uuid4())
        message_id = str(uuid4())
        product_id = str(uuid4())
        product_category_id = str(uuid4())
        recommend_items_id = str(uuid4())
        human_activity_log_id = str(uuid4())
        user_attribute_id = str(uuid4())

        # build models
        group = GroupModel(id=group_id, name='Apparel')
        category = CategoryModel(id=category_id, group_id=group_id, name='Tops', description='Shirts and tees')
        city = CityModel(id=city_id, name='Hanoi')
        user = UserModel(
            id=user_id,
            city_id=city_id,
            name='Test User',
            email='test@example.com',
            dob=datetime(1990, 1, 10).date(),
            phone='+84000000000',
            gender=GenderType.MALE,
            address='123 Example St',
            ward='Ward 1',
            avatar_url='',
            last_active=datetime.utcnow(),
            role=RoleType.USER,
        )
        conversation = ConversationModel(id=conversation_id, user_id=user_id, title='Test convo')
        message = MessageModel(id=message_id, conversation_id=conversation_id, question='What?', answer='Nothing')
        product = ProductModel(
            id=product_id,
            name='Sample Product',
            price=123456.0,
            stock=10,
            image_url='',
            description='Sample',
            size=['M'],
            weight='100g',
            material='Plastic',
            brand='Acme',
        )
        product_category = ProductCategoryModel(id=product_category_id, product_id=product_id, category_id=category_id)
        recommend = RecommendItemsModel(id=recommend_items_id, message_id=message_id, product_id=product_id)
        halog = HumanActivityLogModel(id=human_activity_log_id, message_id=message_id, product_id=product_id, user_id=user_id, action_type=ActionType.CLICK, quantity=1)
        uattr = UserAttributeModel(id=user_attribute_id, user_id=user_id, summarize_attribute='{}')

        with self.db.get_session() as session:
            try:
                # insert in safe order
                self.db.insert_group(session=session, model=group)
                self.db.insert_category(session=session, model=category)
                self.db.insert_city(session=session, model=city)
                self.db.insert_user(session=session, model=user)
                self.db.insert_conversation(session=session, model=conversation)
                self.db.insert_message(session=session, model=message)
                self.db.insert_product(session=session, model=product)
                self.db.insert_product_category(session=session, model=product_category)
                self.db.insert_recommend_items(session=session, model=recommend)
                self.db.insert_human_activity_log(session=session, model=halog)
                self.db.insert_user_attribute(session=session, model=uattr)

                # --- Basic reads ---
                assert self.db.get_group_by_id(session=session, id=group_id) is not None
                assert self.db.get_category_by_id(session=session, id=category_id) is not None
                assert self.db.get_city_by_id(session=session, id=city_id) is not None
                assert self.db.get_user_by_id(session=session, id=user_id) is not None
                assert self.db.get_conversation_by_id(session=session, id=conversation_id) is not None
                assert self.db.get_message_by_id(session=session, id=message_id) is not None
                assert self.db.get_product_by_id(session=session, id=product_id) is not None
                assert self.db.get_product_category_by_id(session=session, id=product_category_id) is not None
                assert self.db.get_recommend_items_by_id(session=session, id=recommend_items_id) is not None
                assert self.db.get_human_activity_log_by_id(session=session, id=human_activity_log_id) is not None
                assert self.db.get_user_attribute_by_id(session=session, id=user_attribute_id) is not None

                # --- Updates ---
                # update group
                group.name = group.name + ' Updated'
                updated_group = self.db.update_group(session=session, model=group)
                assert updated_group is not None and updated_group.name.endswith('Updated')

                # update product price
                product.price = product.price + 1.0
                updated_product = self.db.update_product(session=session, model=product)
                assert updated_product is not None and float(updated_product.price) == float(product.price)

                # update message answer
                message.answer = 'Updated answer'
                updated_message = self.db.update_message(session=session, model=message)
                assert updated_message is not None and updated_message.answer == 'Updated answer'

                # update human activity log quantity
                halog.quantity = 2
                updated_halog = self.db.update_human_activity_log(session=session, model=halog)
                assert updated_halog is not None and updated_halog.quantity == 2

                # update user attribute
                uattr.summarize_attribute = '{"updated": true}'
                updated_uattr = self.db.update_user_attribute(session=session, model=uattr)
                assert updated_uattr is not None

                # --- Deletes (reverse safe order) ---
                self.db.delete_user_attribute(session=session, id=user_attribute_id)
                assert self.db.get_user_attribute_by_id(session=session, id=user_attribute_id) is None

                self.db.delete_human_activity_log(session=session, id=human_activity_log_id)
                assert self.db.get_human_activity_log_by_id(session=session, id=human_activity_log_id) is None

                self.db.delete_recommend_items(session=session, id=recommend_items_id)
                assert self.db.get_recommend_items_by_id(session=session, id=recommend_items_id) is None

                self.db.delete_product_category(session=session, id=product_category_id)
                assert self.db.get_product_category_by_id(session=session, id=product_category_id) is None

                self.db.delete_product(session=session, id=product_id)
                assert self.db.get_product_by_id(session=session, id=product_id) is None

                self.db.delete_message(session=session, id=message_id)
                assert self.db.get_message_by_id(session=session, id=message_id) is None

                self.db.delete_conversation(session=session, id=conversation_id)
                assert self.db.get_conversation_by_id(session=session, id=conversation_id) is None

                self.db.delete_user(session=session, id=user_id)
                assert self.db.get_user_by_id(session=session, id=user_id) is None

                self.db.delete_city(session=session, id=city_id)
                assert self.db.get_city_by_id(session=session, id=city_id) is None

                self.db.delete_category(session=session, id=category_id)
                assert self.db.get_category_by_id(session=session, id=category_id) is None

                self.db.delete_group(session=session, id=group_id)
                assert self.db.get_group_by_id(session=session, id=group_id) is None

            except Exception:
                raise


if __name__ == '__main__':
    test_postgres = TestPostgres()
    # run all model insertions
    test_postgres.test_all_models()
