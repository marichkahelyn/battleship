import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox

GRID = 10
SHIPS = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

IO_LOCK = threading.Lock()  # щоб обидва вікна не читали одночасно

def start_backend():
    exe = "battleship_backend.exe" if os.name == "nt" else "./battleship_backend"
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    # ініціалізація
    with IO_LOCK:
        proc.stdin.write("INIT\n"); proc.stdin.flush()
        _ = proc.stdout.readline()
    return proc

def send_status(proc):
    with IO_LOCK:
        proc.stdin.write("STATUS\n"); proc.stdin.flush()
        line = proc.stdout.readline().strip()
    return line  # NOTREADY або "TURN 1"

def send_state(proc, player):
    with IO_LOCK:
        proc.stdin.write(f"STATE {player}\n"); proc.stdin.flush()
        header = proc.stdout.readline().strip()  # PLAYER ...
        _ = proc.stdout.readline().strip()        # OWN
        own = [list(proc.stdout.readline().strip()) for _ in range(GRID)]
        _ = proc.stdout.readline().strip()        # ENEMY
        enemy = [list(proc.stdout.readline().strip()) for _ in range(GRID)]
        _ = proc.stdout.readline().strip()        # END
    return own, enemy

def send_set(proc, player, length, x, y, orient):
    with IO_LOCK:
        proc.stdin.write(f"SET {player} {length} {x} {y} {orient}\n"); proc.stdin.flush()
        resp = proc.stdout.readline().strip()
    return resp

def send_ready(proc, player):
    with IO_LOCK:
        proc.stdin.write(f"READY {player}\n"); proc.stdin.flush()
        resp = proc.stdout.readline().strip()
    return resp

def send_shot(proc, player, x, y):
    with IO_LOCK:
        proc.stdin.write(f"SHOT {player} {x} {y}\n"); proc.stdin.flush()
        resp = proc.stdout.readline().strip()
    return resp


class PlayerWindow(tk.Toplevel):
    def __init__(self, master, player_num, proc):
        super().__init__(master)
        self.proc = proc
        self.player = player_num
        self.title(f"Гравець {player_num}")
        self.orient = 'H'
        self.selected_len = None
        self.placing = True
        self.turn = False
        self.available = SHIPS.copy()

        self.own_btns = [[None]*GRID for _ in range(GRID)]
        self.enemy_btns = [[None]*GRID for _ in range(GRID)]

        self.build_ui()
        self.poll()

    def build_ui(self):
        left = tk.Frame(self); left.grid(row=0, column=0, padx=5, pady=5)
        right = tk.Frame(self); right.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(left, text="Ваше поле").grid(row=0, column=0, columnspan=GRID)
        tk.Label(right, text="Поле супротивника").grid(row=0, column=0, columnspan=GRID)

        for i in range(GRID):
            for j in range(GRID):
                b = tk.Button(left, width=2, height=1, bg="lightblue")
                b.grid(row=i+1, column=j)
                b.bind("<Enter>", lambda e, x=i, y=j: self.preview(x,y))
                b.bind("<Leave>", lambda e: self.clear_preview())
                b.bind("<Button-1>", lambda e, x=i, y=j: self.place_ship(x,y))
                self.own_btns[i][j] = b

        for i in range(GRID):
            for j in range(GRID):
                b = tk.Button(right, width=2, height=1, bg="white",
                              command=lambda x=i, y=j: self.try_shot(x,y))
                b.grid(row=i+1, column=j)
                self.enemy_btns[i][j] = b

        # панель керування
        ctrl = tk.Frame(self); ctrl.grid(row=1, column=0, columnspan=2, pady=5)
        tk.Button(ctrl, text="Повернути (H/V)", command=self.toggle_orient).grid(row=0, column=0, padx=5)

        # кнопки кораблів
        self.ship_btns = []
        col = 1
        for L in sorted(set(SHIPS), reverse=True):
            btn = tk.Button(ctrl, text=f"{L}-палубний", command=lambda l=L: self.select_ship(l))
            btn.grid(row=0, column=col, padx=2)
            self.ship_btns.append((L, btn))
            col += 1

        tk.Button(ctrl, text="Готово", command=self.make_ready).grid(row=0, column=col, padx=5)

        self.status = tk.Label(self, text="Виберіть корабель і клацніть по полі")
        self.status.grid(row=2, column=0, columnspan=2, pady=3)

    def toggle_orient(self):
        self.orient = 'V' if self.orient == 'H' else 'H'
        self.status.config(text=f"Орієнтація: {self.orient}")

    def select_ship(self, length):
        self.selected_len = length
        self.status.config(text=f"Вибрано {length}-палубний, орієнтація {self.orient}")

    def preview(self, x, y):
        if not self.placing or not self.selected_len:
            return
        for i in range(self.selected_len):
            xx = x + (0 if self.orient == 'H' else i)
            yy = y + (i if self.orient == 'H' else 0)
            if 0 <= xx < GRID and 0 <= yy < GRID:
                if self.own_btns[xx][yy]["bg"] in ("lightblue", "gray"):
                    self.own_btns[xx][yy].config(bg="gray")

    def clear_preview(self):
        if not self.placing:
            return
        for i in range(GRID):
            for j in range(GRID):
                if self.own_btns[i][j]["bg"] == "gray":
                    self.own_btns[i][j].config(bg="lightblue")

    def place_ship(self, x, y):
        if not self.placing or not self.selected_len:
            return
        resp = send_set(self.proc, self.player, self.selected_len, x, y, self.orient)
        if resp == "OK SET":
            # зафарбувати
            for i in range(self.selected_len):
                xx = x + (0 if self.orient == 'H' else i)
                yy = y + (i if self.orient == 'H' else 0)
                self.own_btns[xx][yy].config(bg="navy")
            self.available.remove(self.selected_len)
            # відключити кнопку цього розміру (якщо треба)
            for (L, btn) in self.ship_btns:
                if L == self.selected_len:
                    if self.available.count(L) == 0:
                        btn.config(state=tk.DISABLED)
            self.selected_len = None
            if not self.available:
                self.status.config(text="Усі кораблі виставлені. Натисніть 'Готово'.")
        else:
            messagebox.showerror("Помилка", "Не можна поставити корабель сюди.")

    def make_ready(self):
        if self.placing and self.available:
            messagebox.showinfo("Ще рано", "Спочатку розстав усі кораблі.")
            return
        resp = send_ready(self.proc, self.player)
        if resp.startswith("OK READY"):
            self.placing = False
            self.status.config(text="Очікуємо другого гравця...")
        else:
            messagebox.showerror("Помилка", resp)

    def poll(self):
        """Опитування бекенда: хто ходить і які поля"""
        try:
            status = send_status(self.proc)
            if status.startswith("TURN"):
                turn_num = int(status.split()[1])
                self.turn = (turn_num == self.player)
                if self.turn and not self.placing:
                    self.status.config(text="Твій хід")
                elif not self.placing:
                    self.status.config(text="Хід супротивника")
            own, enemy = send_state(self.proc, self.player)
            for i in range(GRID):
                for j in range(GRID):
                    c = own[i][j]
                    if c == '.':
                        if self.own_btns[i][j]["bg"] not in ("navy",):
                            self.own_btns[i][j].config(bg="lightblue")
                    elif c == 'S':
                        self.own_btns[i][j].config(bg="navy")
                    elif c == 'H':
                        self.own_btns[i][j].config(bg="red")
                    elif c == 'M':
                        self.own_btns[i][j].config(bg="lightgray")

                    e = enemy[i][j]
                    if e == 'H':
                        self.enemy_btns[i][j].config(bg="red")
                    elif e == 'M':
                        self.enemy_btns[i][j].config(bg="lightgray")
        finally:
            self.after(700, self.poll)

    def try_shot(self, x, y):
        if self.placing:
            return
        if not self.turn:
            return
        resp = send_shot(self.proc, self.player, x, y)
        if resp == "HIT":
            self.enemy_btns[x][y].config(bg="red")
            self.status.config(text="Влучив! Стріляй ще.")
        elif resp == "SUNK":
            self.enemy_btns[x][y].config(bg="black")
            self.status.config(text="Потопив! Стріляй ще.")
        elif resp.startswith("WIN"):
            self.enemy_btns[x][y].config(bg="red")
            messagebox.showinfo("Перемога", f"Гравець {self.player} переміг!")
        elif resp == "MISS":
            self.enemy_btns[x][y].config(bg="lightgray")
            self.turn = False
            self.status.config(text="Промах. Чекай.")
        elif resp.startswith("ERR"):
            messagebox.showerror("Помилка", resp)


def main():
    proc = start_backend()
    root = tk.Tk()
    root.withdraw()  # головне вікно ховаємо
    p1 = PlayerWindow(root, 1, proc)
    p2 = PlayerWindow(root, 2, proc)
    root.mainloop()

if __name__ == "__main__":
    main()
