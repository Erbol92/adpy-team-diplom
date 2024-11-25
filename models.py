import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=60), nullable=False)
    sex = sq.Column(sq.String(length=5), nullable=False)
    age = sq.Integer(sq.Integer, nullable=False, default=0)

    def __str__(self):
        return f'{self.name} {self.sex} {self.age}'


class Favorite(Base):
    __tablename__ = 'favorite'

    id = sq.Column(sq.Integer, primary_key=True)
    # id может быть не только числом
    vk_id = sq.Columnt(sq.String(length=30), nullable=False)

    def __str__(self):
        return f'{self.vk_id}'


class UserFavorites(Base):
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey(
        'user.id'), nullable=False)
    favorite_id = sq.Column(sq.Integer, sq.ForeignKey(
        'favorite.id'), nullable=False)


def create_tables(engine):
    Base.metadata.create_all(engine)


def drop_tables(engine):
    Base.metadata.drop_all(engine)
