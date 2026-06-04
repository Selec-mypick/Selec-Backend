from sqlalchemy import Column, Integer, String

from app.base.base_time_entity import BaseTimeEntity


class User(BaseTimeEntity):
    __tablename__ = 'users'

    user_seq = Column(Integer, primary_key=True, index=True)
    account_type = Column(String(20), unique=False, nullable=False)
    business_name = Column(String(100), unique=False, nullable=False)
    business_number = Column(String(50), unique=True, nullable=False)
    user_name = Column(String(50), unique=False, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=False, nullable=False)
    user_id = Column(String(50), unique=True, nullable=False, index=False)
    hashed_password = Column(String(512), unique=False, nullable=False)
