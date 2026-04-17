import tkinter as tk
import csv
import random
import os

BG_MAIN = "#1a1a2e"
BG_CARD = "#16213e"
BG_CARD_EMPTY = "#0f1b30"
FG_NUM = "#e94560"
FG_NAME = "#ffffff"
FG_TITLE = "#e94560"
BTN_BG = "#e94560"
BTN_ACTIVE = "#c73652"

CSV_PATH = os.path.join(os.path.dirname(__file__), "idols.csv")


def load_idols():
    idols = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[0].strip():
                idols.append((int(row[0]), row[1]))
    return idols


def draw_hand(idols, n=13):
    deck = idols * 3  # 52種 × 3枚 = 156枚
    hand = random.sample(deck, n)
    hand.sort(key=lambda x: x[0])
    return hand


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ミリオンマージャン")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.idols = load_idols()
        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text="ミリオンマージャン",
            font=("Yu Gothic UI", 18, "bold"),
            bg=BG_MAIN,
            fg=FG_TITLE,
        ).pack(pady=(20, 4))

        tk.Label(
            self,
            text="52種×3枚のデッキから13枚ドロー",
            font=("Yu Gothic UI", 9),
            bg=BG_MAIN,
            fg="#8888aa",
        ).pack(pady=(0, 12))

        self.tile_frame = tk.Frame(self, bg=BG_MAIN)
        self.tile_frame.pack(padx=24, pady=4)

        self.cards = []
        for i in range(13):
            r, c = divmod(i, 7)
            frame = tk.Frame(
                self.tile_frame,
                bg=BG_CARD_EMPTY,
                relief="groove",
                bd=2,
                width=78,
                height=80,
            )
            frame.grid(row=r, column=c, padx=4, pady=4)
            frame.pack_propagate(False)

            num = tk.Label(frame, text="", font=("Yu Gothic UI", 11, "bold"),
                           bg=BG_CARD_EMPTY, fg=FG_NUM)
            num.pack(pady=(10, 2))

            name = tk.Label(frame, text="", font=("Yu Gothic UI", 8),
                            bg=BG_CARD_EMPTY, fg=FG_NAME, wraplength=70)
            name.pack()

            self.cards.append((frame, num, name))

        tk.Button(
            self,
            text="  ドロー  ",
            font=("Yu Gothic UI", 13, "bold"),
            bg=BTN_BG,
            fg="white",
            activebackground=BTN_ACTIVE,
            activeforeground="white",
            relief="flat",
            padx=24,
            pady=8,
            cursor="hand2",
            command=self._draw,
        ).pack(pady=(16, 24))

    def _draw(self):
        hand = draw_hand(self.idols)
        for i, (frame, num, name) in enumerate(self.cards):
            idol_num, idol_name = hand[i]
            frame.configure(bg=BG_CARD)
            num.configure(text=str(idol_num), bg=BG_CARD)
            name.configure(text=idol_name, bg=BG_CARD)


if __name__ == "__main__":
    App().mainloop()
