from dataclasses import field
from enum import unique
from pydantic.networks import MAX_EMAIL_LENGTH
from tortoise import fields
from tortoise import models
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from pydantic import constr


class User(models.Model):
    """User model"""
    email = fields.CharField(min_length=4, max_length=MAX_EMAIL_LENGTH, unique=True, pk=True)
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


