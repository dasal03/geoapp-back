from sqlalchemy import Column, Integer, String, Date, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=False)
    gender_id = Column(Integer, nullable=False, index=True)
    document_type_id = Column(Integer, nullable=False, index=True)
    document_number = Column(String(50), nullable=False)
    state_of_issue_id = Column(Integer, nullable=False, index=True)
    city_of_issue_id = Column(Integer, nullable=False, index=True)
    date_of_issue = Column(Date, nullable=False)
    role_id = Column(Integer, nullable=False, server_default="2", index=True)
    profile_img = Column(Text, nullable=True)
    active = Column(Integer, nullable=False, server_default="1", index=True)
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
        self.phone_number = kwargs.get("phone_number", None)
        self.date_of_birth = kwargs.get("date_of_birth")
        self.gender_id = kwargs.get("gender_id")
        self.document_type_id = kwargs.get("document_type_id")
        self.document_number = kwargs.get("document_number")
        self.state_of_issue_id = kwargs.get("state_of_issue_id")
        self.city_of_issue_id = kwargs.get("city_of_issue_id")
        self.date_of_issue = kwargs.get("date_of_issue")
        self.role_id = kwargs.get("role_id", 2)
        self.profile_img = kwargs.get("profile_img", None)
        self.active = kwargs.get("active", 1)
