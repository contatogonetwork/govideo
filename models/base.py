"""
GONETWORK AI - Definições de base para modelos de dados
"""

import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, Enum
from sqlalchemy.orm import relationship

from . import Base

# Tabelas associativas
event_tags = Table(
    "event_tags",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("events.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)

asset_tags = Table(
    "asset_tags",
    Base.metadata,
    Column("asset_id", Integer, ForeignKey("assets.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)

# Definições de tipos/enums compartilhados
delivery_status_types = ["pending", "in_progress", "review", "approved", "published", "rejected"]
activity_status_types = ["pending", "in_progress", "completed", "delayed", "cancelled"]
activation_status_types = ["pending", "in_progress", "filmed", "failed", "approved"]
