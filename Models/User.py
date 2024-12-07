from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender_id = Column(Integer)
    document_type_id = Column(Integer)
    document_number = Column(String(50), nullable=False)
    state_of_issue_id = Column(Integer)
    city_of_issue_id = Column(Integer)
    date_of_issue = Column(DateTime, nullable=False)
    role_id = Column(Integer, server_default=str(2))
    profile_img = Column(Text, nullable=False)
    active = Column(Integer, server_default=str(1))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(
        DateTime, default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    def __init__(self, **kwargs):
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.email = kwargs.get("email")
        self.phone_number = kwargs.get("phone_number")
        self.date_of_birth = kwargs.get("date_of_birth")
        self.gender_id = kwargs.get("gender_id", 0)
        self.document_type_id = kwargs.get("document_type_id", 0)
        self.document_number = kwargs.get("document_number", "")
        self.state_of_issue_id = kwargs.get("state_of_issue_id", 0)
        self.city_of_issue_id = kwargs.get("city_of_issue_id", 0)
        self.date_of_issue = kwargs.get("date_of_issue")
        self.role_id = kwargs.get("role_id", 2)
        self.profile_img = kwargs.get("profile_img", "")
