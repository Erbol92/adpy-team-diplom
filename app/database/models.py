"""Модели для работы с базой данных"""

from typing import Annotated
from enum import StrEnum

from sqlalchemy import ForeignKey, String, text, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Sex(StrEnum):
    MALE = 'man'
    FEMALE = 'female'


# Анотация типов для подстановки в модели таблиц
int_pk = Annotated[int, mapped_column(primary_key=True)]
str_40 = Annotated[str, 40]


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    type_annotation_map = {
        str_40: String(40)
    }


class User(Base):
    """Пользователь бота"""
    __tablename__ = 'user'

    user_id: Mapped[int_pk]
    first_name: Mapped[str_40]
    last_name: Mapped[str_40]
    sex: Mapped[Sex]
    age: Mapped[int]
    city_code: Mapped[int]

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.age} лет)'

    __table_args__ = (
        CheckConstraint("age >= 18", name="check_success_age_adult")
    )


class Candidate(Base):
    """Потенциальные кандидаты для знакомства"""
    __tablename__ = 'candidate'

    candidate_id: Mapped[int_pk]
    vk_id: Mapped[int] = mapped_column(unique=True)

    def __str__(self):
        return f'Кандидат № {self.candidate_id}'


class UserCandidate(Base):
    """Кандидаты подходящие конкретному пользователю"""
    __tablename__ = 'favorite_candidate'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'), primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey('candidate.candidate_id'), primary_key=True)
    favorite: Mapped[bool] = mapped_column(server_default=text('FALSE'))
    in_blacklist: Mapped[bool] = mapped_column(server_default=text('FALSE'))

    user: Mapped['User'] = relationship(back_populates='favorite_candidate', cascade='all, delete')
    candidate: Mapped['Candidate'] = relationship(back_populates='favorite_candidate', cascade='all, delete')
