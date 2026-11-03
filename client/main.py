# Spēles klients (pygame): izvēlne, spēles zīmēšana, ievade un rezultātu sūtīšana uz API.
#IMPORTI UN IESTATĪJUMI
import pygame
import sys
import os
import time
import json
import threading
import urllib.request
import urllib.error

# Pievienojam projekta sakni meklēšanas ceļiem, lai varētu importēt mapi game
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.logic import Game

# Jūsu FastAPI servera adrese (palaiž ar: uvicorn api.main:app --reload)
API_URL = "http://127.0.0.1:8000"

NAME_MAX = 20                 # maksimālais vārda garums (tāds pats kā API)
ADMIN_PASSWORD = "123456"     # admina parole (tiek ievadīta izvēlnē laukā "Admins")
ADMIN_PASS_MAX = 20           # maksimālais paroles garums, ko var ievadīt
ADMIN_POINTS_MAX = 9          # maksimālais ciparu skaits punktiem, ko admins pievieno

pygame.init()

# Spēles logs un fonti
screen = pygame.display.set_mode((520, 700))
pygame.display.set_caption("2048 Kubi")

font = pygame.font.SysFont("arial", 30, bold=True)   # lielais fonts (virsraksti, cipari)
small = pygame.font.SysFont("arial", 19)             # mazais fonts (parastais teksts)

clock = pygame.time.Clock()   # ierobežo spēli līdz 60 kadriem sekundē

# Krāsas (RGB)
BG = (250, 248, 239)
BLACK = (40, 40, 40)
WHITE = (255, 255, 255)
GREEN = (60, 140, 70)
RED = (180, 70, 40)
GRAY = (140, 140, 140)
BLUE = (60, 120, 200)

# Kvadrātu krāsas pēc to vērtības
colors = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (230, 190, 65),
    2048: (237, 194, 46)
}

# ---------------------------------------------------------------- 2. SPĒLES STĀVOKLIS
game = Game()          # pašreizējā spēle (loģika atrodas game/logic.py)

state = "menu"         # pašreizējais stāvoklis (skat. sarakstu faila sākumā)
start_time = 0         # brīdis, kad sākās partija
pause_time = 0         # brīdis, kad sākās pauze (vai admina ievade)
paused = 0             # cik sekundes kopā pavadītas pauzē
saved = False          # vai rezultāts šai partijai jau saglabāts

player_name = ""       # spēlētāja vārds (ievada izvēlnē)
send_status = ""       # rezultāta sūtīšanas statuss: "", "sending", "ok", "error"

# --- Izvēlnes ievades lauki ---
admin_pass = ""        # admina parole, ko ievadīja laukā "Admins"
active_field = "name"  # kurš lauks šobrīd aktīvs: "name" vai "admin"
menu_error = ""        # kļūdas ziņojums izvēlnē (piem., nepareiza parole)

# --- Admina režīms ---
admin_mode = False     # True, ja ievadīta pareiza admina parole
admin_points = ""      # cipari, ko admins ievada, lai pievienotu punktus


# ---------------------------------------------------------------- 3. PALĪGFUNKCIJAS
def text(msg, x, y, size=small, color=BLACK):
    """Uzzīmē tekstu ar kreiso augšējo stūri punktā (x, y)."""
    img = size.render(str(msg), True, color)
    screen.blit(img, (x, y))


def text_center(msg, y, size=small, color=BLACK):
    """Uzzīmē tekstu, centrētu logā horizontāli (loga platums 520, centrs 260)."""
    img = size.render(str(msg), True, color)
    screen.blit(img, img.get_rect(center=(260, y)))


def draw_input_box(x, y, w, h, value, active):
    """Uzzīmē ievades lauku ar tekstu; aktīvam laukam ir zila rāmja līnija un mirgojošs kursors."""
    pygame.draw.rect(screen, WHITE, (x, y, w, h))
    pygame.draw.rect(screen, BLUE if active else BLACK, (x, y, w, h),
                     3 if active else 2)

    # Kursors mirgo divas reizes sekundē
    cursor = "|" if active and int(time.time() * 2) % 2 == 0 else ""
    text(value + cursor, x + 12, y + 10)


def save_local(record):
    """Rezerves saglabāšana failā data/leaderboard.json (ja API nav pieejams)."""
    file = "data/leaderboard.json"

    # Ielādējam esošos ierakstus; ja faila nav vai tas bojāts — sākam ar tukšu sarakstu
    try:
        with open(file, "r") as f:
            records = json.load(f)
    except Exception:
        records = []

    records.append(record)
    records.sort(key=lambda x: x["score"], reverse=True)   # labākie augšā

    os.makedirs("data", exist_ok=True)

    # Saglabājam tikai 10 labākos
    with open(file, "w") as f:
        json.dump(records[:10], f, indent=4)


def send_to_api(payload):
    """Nosūta rezultātu uz API (POST /scores) atsevišķā pavedienā, lai spēle nepakartos."""
    global send_status

    try:
        req = urllib.request.Request(
            API_URL + "/scores",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            send_status = "ok" if resp.status == 201 else "error"
    except (urllib.error.URLError, OSError, ValueError):
        # Serveris nav pieejams vai atbildēja ar kļūdu
        send_status = "error"


def save_score():
    """Saglabā partijas rezultātu failā un nosūta uz API."""
    global send_status

    # Dati, ko sagaida API (skat. api/main.py, klase Score)
    payload = {
        "name": player_name,
        "score": game.score,
        "game_time": int(time.time() - start_time - paused),
        "max_tile": max(2, game.best_tile)   # API pieņem tikai vērtības no 2
    }

    # Rezerves kopija failā
    save_local({
        "name": payload["name"],
        "score": payload["score"],
        "time": payload["game_time"],
        "best_tile": payload["max_tile"]
    })

    # Sūtām uz API fonā; statusu atjauno funkcija send_to_api
    send_status = "sending"
    threading.Thread(target=send_to_api, args=(payload,), daemon=True).start()


def new_game():
    """Sāk jaunu partiju (vārds un admina režīms saglabājas)."""
    global game, state, start_time, paused, saved, send_status, admin_points

    game = Game()
    state = "playing"
    start_time = time.time()
    paused = 0
    saved = False
    send_status = ""
    admin_points = ""


# ---------------------------------------------------------------- 4. ZĪMĒŠANA
def draw():
    """Uzzīmē visu ekrānu atkarībā no pašreizējā stāvokļa (state)."""
    screen.fill(BG)

    # ----- Izvēlne: vārda un admina paroles ievade -----
    if state == "menu":
        text_center("2048 KUBI", 170, font)

        # Vārda lauks
        text("Ievadi savu vārdu:", 110, 250)
        draw_input_box(110, 278, 300, 44, player_name, active_field == "name")

        # Admina lauks (parole tiek rādīta kā zvaigznītes)
        text("Admins (parole):", 110, 345, small, GRAY)
        draw_input_box(110, 373, 300, 44, "*" * len(admin_pass),
                       active_field == "admin")

        # Ziņojums zem laukiem
        if menu_error:
            text_center(menu_error, 450, small, RED)
        elif player_name:
            text_center("Nospied ENTER, lai sāktu", 450)
        else:
            text_center("Vārds nedrīkst būt tukšs", 450, small, RED)

        text_center("TAB - nomainīt lauku", 490, small, GRAY)

    # ----- Spēles ekrāns (arī pauze, admina ievade un beigu ekrāns) -----
    else:
        text("2048 KUBI", 180, 10, font)
        text("Punkti: " + str(game.score), 20, 65)
        text("Lielākais: " + str(game.best_tile), 300, 65)

        # Admina režīma norāde augšējā labajā stūrī
        if admin_mode:
            text("ADMIN", 430, 15, small, RED)

        # Laiks: pauzes un admina ievades laikā taimeris apstājas
        seconds = int(time.time() - start_time - paused)
        if state in ("paused", "admin_input"):
            seconds = int(pause_time - start_time - paused)

        text("Laiks: " + str(seconds) + " s", 20, 100)
        text(player_name, 300, 100)

        # Režģa fons
        pygame.draw.rect(screen, (187, 173, 160), (20, 145, 480, 480))

        # Katra režģa rūtiņa
        for y in range(4):
            for x in range(4):
                value = game.grid[y][x]

                rect = (30 + x * 117, 155 + y * 117, 107, 107)

                color = colors.get(value, (205, 193, 180))

                pygame.draw.rect(screen, color, rect)

                # Skaitli zīmējam rūtiņas vidū
                if value:
                    img = font.render(str(value), True, BLACK)
                    screen.blit(img, img.get_rect(center=(
                        rect[0] + 53, rect[1] + 53
                    )))

        # Padomi spēlētājam
        text("E - Noņemt 2 kvadrātus", 20, 645)
        text("R - Atstāt lielāko", 280, 645)

        # Admina taustiņu padomi
        if admin_mode:
            text("T - pievienot punktus", 20, 672, small, RED)
            text("G - beigt spēli", 280, 672, small, RED)

        # Pauzes uzraksts
        if state == "paused":
            text("PAUZE", 200, 300, font, RED)
            text("Nospied P, lai turpinātu", 125, 350)

        # Admina punktu ievades logs virs režģa
        if state == "admin_input":
            pygame.draw.rect(screen, WHITE, (60, 250, 400, 190))
            pygame.draw.rect(screen, RED, (60, 250, 400, 190), 3)
            text_center("Pievienot punktus", 280, small, RED)
            draw_input_box(110, 305, 300, 44, admin_points, True)
            text_center("ENTER - apstiprināt", 385, small, BLACK)
            text_center("ESC - atcelt", 412, small, GRAY)

        # Beigu ekrāns
        if state == "game_over":
            text("TU UZVARĒJI!" if game.won else "SPĒLE BEIGUSIES",
                 110, 280, font)
            text("Punkti: " + str(game.score), 190, 340)
            text("Nospied R, lai sāktu no jauna", 100, 400)

            # Rezultāta sūtīšanas statuss
            if send_status == "sending":
                text_center("Sūta rezultātu...", 450)
            elif send_status == "ok":
                text_center("Rezultāts nosūtīts uz tabulu!", 450, small, GREEN)
            elif send_status == "error":
                text_center("Neizdevās nosūtīt (saglabāts lokāli)", 450,
                            small, RED)


# ---------------------------------------------------------------- 5. GALVENAIS CIKLS
running = True

while running:

    # Apstrādājam visus notikumus (taustiņi, pele, loga aizvēršana)
    for event in pygame.event.get():

        # Loga aizvēršana
        if event.type == pygame.QUIT:
            running = False

        # ===== TASTATŪRA =====
        if event.type == pygame.KEYDOWN:

            # ----- Izvēlne -----
            if state == "menu":

                if event.key == pygame.K_RETURN:
                    # ENTER: pārbaudām vārdu un paroli, tad sākam spēli
                    name = player_name.strip()

                    if not name:
                        menu_error = "Vārds nedrīkst būt tukšs"
                    elif admin_pass and admin_pass != ADMIN_PASSWORD:
                        # Parole ievadīta, bet nepareiza
                        menu_error = "Nepareiza admina parole"
                        admin_pass = ""
                    else:
                        player_name = name
                        # Admina režīms ieslēdzas tikai ar pareizu paroli
                        admin_mode = (admin_pass == ADMIN_PASSWORD)
                        new_game()

                elif event.key == pygame.K_TAB:
                    # TAB: pārslēdzam aktīvo lauku
                    active_field = "admin" if active_field == "name" else "name"

                elif event.key == pygame.K_BACKSPACE:
                    # Dzēšam pēdējo simbolu aktīvajā laukā
                    if active_field == "name":
                        player_name = player_name[:-1]
                    else:
                        admin_pass = admin_pass[:-1]
                    menu_error = ""

                elif event.unicode and event.unicode.isprintable():
                    # Parasts simbols: pievienojam aktīvajam laukam
                    if active_field == "name" and len(player_name) < NAME_MAX:
                        player_name += event.unicode
                    elif active_field == "admin" and len(admin_pass) < ADMIN_PASS_MAX:
                        admin_pass += event.unicode
                    menu_error = ""

            # ----- Spēle notiek -----
            elif state == "playing":

                if event.key == pygame.K_p:
                    # P: pauze
                    state = "paused"
                    pause_time = time.time()

                # Kustība ar bultiņām vai WASD
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    game.move("left")

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.move("right")

                elif event.key in (pygame.K_UP, pygame.K_w):
                    game.move("up")

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    game.move("down")

                elif event.key == pygame.K_e:
                    # E: noņemt 2 kvadrātus (nepieciešams 512)
                    game.start_remove_mode()

                elif event.key == pygame.K_r:
                    # R: atstāt tikai lielāko kvadrātu
                    game.keep_largest()

                # --- Admina taustiņi (darbojas tikai admina režīmā) ---
                elif admin_mode and event.key == pygame.K_t:
                    # T: atvērt punktu pievienošanas logu (taimeris apstājas)
                    state = "admin_input"
                    pause_time = time.time()
                    admin_points = ""

                elif admin_mode and event.key == pygame.K_g:
                    # G: beigt spēli pirms laika.
                    # Atzīmējam spēli kā beigušos; saglabāšanu izdara bloks zemāk.
                    game.game_over = True

                # Ja spēle beigusies vai uzvarēta — pārejam uz beigu ekrānu
                if game.won or game.game_over:
                    state = "game_over"

                    # Rezultātu saglabājam tikai vienu reizi
                    if not saved:
                        save_score()
                        saved = True

            # ----- Pauze -----
            elif state == "paused":
                if event.key == pygame.K_p:
                    # Pauzes laiku pieskaitām pie "paused", lai taimeris to neņemtu vērā
                    paused += time.time() - pause_time
                    state = "playing"

            # ----- Admina punktu ievade -----
            elif state == "admin_input":

                if event.key == pygame.K_RETURN:
                    # ENTER: pievienojam ievadītos punktus
                    if admin_points:
                        game.score += int(admin_points)
                    paused += time.time() - pause_time
                    state = "playing"

                elif event.key == pygame.K_ESCAPE:
                    # ESC: atcelt, punkti netiek pievienoti
                    paused += time.time() - pause_time
                    state = "playing"

                elif event.key == pygame.K_BACKSPACE:
                    admin_points = admin_points[:-1]

                elif (event.unicode.isascii() and event.unicode.isdigit()
                      and len(admin_points) < ADMIN_POINTS_MAX):
                    # Pieņemam tikai ciparus 0-9
                    admin_points += event.unicode

            # ----- Spēle beigusies -----
            elif state == "game_over":
                if event.key == pygame.K_r:
                    new_game()

        # ===== PELE =====
        if event.type == pygame.MOUSEBUTTONDOWN:

            # Izvēlnē ar peli var izvēlēties ievades lauku
            if state == "menu":
                if pygame.Rect(110, 278, 300, 44).collidepoint(event.pos):
                    active_field = "name"
                elif pygame.Rect(110, 373, 300, 44).collidepoint(event.pos):
                    active_field = "admin"

            # Spēlē ar peli noņem kvadrātus (režīms E)
            elif state == "playing":
                # Pārrēķinām peles koordinātas par režģa rūtiņu
                x = (event.pos[0] - 30) // 117
                y = (event.pos[1] - 155) // 117

                if game.remove_mode:
                    if 0 <= x < 4 and 0 <= y < 4:
                        game.remove_tile(y, x)

    # Zīmējam kadru un ierobežojam ātrumu līdz 60 FPS
    draw()
    pygame.display.update()

    clock.tick(60)

pygame.quit()
