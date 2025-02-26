from pydantic import BaseModel


class Order(BaseModel):
    seller_id: int
    point_id: int
    client_id: int
    about: str
