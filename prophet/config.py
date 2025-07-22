import os

# Load environment variables from .env
from dataclasses import dataclass

from dotenv import load_dotenv

_ = load_dotenv()


@dataclass
class AppConfig:
    DEVMODE: bool
    PORT: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        PORT = os.getenv("BEES_PORT", os.getenv("PORT", "8000"))
        return cls(
            PORT=int(PORT),
            DEVMODE=bool(os.getenv("BEES_DEVMODE", False))
        )


@dataclass
class AiConfig:
    API_KEY: str

    @classmethod
    def from_env(cls) -> "AiConfig":
        API_KEY = os.getenv("GROQ_API_KEY", "")

        if not API_KEY:
            raise ValueError(f"{API_KEY} cannot be empty")

        return cls(**{"API_KEY": API_KEY})


@dataclass
class SupaConfig:
    URL: str
    KEY: str
    TABLE: str

    @classmethod
    def from_env(cls) -> "SupaConfig":
        URL = os.getenv("SUPABASE_URL", "")
        KEY = os.getenv("SUPABASE_KEY", "")
        TABLE = os.getenv("SUPABASE_TABLE", "improvements")

        values: dict[str, str] = {"URL": URL, "KEY": KEY, "TABLE": TABLE}

        for name, val in values.items():
            if not val:
                raise ValueError(f"SUPABASE_{name} cannot be empty")

        return cls(**values)
