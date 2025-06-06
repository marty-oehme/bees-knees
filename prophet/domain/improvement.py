from dataclasses import dataclass
from uuid import uuid4

from prophet.domain.original import Original


@dataclass
class Improvement:  # GoodJoke: Queen
    original: Original
    title: str
    summary: str
    id: str = str(uuid4())
