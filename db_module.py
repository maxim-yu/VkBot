from authorization_data import DSN
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, BigInteger, Boolean, String

Base = declarative_base()


class VkUsers(Base):
    __tablename__ = 'vk_users'
    table_id = Column(Integer, primary_key=True)
    full_name = Column(String)
    vk_id = Column(BigInteger, unique=True)
    have_seen = Column(Boolean, nullable=False)
    blacklisted = Column(Boolean, nullable=False)
    favourite = Column(Boolean, nullable=False)


def create_table(engine_):
    Base.metadata.create_all(engine_)


def fill_data_in_db(users_list):
    for item in users_list:
        vk_id = item[0]
        full_name = item[1]
        session.add(VkUsers(full_name=full_name, vk_id=vk_id, have_seen=False, blacklisted=False, favourite=False))
    session.commit()


def get_all_ids_in_table():
    ids_list = list()
    request = session.query(VkUsers.vk_id)
    for line in request:
        ids_list.append(line[0])
    return ids_list


def clear_history_and_favorite():
    x_users = session.query(VkUsers).filter(VkUsers.blacklisted == False).all()
    for user in x_users:
        session.delete(user)
    session.commit()


def clear_unviewed_ids():
    x_users = session.query(VkUsers).filter(VkUsers.have_seen == False).all()
    for user in x_users:
        session.delete(user)
    session.commit()


def mark_as_viewed(some_id):
    session.query(VkUsers).filter(VkUsers.vk_id == some_id).update({VkUsers.have_seen: True}, synchronize_session=False)
    session.commit()


def mark_as_favourite(some_id):
    session.query(VkUsers).filter(VkUsers.vk_id == some_id).update({VkUsers.favourite: True}, synchronize_session=False)
    session.commit()


def mark_as_blacklisted(some_id):
    session.query(VkUsers).filter(VkUsers.vk_id == some_id).update({VkUsers.blacklisted: True}, synchronize_session=False)
    session.commit()


def get_unviewed_ids():
    ids_list = list()
    request = session.query(VkUsers.vk_id, VkUsers.full_name).filter(VkUsers.have_seen == False)
    for item in request:
        ids_list.append(item)
    return ids_list


def get_favorite_ids():
    ids_list = list()
    request = session.query(VkUsers.vk_id, VkUsers.full_name).filter(VkUsers.favourite == True)
    for item in request:
        ids_list.append(item)
    return ids_list


engine = sqlalchemy.create_engine(DSN)
create_table(engine)

Session = sessionmaker(bind=engine)
session = Session()
session.close()
