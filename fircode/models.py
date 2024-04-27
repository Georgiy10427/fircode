from pydantic.networks import MAX_EMAIL_LENGTH
from tortoise import fields
from tortoise import models
from tortoise.contrib.pydantic import pydantic_model_creator
from typing_extensions import Annotated
from pydantic import BaseModel, StringConstraints, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from enum import Enum


class User(models.Model):
    """User model"""
    email = fields.CharField(min_length=4, max_length=MAX_EMAIL_LENGTH, unique=True, pk=True)
    phone = fields.CharField(min_lenght=4, max_length=15)
    first_name = fields.CharField(min_length=2, max_length=64)
    second_name = fields.CharField(min_length=2, max_length=64)
    is_admin = fields.BooleanField()
    hashed_password = fields.CharField(min_length=5, max_length=512)
    contribution = fields.IntField()

    class Meta:
        table = "user"

    class PydanticMeta:
        exclude = ["hashed_password"]


class SessionToken(models.Model):
    token = fields.CharField(min_length=128, max_length=512, pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "shelter.User"
    )

    class Meta:
        table = "session_token"


class Gender(str, Enum):
    male = 'male'
    female = 'female'


class Dog(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(min_lenght=1, max_length=32)
    photo = fields.TextField(default="dog_photo.png")
    gender = fields.CharEnumField(enum_type=Gender, max_length=10)
    age = fields.IntField()
    description = fields.TextField(max_lenght=1024)
    feed_amount = fields.IntField(default=0)
    host = fields.ForeignKeyField("shelter.User", null=True)


class UserRegistrationRequest(BaseModel):
    email: EmailStr
    phone_number: PhoneNumber
    first_name: Annotated[str, StringConstraints(min_length=2, max_length=64)]
    second_name: Annotated[str, StringConstraints(min_length=2, max_length=64)]
    password: Annotated[str, StringConstraints(min_length=1, max_length=512)]


class SignInRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=1, max_length=512)]


UserResponse = pydantic_model_creator(User)
DogIn = pydantic_model_creator(Dog, exclude_readonly=True, name="Dog")
DogOut = pydantic_model_creator(Dog)