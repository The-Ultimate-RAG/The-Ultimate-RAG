from enum import Enum


class ThemeOptions(str, Enum):
    '''
    Used as custom-defined fields in `users` table
    Means UI theme
    '''
    LIGHT = "light"
    DARK = "dark"


class LanguageOptions(str, Enum):
    '''
    Used as custom-defined fields in `users` table
    Means preferred response language
    '''
    AR = "ar"
    EN = "en"
    RU = "ru"
