from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Table, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.postgr.db import Base
import uuid

# Association table for many-to-many relationship between GroupChat and Agent
group_chat_agents = Table(
    'group_chat_agents',
    Base.metadata,
    Column('group_chat_id', Uuid(as_uuid=True), ForeignKey('group_chats.id')),
    # В `Agent.id` используется String, поэтому в связующей таблице тоже String.
    Column('agent_id', String(64), ForeignKey('agents.id'))
)


class GroupChat(Base):
    __tablename__ = 'group_chats'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_by_user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agents = relationship("Agent", secondary=group_chat_agents, back_populates="group_chats")
    user = relationship("User", back_populates="group_chats")

    def __repr__(self):
        return f"<GroupChat(id={self.id}, name='{self.name}')>"
