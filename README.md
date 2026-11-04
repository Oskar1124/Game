# 2048 Spēle – API un serveris

## Projekta apraksts

Šis projekts ir 2048 spēles API, kas izveidots ar Python un FastAPI. API nodrošina spēlētāju rezultātu saglabāšanu SQLite datubāzē, labāko rezultātu iegūšanu un spēlētāju statistikas apskatīšanu.

## Izmantotās tehnoloģijas

- Python 3
- FastAPI
- Uvicorn
- SQLite
- Pydantic

## Projekta palaišana

### 1. Lejupielādēt projektu

Lejupielādē projektu no GitHub un atver to Visual Studio Code.

### 2. Izveidot virtuālo vidi

Projekta galvenajā mapē atver termināli un izpildi komandu:

python -m venv .venv

### 3. Aktivizēt virtuālo vidi

Windows PowerShell:

.venv\Scripts\Activate.ps1

### 4. Instalēt nepieciešamās bibliotēkas

pip install -r requirements.txt

### 5. Palaist serveri
uvicorn api.main:app --reload

Ja serveris ir palaists veiksmīgi, tas būs pieejams adresē:

http://127.0.0.1:8000

## API dokumentācija

Lai apskatītu un pārbaudītu API endpointus, atver pārlūkprogrammā:

http://127.0.0.1:8000/docs

## API endpointi

| Metode | Endpoints | Apraksts |
|---|---|---|
| POST | `/scores` | Saglabā spēlētāja rezultātu datubāzē. |
| GET | `/scores/top` | Iegūst 10 labākos rezultātus. |
| GET | `/players/{name}/stats` | Iegūst konkrēta spēlētāja statistiku. |

## Rezultātu datu piemērs

Nosūtot POST pieprasījumu uz `/scores`, jānorāda šādi dati:
{
  "name": "Oskars",
  "score": 2048,
  "game_time": 120,
  "max_tile": 2048
}

Atbildes kodi

| Kods | Nozīme |
|---|---|
| 200 | Pieprasījums izpildīts veiksmīgi. |
| 201 | Rezultāts veiksmīgi saglabāts. |
| 404 | Spēlētājs nav atrasts. |
| 422 | Ievadīti nederīgi dati. |
Datubāze

Projektā tiek izmantota SQLite datubāze. Spēlētāju rezultāti tiek saglabāti failā `scores.db`. Dati saglabājas arī pēc servera izslēgšanas un atkārtotas palaišanas.

## Autors

Oskars Rodionovs P25-1
