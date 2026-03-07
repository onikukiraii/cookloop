from pydantic import BaseModel, EmailStr


class UserCreateParams(BaseModel):
    name: str
    email: EmailStr
