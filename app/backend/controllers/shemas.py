from pydantic import BaseModel, Field, EmailStr, field_validator

class SUser(BaseModel):
    email: EmailStr
    password: str = Field(default=..., min_length=8, max_length=32)

    @field_validator('password', mode='before')
    def validate_password(cls, p):
        digits_count = sum([p.count(digit) for digit in "0123456789"])
        special_symbols_count = sum([p.count(symbol) for symbol in "!@#$%^&*()_+=<,.>/?:;"])

        if digits_count < 3:
            raise ValueError(f"Your password is too simple, add at least {3 - digits_count} digits")        
        if special_symbols_count < 3:
            raise ValueError(f"Your password is too simple, add at least {3 - special_symbols_count} special symbols")
        
        return p