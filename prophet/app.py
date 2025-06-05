from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
