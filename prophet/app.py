import os
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq



BEE_FEED = "https://babylonbee.com/feed"
BEE_FEED_TEST = "test/resources/feed.atom"  # NOTE: Switch out when done testing


@dataclass
class Original:  # BadJoke: Sting
    id: str  # should probably be a sha256sum of the title/link?
    title: str
    summary: str
    link: str
    date: datetime


@dataclass
class Improvement:  # GoodJoke: Queen
    original: Original
    title: str
    summary: str
    id: str = str(uuid4())



def grab_latest_stings() -> list[str]:
    feed: feedparser.FeedParserDict = feedparser.parse(BEE_FEED_TEST)  # noqa: F841
    return feed.entries


def improve_with_groq(original: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY", "NO_API_KEY_FOUND"))

    suggestions = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Improve on the following satirical headline. The headline should be funny, can involve current political events and should have an edge to it. Print only the suggestions, with one suggestion on each line.\nOriginal: '{original}'",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print("Suggestions: ", suggestions.choices[0].message.content)
    winner = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"From the following satirical headline suggestions, pick the strongest one and print it. Do not print anything else. The chosen suggestion should be the most edgy, able to trend on social media and funniest. The suggestions:\n\n{suggestions}",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print("Winner: ", winner.choices[0].message.content)
    winner_str = winner.choices[0].message.content
    if not winner_str:
        raise ValueError
    return winner_str


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/improve")
def improve_headline(content: str):
    return improve_with_groq(content)



@app.get("/improvement")
def improve_headline(content: str):
    return improve_with_groq(content)


@app.get("/testanswer")
def read_root():
    response = {
        "data": [
            {
                "id": 1,
                "name": "Chocolate",
                "price": "4.50",
            },
            {
                "id": 2,
                "name": "Sorvete",
                "price": "2.42",
            },
            {
                "id": 3,
                "name": "Refrigerante",
                "price": "4.90",
            },
            {
                "id": 4,
                "name": "X-salada",
                "price": "7.99",
            },
        ]
    }
    return response


def start() -> None:
    from uvicorn import run

    print(grab_latest_stings())

    # run("prophet.app:app", reload=True)


if __name__ == "__main__":
    start()
