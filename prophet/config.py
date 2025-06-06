import os

# Load environment variables from .env
from dataclasses import dataclass

from dotenv import load_dotenv

_ = load_dotenv()


@dataclass
class AiConfig:
    API_KEY: str

    @classmethod
    def from_env(cls) -> "AiConfig":
        API_KEY = os.getenv("GROQ_API_KEY", "")

        if not API_KEY:
            raise ValueError(f"{API_KEY} cannot be empty")

        return cls(**{"API_KEY": API_KEY})
