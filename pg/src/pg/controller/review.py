from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Review as ReviewModel
from ..schema import Review
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, ReviewModel, Review)
_update_method = partial(_update, ReviewModel, Review)
_delete_method = partial(_delete, ReviewModel, Review)
_get_method = partial(_get_data, ReviewModel, Review)
_get_by_id_method = partial(_get_data_by_id, ReviewModel, Review)


class ReviewController(Repository):
    """Controller implementing CRUD operations for `Review` resources."""

    def insert_review(self, session: Session, model: Review) -> Review:
        """Insert a review entry and return created schema."""
        return cast(Review, _insert_method(session, model))

    def update_review(self, session: Session, model: Review) -> Review | None:
        """Update a review; return updated schema or None."""
        result = _update_method(session, model)
        return cast(Review, result) if result else None

    def delete_review(self, session: Session, id: str) -> Review | None:
        """Delete a review by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Review, result) if result else None

    def get_reviews(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        Review_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Review] | None:
        """Fetch reviews with optional filters/limit/offset; returns list or None."""
        result = _get_method(session, filter, Review_by, limit, offset)
        return cast(list[Review], result) if result else None

    def get_review_by_id(self, session: Session, id: str) -> Review | None:
        """Fetch a single review by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Review, result) if result else None
