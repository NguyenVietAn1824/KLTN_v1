from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Category as CategoryModel
from ..schema import Category
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update


_insert_method = partial(_insert, CategoryModel, Category)
_update_method = partial(_update, CategoryModel, Category)
_delete_method = partial(_delete, CategoryModel, Category)
_get_method = partial(_get_data, CategoryModel, Category)
_get_by_id_method = partial(_get_data_by_id, CategoryModel, Category)


class CategoryController(Repository):
    """Controller implementing CRUD operations for `Category` resources."""

    def insert_category(self, session: Session, model: Category) -> Category:
        """Insert a category and return the created schema."""
        return cast(Category, _insert_method(session, model))

    def update_category(self, session: Session, model: Category) -> Category | None:
        """Update a category; return updated schema or None."""
        result = _update_method(session, model)
        return cast(Category, result) if result else None

    def delete_category(self, session: Session, id: str) -> Category | None:
        """Delete a category by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Category, result) if result else None

    def get_categories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Category] | None:
        """Fetch categories with optional filters; return list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Category], result) if result else None

    def get_category_by_id(self, session: Session, id: str) -> Category | None:
        """Fetch a category by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Category, result) if result else None
