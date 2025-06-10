from typing import override

from groq import Groq

from prophet.config import AiConfig
from prophet.domain.improvement import Improvement
from prophet.domain.llm import LLMClient
from prophet.domain.original import Original

AVOID_SHOCKING_TURN_OF_EVENTS: bool = True


class GroqClient(LLMClient):
    config_ai: AiConfig
    client: Groq

    def __init__(
        self, config_ai: AiConfig | None = None, client: Groq | None = None
    ) -> None:
        self.config_ai = config_ai if config_ai else AiConfig.from_env()
        self.client = client if client else Groq(api_key=self.config_ai.API_KEY)

    @override
    def rewrite(self, original: Original) -> Improvement:
        suggestions = self.get_alternative_title_suggestions(original.title)
        new_title = self.rewrite_title(original.title, suggestions)
        new_summary = self.rewrite_summary(original, new_title)

        return Improvement(original=original, title=new_title, summary=new_summary)

    @override
    def get_alternative_title_suggestions(
        self, original_content: str, custom_prompt: str | None = None
    ) -> str:
        prompt = (
            custom_prompt
            if custom_prompt
            else """You are a comedy writer at a satirical newspaper. Improve
            on the following satirical headline. Your new headline is funny,
            can involve current political events and has an edge to it. Print
            only the suggestions, with one suggestion on each line."""
        )
        suggestions = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": original_content,
                },
            ],
            model="llama-3.3-70b-versatile",
        )
        suggestions_str = suggestions.choices[0].message.content
        if not suggestions_str:
            raise ValueError
        return suggestions_str

    @override
    def rewrite_title(
        self,
        original_content: str,
        suggestions: str | None = None,
        custom_prompt: str | None = None,
    ) -> str:
        prompt = (
            custom_prompt
            if custom_prompt
            else """
        You are an editor at a satirical newspaper. Improve on the following
        satirical headline. For a given headline, you diligently evaluate: (1)
        Whether the headline is funny; (2) Whether the headline follows a clear
        satirical goal; (3) Whether the headline has sufficient substance and
        bite. Based on the outcomes of your review, you pick your favorite
        headline from the given suggestions and you make targeted revisions to
        it. Keep the length roughly to that of the original suggestions. Your
        output consists solely of the revised headline.
        """
        )
        if not suggestions:
            suggestions = self.get_alternative_title_suggestions(original_content)
        winner = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": suggestions,
                },
            ],
            model="llama-3.3-70b-versatile",
        )
        print("Winner: ", winner.choices[0].message.content)
        winner_str = winner.choices[0].message.content
        if not winner_str:
            raise ValueError
        return winner_str.strip(" \"'")

    @override
    def rewrite_summary(
        self,
        original: Original,
        improved_title: str | None = None,
        custom_prompt: str | None = None,
    ) -> str:
        prompt = (
            custom_prompt
            if custom_prompt
            else f""" Below there is an original title and an original summary. Then follows an improved title. Write an improved summary based on the original summary which fits to the improved title. {"Do not use the phrase: 'in a surprising turn of events' or 'in a shocking turn of events.'" if AVOID_SHOCKING_TURN_OF_EVENTS else ""} Only output the improved summary.\n\nTitle:{original.title}\nSummary:{original.summary}\n---\nTitle:{improved_title}\nSummary:"""
        )
        if not improved_title:
            improved_title = self.rewrite_title(original.title)

        summary = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        summary_str = summary.choices[0].message.content
        if not summary_str:
            raise ValueError
        print("Improved summary", summary_str)
        return summary_str.strip(" \"'")
