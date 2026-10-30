
import pygame
import sys
import os
import time
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.logic import Game

pygame.init()

screen = pygame.display.set_mode((520, 700))
pygame.display.set_caption("2048 Kubi")

font = pygame.font.SysFont("arial", 30, bold=True)
small = pygame.font.SysFont("arial", 19)

BG = (250, 248, 239)
BLACK = (40, 40, 40)
WHITE = (255, 255, 255)

game = Game()

state = "menu"
start_time = 0
pause_time = 0
paused = 0
saved = False

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

def text(msg, x, y, size=small, color=BLACK):
    img = size.render(str(msg), True, color)
    screen.blit(img, (x, y))


def save_score():
    file = "data/leaderboard.json"

    try:
        with open(file, "r") as f:
            records = json.load(f)
    except:
        records = []

    records.append({
        "score": game.score,
        "time": int(time.time() - start_time - paused),
        "best_tile": game.best_tile
    })

    records.sort(key=lambda x: x["score"], reverse=True)

    os.makedirs("data", exist_ok=True)

    with open(file, "w") as f:
        json.dump(records[:10], f, indent=4)


def new_game():
    global game, state, start_time, paused, saved

    game = Game()
    state = "playing"
    start_time = time.time()
    paused = 0
    saved = False


def draw():
    screen.fill(BG)

    if state == "menu":
        text("2048 KUBI", 170, 220, font)
        text("Nospied ENTER, lai sāktu", 115, 350)
        
    else:
        text("2048 KUBI", 180, 10, font)
        text("Punkti: " + str(game.score), 20, 65)
        text("Lielākais: " + str(game.best_tile), 300, 65)

        seconds = int(time.time() - start_time - paused)
        if state == "paused":
            seconds = int(pause_time - start_time - paused)

        text("Laiks: " + str(seconds) + " s", 20, 100)

        pygame.draw.rect(screen, (187, 173, 160), (20, 145, 480, 480))

        for y in range(4):
            for x in range(4):
                value = game.grid[y][x]

                rect = (30 + x * 117, 155 + y * 117, 107, 107)

                color = colors.get(value, (205, 193, 180))

                pygame.draw.rect(screen, color, rect)

                if value:
                    img = font.render(str(value), True, BLACK)
                    screen.blit(img, img.get_rect(center=(
                        rect[0] + 53, rect[1] + 53
                    )))

        text("E - Noņemt 2 kvadrātus", 20, 645)
        text("R - Atstāt lielāko", 280, 645)

        if state == "paused":
            text("PAUZE", 200, 300, font, (180, 70, 40))
            text("Nospied P, lai turpinātu", 125, 350)

        if state == "game_over":
            text("TU UZVARĒJI!" if game.won else "SPĒLE BEIGUSIES",
                 110, 280, font)
            text("Punkti: " + str(game.score), 190, 340)
            text("Nospied R, lai sāktu no jauna", 100, 400)


running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if state == "menu":
                if event.key == pygame.K_RETURN:
                    new_game()

            elif state == "playing":

                if event.key == pygame.K_p:
                    state = "paused"
                    pause_time = time.time()

                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    game.move("left")

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.move("right")

                elif event.key in (pygame.K_UP, pygame.K_w):
                    game.move("up")

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    game.move("down")

                elif event.key == pygame.K_e:
                    game.start_remove_mode()

                elif event.key == pygame.K_r:
                    game.keep_largest()

                if game.won or game.game_over:
                    state = "game_over"

                    if not saved:
                        save_score()
                        saved = True

            elif state == "paused":
                if event.key == pygame.K_p:
                    paused += time.time() - pause_time
                    state = "playing"

            elif state == "game_over":
                if event.key == pygame.K_r:
                    new_game()

        if event.type == pygame.MOUSEBUTTONDOWN and state == "playing":

            x = (event.pos[0] - 30) // 117
            y = (event.pos[1] - 155) // 117

            if game.remove_mode:
                if 0 <= x < 4 and 0 <= y < 4:
                    game.remove_tile(y, x)

    draw()
    pygame.display.update()

    pygame.time.Clock().tick(60)

pygame.quit()
