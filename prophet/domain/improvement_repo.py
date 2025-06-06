from typing import Protocol

from prophet.domain.improvement import Improvement


class ImprovementNotFoundError(Exception):
    pass


class IImprovementRepo(Protocol):
    def add(self, improvement: Improvement) -> None:
        raise NotImplementedError

    def add_all(self, improvements: list[Improvement]) -> None:
        raise NotImplementedError

    def get(self, id: str) -> Improvement:
        raise NotImplementedError

    def get_all(self) -> list[Improvement]:
        raise NotImplementedError
