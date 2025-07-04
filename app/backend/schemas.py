from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator
import re


class ThemeOptions(str, Enum):
    LIGHT = "light"
    DARK = "dark"


class LanguageOptions(str, Enum):
    AR = "ar"
    EN = "en"
    RU = "ru"

