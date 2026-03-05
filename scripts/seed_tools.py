Let's open relevant files mentally. Assume app/database/db.py defines SessionLocal, engine, Base. tool_model has Tool table. Need to import get_registry maybe. core/registry provides Registry class with register decorator. tools sample_tool defines a tool. We need to load all tools via registry. So script will create DB tables, then iterate over registry.tools and insert into DB if not exists.

Also need to handle environment config: settings from app/settings.py which likely includes DATABASE_URL. Use SQLAlchemy.

Implement main guard.

Let's craft code.#!/usr/bin/env python3
import sys
from pathlib import Path

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.db import Base, engine, SessionLocal
from app.models.tool_model import Tool
from app.core.registry import registry


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_tools(session: Session) -> None:
    for tool_name, tool_cls in registry.tools.items():
        existing = session.query(Tool).filter_by(name=tool_name).first()
        if existing:
            continue
        try:
            new_tool = Tool(
                name=tool_name,
                module_path=f"{tool_cls.__module__}",
                class_name=tool_cls.__name__,
                description=getattr(tool_cls, "__doc__", "").strip(),
            )
            session.add(new_tool)
            session.commit()
        except IntegrityError:
            session.rollback()
        except SQLAlchemyError as exc:
            session.rollback()
            raise RuntimeError(f"Failed to seed tool {tool_name}") from exc


def main() -> None:
    create_tables()
    with SessionLocal() as session:
        seed_tools(session)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)