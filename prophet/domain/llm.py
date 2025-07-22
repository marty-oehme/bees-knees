from typing import Protocol

from prophet.domain.improvement import Improvement
from prophet.domain.original import Original


class LLMClient(Protocol):
    def rewrite(
        self, original: Original, previous_titles: list[str] | None = None
    ) -> Improvement:
        raise NotImplementedError

    def rewrite_title(
        self, original_content: str, suggestions: str | None = None
    ) -> str:
        raise NotImplementedError

    def rewrite_summary(
        self, original: Original, improved_title: str | None = None
    ) -> str:
        raise NotImplementedError

    def get_alternative_title_suggestions(self, original_content: str) -> str:
        raise NotImplementedError
