"""Модели для работы с базой данных"""

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.engine import Base, int_pk


class User(Base):
    """Пользователь бота"""
    __tablename__ = 'user'

    user_id: Mapped[int_pk]
    vk_id: Mapped[int] = mapped_column(unique=True)
    already_searched: Mapped[bool] = mapped_column(server_default=text('FALSE'))

    candidate: Mapped['Candidate'] = relationship(back_populates='user', cascade='all, delete')
    favorite_candidate: Mapped['FavoriteCandidate'] = relationship(back_populates='user', cascade='all, delete')
    blacklist: Mapped['Blacklist'] = relationship(back_populates='user', cascade='all, delete')

    def __str__(self):
        return f'{self.vk_id}'


class Candidate(Base):
    """Потенциальные кандидаты для знакомства"""
    __tablename__ = 'candidate'

    candidate_id: Mapped[int_pk]
    vk_id: Mapped[int] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'))
    skip: Mapped[bool] = mapped_column(server_default=text('FALSE'))

    user: Mapped['User'] = relationship(back_populates='candidate', cascade='all, delete')
    favorite_candidate: Mapped['FavoriteCandidate'] = relationship(back_populates='candidate', cascade='all, delete')
    blacklist: Mapped['Blacklist'] = relationship(back_populates='candidate', cascade='all, delete')

    def __str__(self):
        return f'Кандидат № {self.candidate_id}'


class FavoriteCandidate(Base):
    """Избранные кандидаты"""
    __tablename__ = 'favorite_candidate'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'), primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey('candidate.candidate_id'), primary_key=True)

    user: Mapped['User'] = relationship(back_populates='favorite_candidate', cascade='all, delete')
    candidate: Mapped['Candidate'] = relationship(back_populates='favorite_candidate', cascade='all, delete')


class Blacklist(Base):
    """Кандидаты которые больше не будут показываться пользователю"""
    __tablename__ = 'blacklist'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'), primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey('candidate.candidate_id'), primary_key=True)

    user: Mapped['User'] = relationship(back_populates='blacklist', cascade='all, delete')
    candidate: Mapped['Candidate'] = relationship(back_populates='blacklist', cascade='all, delete')
