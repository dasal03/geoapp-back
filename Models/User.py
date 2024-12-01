from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=True, default=None)
    middle_name = Column(String(100), nullable=True, default=None)
    last_name = Column(String(100), nullable=True, default=None)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    country_id = Column(Integer, default=0)
    phone_number = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    document_type_id = Column(Integer, default=0)
    document_number = Column(String(50), nullable=False, default="")
    place_of_issue_id = Column(Integer, default=0)
    issue_date = Column(DateTime, nullable=False)
    issue_state_id = Column(Integer, default=0)
    expiry_date = Column(DateTime, nullable=False)
    issue_authority = Column(String(50), nullable=True)
    date_of_birth = Column(DateTime, nullable=False)
    gender_id = Column(Integer, default=0)
    role_id = Column(Integer, default=2)
    active = Column(Integer, default=1)

    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(
        DateTime, default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    def __init__(self, **kwargs):
        self.first_name = kwargs.get("first_name")
        self.middle_name = kwargs.get("middle_name")
        self.last_name = kwargs.get("last_name")
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.email = kwargs.get("email")
        self.country_id = kwargs.get("country_id", 0)
        self.phone_number = kwargs.get("phone_number")
        self.address = kwargs.get("address")
        self.document_type_id = kwargs.get("document_type_id", 0)
        self.document_number = kwargs.get("document_number", "")
        self.place_of_issue_id = kwargs.get("place_of_issue_id", 0)
        self.issue_date = kwargs.get("issue_date")
        self.issue_state_id = kwargs.get("issue_state_id", 0)
        self.expiry_date = kwargs.get("expiry_date")
        self.issue_authority = kwargs.get("issue_authority", None)
        self.date_of_birth = kwargs.get("date_of_birth")
        self.gender_id = kwargs.get("gender_id", 0)
        self.role_id = kwargs.get("role_id", 2)
        self.active = kwargs.get("active", 1)
