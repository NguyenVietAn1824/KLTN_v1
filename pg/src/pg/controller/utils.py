from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Base
from ..schema import DatabaseSchema


def _insert(
    model_cls: type[Base],
    schema_cls: type[DatabaseSchema],
    session: Session,
    data: DatabaseSchema,
) -> DatabaseSchema:
    """Insert arbitrary data model.

    Args:
        session (Session): database session
        model_cls (Type[Base]): data model type
        schema_cls (Type[DatabaseSchema]): data schema type
        data (DatabaseSchema): data

    Returns:
        DatabaseSchema: inserted data
    """
    try:
        obj = model_cls(**data.model_dump(exclude_none=True))
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return schema_cls.model_validate(obj)
    except Exception as e:
        raise e


def _update(
    model_cls: type[Base],
    schema_cls: type[DatabaseSchema],
    session: Session,
    data: DatabaseSchema,
) -> DatabaseSchema | None:
    """Update arbitrary data model.

    Args:
        session (Session): database session
        model_cls (Type[Base]): data model type
        schema_cls (Type[DatabaseSchema]): data schema type
        data (DatabaseSchema): data

    Returns:
        DatabaseSchema | None: updated data or None if no data updated
    """
    try:
        obj = session.get(model_cls, data.id)
        if obj:
            for k, v in vars(data).items():
                if v is not None:
                    setattr(obj, k, v)

            session.add(obj)
            session.commit()
            session.refresh(obj)
            return schema_cls.model_validate(obj)
        else:
            return None
    except Exception as e:
        raise e


def _get_data(
    model_cls: type[Base],
    schema_cls: type[DatabaseSchema],
    session: Session,
    filter: dict[str, object] | None = None,
    order_by: Sequence | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[DatabaseSchema] | None:
    """Get arbitrary data with optional filtering, ordering and limit.

    Args:
        session (Session): database session
        model_cls (Type[Base]): data model type
        schema_cls (Type[DatabaseSchema]): data schema type
        filter (dict[str, object] | None, optional): filter. Defaults to None.
        limit (int | None, optional): limit. Defaults to None.
        offset (int | None, optional): record offset for pagination. Defaults to None.

    Returns:
        list[DatabaseSchema] | None: list of data returned or None if no data returned
    """
    try:
        statement = select(model_cls)
        if filter:
            statement = statement.filter_by(**filter)
        if order_by:
            statement = statement.order_by(*order_by)
        if limit is not None:
            statement = statement.limit(limit)
        if offset is not None:
            statement = statement.offset(offset)
        objs = session.scalars(statement=statement).all()
        if len(objs) == 0:
            return None
        return [schema_cls.model_validate(obj) for obj in objs]
    except Exception as e:
        raise e


def _get_data_by_id(
    model_cls: type[Base],
    schema_cls: type[DatabaseSchema],
    session: Session,
    id: str,
) -> DatabaseSchema | None:
    """Get a single object by id and return validated schema or None.

    Args:
        session (Session): database session
        model_cls (Type[Base]): data model type
        schema_cls (Type[DatabaseSchema]): data schema type
        id (int): id

    Returns:
        DatabaseSchema: Returned data
    """
    try:
        obj = session.get(model_cls, id)
        if not obj:
            return None
        return schema_cls.model_validate(obj)
    except Exception as e:
        raise e


def _delete(
    model_cls: type[Base],
    schema_cls: type[DatabaseSchema],
    session: Session,
    id: str,
) -> DatabaseSchema | None:
    """Delete an object by id and return the validated schema of deleted item.

    Args:
        session (Session): database session
        model_cls (Type[Base]): data model type
        schema_cls (Type[DatabaseSchema]): data schema type
        id (int): id

    Returns:
        DatabaseSchema: Deleted data or None if no delete
    """
    try:
        obj = session.get(model_cls, id)
        if obj:
            session.delete(obj)
            session.commit()
            return schema_cls.model_validate(obj)
        else:
            return None
    except Exception as e:
        raise e


def _get_data_by_ids(
    model_cls: type[Base],
    schema_cls: type[DatabaseSchema],
    session: Session,
    ids: list[str],
) -> list[DatabaseSchema] | None:
    """Fetch multiple objects by a list of ids.

    Args:
        session (Session): database session
        model_cls (Type[Base]): data model type
        schema_cls (Type[DatabaseSchema]): data schema type
        ids (list[str]): list of ids to fetch

    Returns:
        list[DatabaseSchema] | None: list of data returned or None if no data returned
    """
    if not ids:
        return None

    try:
        statement = select(model_cls).where(model_cls.id.in_(ids))
        objs = session.scalars(statement=statement).all()
        if len(objs) == 0:
            return None
        return [schema_cls.model_validate(obj) for obj in objs]
    except Exception as e:
        raise e
