# FastAPI serveris: saņem rezultātus no spēles un atdod tos mājaslapai.
# Palaišana (no projekta saknes mapes):  uvicorn api.main:app --reload
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict, field_validator

from api.db import init_db, add_score, get_top_scores, get_player_stats

app = FastAPI()

# CORS: ļauj mājaslapai (saite.html) sūtīt pieprasījumus uz šo serveri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class Score(BaseModel):
    """Rezultāta datu forma, ko sūta spēle (POST /scores). Pydantic pārbauda laukus."""
    model_config = ConfigDict(str_strip_whitespace=True)  # automātiski noņem atstarpes vārda malās

    name: str = Field(min_length=1, max_length=20)  # vārds: 1-20 simboli
    score: int = Field(ge=0)                        # punkti: nav negatīvi
    game_time: int = Field(ge=0)                    # laiks sekundēs
    max_tile: int = Field(ge=2)                     # lielākais kvadrāts: vismaz 2

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        # Papildu pārbaude: vārds nedrīkst būt tukšs
        if not value:
            raise ValueError("Vards nedrikst but tukss")
        return value


# Izveidojam tabulu datubāzē, kad serveris startē
init_db()


@app.get("/")
def home():
    """Pārbaude, vai serveris darbojas."""
    return {"message": "API strāda!"}


@app.post("/scores", status_code=201)
def create_score(data: Score):
    """Saglabā jaunu rezultātu (to izsauc spēle pēc partijas beigām)."""
    add_score(data.model_dump())
    return {"message": "Rezultāts saglabāts!"}


@app.get("/scores/top")
def top_scores():
    """Atdod 10 labākos rezultātus (līderu tabulai mājaslapā)."""
    return get_top_scores()


@app.get("/players/{name}/stats")
def player_stats(name: str):
    """Atdod viena spēlētāja statistiku; ja tāda nav — kļūda 404."""
    stats = get_player_stats(name)

    if stats is None:
        raise HTTPException(
            status_code=404,
            detail="Spēlētājs nav atrasts"
        )

    return stats
