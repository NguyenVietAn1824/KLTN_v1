from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import PolicyRule as PolicyRuleModel
from ..schema import PolicyRule
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, PolicyRuleModel, PolicyRule)
_update_method = partial(_update, PolicyRuleModel, PolicyRule)
_delete_method = partial(_delete, PolicyRuleModel, PolicyRule)
_get_method = partial(_get_data, PolicyRuleModel, PolicyRule)
_get_by_id_method = partial(_get_data_by_id, PolicyRuleModel, PolicyRule)


class PolicyRuleController(Repository):
    """Controller implementing CRUD operations for `PolicyRule` resources."""

    def insert_policy_rule(self, session: Session, model: PolicyRule) -> PolicyRule:
        """Insert a policy rule and return the created schema."""
        return cast(PolicyRule, _insert_method(session, model))

    def update_policy_rule(self, session: Session, model: PolicyRule) -> PolicyRule | None:
        """Update a policy rule; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(PolicyRule, result) if result else None

    def delete_policy_rule(self, session: Session, id: str) -> PolicyRule | None:
        """Delete a policy rule by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(PolicyRule, result) if result else None

    def get_policy_rules(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[PolicyRule] | None:
        """Fetch policy rules with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[PolicyRule], result) if result else None

    def get_policy_rule_by_id(self, session: Session, id: str) -> PolicyRule | None:
        """Retrieve a single policy rule by ID; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(PolicyRule, result) if result else None
