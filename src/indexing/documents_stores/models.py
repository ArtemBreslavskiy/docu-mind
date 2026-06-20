from sqlalchemy import Column, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    meta_json = Column(String, default="{}")
