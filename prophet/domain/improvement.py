from dataclasses import dataclass, field
from uuid import uuid4

from prophet.domain.original import Original


@dataclass
class Improvement:  # GoodJoke: Queen
    original: Original
    title: str
    summary: str
    id: str = field(default_factory=lambda: str(uuid4()))
