import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.db import Base


class ToolModel(Base):
    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    registry_id = Column(UUID(as_uuid=True), ForeignKey("registries.id"), nullable=False)
    registry = relationship("RegistryModel", back_populates="tools")

    def __repr__(self) -> str:
        return f"<Tool {self.name} v{self.version}>"

    @classmethod
    def create(cls, session, *, name: str, version: str, description: str | None = None, registry_id: uuid.UUID):
        tool = cls(name=name, version=version, description=description, registry_id=registry_id)
        session.add(tool)
        session.flush()
        return tool

    @classmethod
    def get_by_name(cls, session, name: str):
        return session.query(cls).filter_by(name=name).first()

    @classmethod
    def list_all(cls, session):
        return session.query(cls).all()

    @classmethod
    def delete(cls, session, tool_id: uuid.UUID):
        tool = session.get(cls, tool_id)
        if not tool:
            raise ValueError(f"Tool with id {tool_id} does not exist")
        session.delete(tool)

    def update(self, *, name: str | None = None, version: str | None = None, description: str | None = None):
        if name is not None:
            self.name = name
        if version is not None:
            self.version = version
        if description is not None:
            self.description = description

    def to_dict(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "registry_id": str(self.registry_id),
        }