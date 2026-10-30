import random


class Game:
    def __init__(self):
        self.size = 4
        self.reset_game()

    def reset_game(self):
        self.grid = [[0] * self.size for _ in range(self.size)]
        self.score = 0
        self.moves = 0
        self.remove_available = True
        self.remove_mode = False
        self.remove_left = 0
        self.clear_uses = 2
        self.won = False
        self.game_over = False
        self.best_tile = 0
        self.add_tile()
        self.add_tile()

    def add_tile(self):
        empty = [(r, c) for r in range(4) for c in range(4)
                 if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 4 if random.random() < 0.1 else 2

    def move(self, direction):
        if self.game_over or self.won or self.remove_mode:
            return False

        old = [row[:] for row in self.grid]
        gained = 0

        for i in range(4):
            if direction in ("left", "right"):
                line = self.grid[i][:]
            else:
                line = [self.grid[r][i] for r in range(4)]

            if direction in ("right", "down"):
                line.reverse()

            values = [v for v in line if v]
            result = []
            j = 0

            while j < len(values):
                if j + 1 < len(values) and values[j] == values[j + 1]:
                    merged = values[j] * 2
                    result.append(merged)
                    gained += merged
                    self.best_tile = max(self.best_tile, merged)
                    j += 2
                else:
                    result.append(values[j])
                    j += 1

            result += [0] * (4 - len(result))
            if direction in ("right", "down"):
                result.reverse()

            if direction in ("left", "right"):
                self.grid[i] = result
            else:
                for r in range(4):
                    self.grid[r][i] = result[r]

        if self.grid != old:
            self.score += gained
            self.moves += 1
            self.add_tile()
            self.check_state()
            return True

        return False

    def check_state(self):
        self.best_tile = max(self.best_tile,
                             max(max(row) for row in self.grid))
        if any(2048 in row for row in self.grid):
            self.won = True
            return

        for r in range(4):
            for c in range(4):
                if self.grid[r][c] == 0:
                    return
                if c < 3 and self.grid[r][c] == self.grid[r][c + 1]:
                    return
                if r < 3 and self.grid[r][c] == self.grid[r + 1][c]:
                    return

        self.game_over = True

    def start_remove_mode(self):
        if (self.remove_available and not self.game_over and not self.won
                and any(512 in row for row in self.grid)):
            self.remove_mode = True
            self.remove_left = 2
            return True
        return False

    def remove_tile(self, row, col):
        if not self.remove_mode or self.grid[row][col] == 0:
            return False

        self.grid[row][col] = 0
        self.remove_left -= 1

        if self.remove_left == 0:
            self.remove_mode = False
            self.remove_available = False

        self.check_state()
        return True

    def keep_largest(self):
        if self.clear_uses <= 0 or self.game_over or self.won:
            return False

        largest = max(max(row) for row in self.grid)
        self.grid = [[0] * 4 for _ in range(4)]

        if largest:
            self.grid[1][1] = largest

        self.clear_uses -= 1
        self.check_state()
        return True
