from sqlalchemy import Column, Integer, String, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    chat_id = Column(Integer)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    bot_mode = Column(String)
