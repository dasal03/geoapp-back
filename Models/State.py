from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StateModel(Base):
    __tablename__ = "states"

    state_id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, nullable=False, index=True)
    state_name = Column(String(100), nullable=False)
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.country_id = kwargs.get("country_id")
        self.state_name = kwargs.get("state_name")
