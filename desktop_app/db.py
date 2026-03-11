from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def session_scope():
    from app.db.session import create_session_factory

    session = create_session_factory()()
    try:
        yield session
    finally:
        session.close()
