
from typing import Protocol

from prophet.domain.improvement import Improvement


class IImprovementRepo(Protocol):
    def add(self, improvement: Improvement) -> None:
        raise NotImplementedError

    def get(self, id: str) -> Improvement:
        raise NotImplementedError

    def get_all(self) -> list[Improvement]:
        raise NotImplementedError
