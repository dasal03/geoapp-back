from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class GenderModel(Base):
    __tablename__ = "genders"
    gender_id = Column(Integer, primary_key=True, index=True)
    gender_name = Column(String(255), nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.gender_name = kwargs.get("gender_name")
