from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StateModel(Base):
    __tablename__ = "states"
    state_id = Column(Integer, primary_key=True, index=True)
    state_name = Column(String(255), nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.state_name = kwargs.get("state_name")
