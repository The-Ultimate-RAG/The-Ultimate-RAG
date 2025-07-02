from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Self, Any

from dotenv import load_dotenv


@dataclass(slots=True, frozen=True, kw_only=True)
class EmailConfig:
    smtp_host: str
    smtp_port: int
    smtp_email: str
    smtp_password: str
    application_server_url: str

    @classmethod
    @lru_cache(maxsize=1)
    def from_env(cls) -> Self:
        load_dotenv()

        env_var_map: dict[str, str] = {
            "smtp_host": os.environ["SMTP_HOST"],
            "smtp_port": os.environ["SMTP_PORT"],
            "smtp_email": os.environ["SMTP_EMAIL"],
            "smtp_password": os.environ["SMTP_PASSWORD"],
            "application_server_url": os.environ["APPLICATION_SERVER_URL"],
        }

        config_values: dict[str, Any] = {}
        missing_variables: list[str] = []

        for attribute, env_var_name in env_var_map.items():
            value = os.getenv(env_var_name)
            if not value:
                missing_variables.append(env_var_name)
            config_values[attribute] = value

        if missing_variables:
            raise ValueError(f"Missing required environment variables:  "
                             f"{", ".join(missing_variables)}. "
                             f"Please ensure they are set in your .env file")

        try:
            config_values["smtp_port"] = int(config_values["smtp_port"])
        except ValueError:
            raise ValueError("SMTP port must be an integer")

        return cls(**config_values)
