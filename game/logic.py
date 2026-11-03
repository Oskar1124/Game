# Spēles loģika (2048). Šeit nav zīmēšanas — tikai noteikumi un stāvoklis.
# Klients (client/main.py) izmanto klasi Game un attēlo tās datus ekrānā.
import random


class Game:
    """Viena 2048 spēle: režģis, punkti, uzvara/zaudējums un īpašās spējas."""

    def __init__(self):
        # Režģa izmērs (4x4)
        self.size = 4
        self.reset_game()

    def reset_game(self):
        """Sagatavo jaunu spēli: tukšs režģis, nulles punkti un sākuma karogi."""
        self.grid = [[0] * self.size for _ in range(self.size)]  # 4x4 režģis ar nullēm
        self.score = 0               # kopējie punkti
        self.moves = 0               # veikto gājienu skaits
        self.remove_available = True # vai vēl var izmantot "noņemt 2 kvadrātus" (E)
        self.remove_mode = False     # vai šobrīd notiek kvadrātu noņemšana
        self.remove_left = 0         # cik kvadrātus vēl drīkst noņemt
        self.clear_uses = 2          # cik reižu vēl drīkst izmantot "atstāt lielāko" (R)
        self.won = False             # uzvara (sasniegts 2048)
        self.game_over = False       # spēle beigusies (vairs nav gājienu)
        self.best_tile = 0           # lielākais kvadrāts, kas bijis spēlē
        # Spēles sākumā uz režģa ir divi kvadrāti
        self.add_tile()
        self.add_tile()

    def add_tile(self):
        """Pievieno jaunu kvadrātu (2 vai 4) nejaušā tukšā vietā."""
        empty = [(r, c) for r in range(4) for c in range(4)
                 if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            # 90% iespēja uz 2, 10% iespēja uz 4
            self.grid[r][c] = 4 if random.random() < 0.1 else 2

    def move(self, direction):
        """Pārvieto visus kvadrātus virzienā left/right/up/down.

        Atgriež True, ja režģis mainījās, citādi False.
        """
        # Gājienus nevar veikt, ja spēle beigusies vai notiek kvadrātu noņemšana
        if self.game_over or self.won or self.remove_mode:
            return False

        old = [row[:] for row in self.grid]  # vecā režģa kopija, lai redzētu, vai kaut kas mainījās
        gained = 0                           # punkti, kas iegūti šajā gājienā

        # Apstrādājam katru rindu (left/right) vai kolonnu (up/down)
        for i in range(4):
            if direction in ("left", "right"):
                line = self.grid[i][:]
            else:
                line = [self.grid[r][i] for r in range(4)]

            # Uz right/down apgriežam līniju, lai vienmēr virzītos "uz sākumu"
            if direction in ("right", "down"):
                line.reverse()

            # Izmetam nulles un saliekam vienādos blakus kvadrātus
            values = [v for v in line if v]
            result = []
            j = 0

            while j < len(values):
                if j + 1 < len(values) and values[j] == values[j + 1]:
                    merged = values[j] * 2          # divi vienādi kvadrāti saplūst
                    result.append(merged)
                    gained += merged                # punkti = jaunā kvadrāta vērtība
                    self.best_tile = max(self.best_tile, merged)
                    j += 2
                else:
                    result.append(values[j])
                    j += 1

            # Aizpildām līniju ar nullēm līdz 4 un apgriežam atpakaļ, ja vajag
            result += [0] * (4 - len(result))
            if direction in ("right", "down"):
                result.reverse()

            # Ierakstām rezultātu atpakaļ režģī
            if direction in ("left", "right"):
                self.grid[i] = result
            else:
                for r in range(4):
                    self.grid[r][i] = result[r]

        # Ja režģis mainījās — gājiens ir derīgs
        if self.grid != old:
            self.score += gained
            self.moves += 1
            self.add_tile()       # pēc gājiena parādās jauns kvadrāts
            self.check_state()    # pārbaudām uzvaru / zaudējumu
            return True

        return False

    def check_state(self):
        """Pārbauda, vai spēle uzvarēta (2048) vai zaudēta (nav gājienu)."""
        # Atjaunojam lielāko kvadrātu
        self.best_tile = max(self.best_tile,
                             max(max(row) for row in self.grid))

        # Uzvara: uz režģa ir 2048
        if any(2048 in row for row in self.grid):
            self.won = True
            return

        # Ja ir tukša vieta vai vienādi blakus kvadrāti — gājiens vēl ir iespējams
        for r in range(4):
            for c in range(4):
                if self.grid[r][c] == 0:
                    return
                if c < 3 and self.grid[r][c] == self.grid[r][c + 1]:
                    return
                if r < 3 and self.grid[r][c] == self.grid[r + 1][c]:
                    return

        # Citādi gājienu vairs nav — spēle beigusies
        self.game_over = True

    def start_remove_mode(self):
        """Ieslēdz režīmu "noņemt 2 kvadrātus" (taustiņš E).

        Pieejams vienu reizi spēlē un tikai tad, ja uz režģa ir 512.
        """
        if (self.remove_available and not self.game_over and not self.won
                and any(512 in row for row in self.grid)):
            self.remove_mode = True
            self.remove_left = 2
            return True
        return False

    def remove_tile(self, row, col):
        """Noņem kvadrātu no norādītās rūtiņas (izsauc ar peles klikšķi)."""
        if not self.remove_mode or self.grid[row][col] == 0:
            return False

        self.grid[row][col] = 0
        self.remove_left -= 1

        # Kad noņemti 2 kvadrāti — režīms izslēdzas un vairs nav pieejams
        if self.remove_left == 0:
            self.remove_mode = False
            self.remove_available = False

        self.check_state()
        return True

    def keep_largest(self):
        """Atstāj tikai lielāko kvadrātu (taustiņš R). Drīkst izmantot 2 reizes."""
        if self.clear_uses <= 0 or self.game_over or self.won:
            return False

        largest = max(max(row) for row in self.grid)
        self.grid = [[0] * 4 for _ in range(4)]  # notīrām visu režģi

        # Lielāko kvadrātu ieliekam režģa vidū
        if largest:
            self.grid[1][1] = largest

        self.clear_uses -= 1
        self.check_state()
        return True
