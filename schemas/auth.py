from pydantic import BaseModel


class CreateUser(BaseModel):
    email: str
    password: str


class CreateClient(CreateUser):
    first_name: str


class CreateSeller(CreateUser):
    name: str
    about: str


class CreatePoint(CreateUser):
    name: str


class Login(BaseModel):
    email: str
    password: str
