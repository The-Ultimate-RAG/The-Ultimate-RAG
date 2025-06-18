from pydantic import BaseModel, Field, EmailStr, field_validator

class SUser(BaseModel):
    email: EmailStr
    password: str = Field(default=..., min_length=8, max_length=32)

    @field_validator('password', mode='before')
    def validate_password(cls, p):
        # TODO: implement validation logic
        return p