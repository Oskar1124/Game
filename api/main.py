from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict, field_validator

from api.db import init_db, add_score, get_top_scores, get_player_stats

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class Score(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=20)
    score: int = Field(ge=0)
    game_time: int = Field(ge=0)
    max_tile: int = Field(ge=2)

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        if not value:
            raise ValueError("Vards nedrikst but tukss")
        return value


init_db()


@app.get("/")
def home():
    return {"message": "API strāda!"}


@app.post("/scores", status_code=201)
def create_score(data: Score):
    add_score(data.model_dump())
    return {"message": "Rezultāts saglabāts!"}


@app.get("/scores/top")
def top_scores():
    return get_top_scores()


@app.get("/players/{name}/stats")
def player_stats(name: str):
    stats = get_player_stats(name)

    if stats is None:
        raise HTTPException(
            status_code=404,
            detail="Spēlētājs nav atrasts"
        )

    return stats