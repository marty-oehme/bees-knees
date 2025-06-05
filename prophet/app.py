import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
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


@app.get("/test")
@app.get("/improve")
def improve_headline(content: str):
    return improve_with_groq(content)

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

    run("prophet.app:app", reload=True)


if __name__ == "__main__":
    start()
