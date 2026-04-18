# tkinter: Python標準のGUIライブラリ（画面を作るために使う）
import tkinter as tk
# csv: CSVファイル（カンマ区切りデータ）を読み込むライブラリ
import csv
# random: ランダム抽出に使う
import random
import os
# @dataclass: クラス定義を短く書ける仕組み（後述）
from dataclasses import dataclass

# --- 画面の色を定数で管理（変更が1箇所で済む） ---
BG_MAIN = "#1a1a2e"
BG_CARD = "#16213e"
BG_CARD_EMPTY = "#0f1b30"
FG_NAME = "#ffffff"
FG_TITLE = "#e94560"
BTN_BG = "#e94560"
BTN_ACTIVE = "#c73652"
FONT_FAMILY = "Meiryo UI"

# __file__ = このスクリプト自身のパス。同じフォルダにあるCSVを指定
CSV_PATH = os.path.join(os.path.dirname(__file__), "idols.csv")

# 属性牌のデータ。各要素は (ID, 内部名, 表示名) のタプル
ATTRIBUTE_TILES = [
    (101, "Princess", "Princess"),
    (102, "Fairy", "Fairy"),
    (103, "Angel", "Angel"),
]


# @dataclass を付けると __init__ が自動生成される
# 普通のクラスで書く frame=frame, label=label の定型コードが不要になる
@dataclass
class CardWidget:
    frame: tk.Frame
    label: tk.Label


def load_idols():
    """CSVファイルからアイドルデータを読み込んで返す"""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"アイドルデータが見つかりません: {CSV_PATH}")
    idols = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.reader(f):
            # 行が3列以上あり、1列目が空でないものだけ処理
            if len(row) >= 3 and row[0].strip():
                try:
                    # (ID, 内部名, 表示名) のタプルとして追加
                    idols.append((int(row[0]), row[1], row[2]))
                except ValueError:
                    # IDが数値でない行はスキップ
                    continue
    return idols


def draw_hand(deck, n=13):
    """デッキからn枚をランダムに引き、ID順にソートして返す"""
    if len(deck) < n:
        raise ValueError(f"デッキ枚数({len(deck)})が手牌枚数({n})未満")
    # sample: 元のリストを変えずにランダムにn個選ぶ
    hand = random.sample(deck, n)
    # lambda: 1行で書ける無名関数。x[0](=ID)を基準にソート
    hand.sort(key=lambda x: x[0])
    return hand


# tk.Tk を継承してアプリのメインウィンドウを作る
class App(tk.Tk):
    def __init__(self):
        # super().__init__(): 親クラス(tk.Tk)の初期化を呼ぶ
        # これを忘れるとウィンドウが正しく作られない
        super().__init__()
        self.title("ミリオンマージャン")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        idols = load_idols()
        # 53種×3枚＋属性牌3枚 = 162枚のデッキを構築
        self._deck = idols * 3 + ATTRIBUTE_TILES
        self._build_ui()

    def _build_ui(self):
        """画面上のウィジェット（部品）を配置する"""
        tk.Label(
            self,
            text="ミリオンマージャン",
            font=(FONT_FAMILY, 18, "bold"),
            bg=BG_MAIN,
            fg=FG_TITLE,
        ).pack(pady=(20, 4))

        tk.Label(
            self,
            text="53種×3枚+属性牌3枚のデッキから13枚ドロー",
            font=(FONT_FAMILY, 9),
            bg=BG_MAIN,
            fg="#8888aa",
        ).pack(pady=(0, 12))

        # 13枚のカードを横並びにするコンテナ
        self.tile_frame = tk.Frame(self, bg=BG_MAIN)
        self.tile_frame.pack(padx=24, pady=4)

        self.cards = []
        for i in range(13):
            # 各カードの枠。width/height で固定サイズを指定
            frame = tk.Frame(
                self.tile_frame,
                bg=BG_CARD_EMPTY,
                relief="groove",
                bd=2,
                width=56,
                height=100,
            )
            # grid: 格子状に配置。row=0, column=i で横1列に並べる
            frame.grid(row=0, column=i, padx=3, pady=4)
            # pack_propagate(False): 中身のサイズに合わせて枠が縮むのを防ぐ
            # これがないと width/height の指定が無視される
            frame.pack_propagate(False)

            label = tk.Label(frame, text="", font=(FONT_FAMILY, 8),
                             bg=BG_CARD_EMPTY, fg=FG_NAME, wraplength=50)
            # expand=True: 親フレーム内で上下左右の中央に配置
            label.pack(expand=True)

            self.cards.append(CardWidget(frame=frame, label=label))

        # command=self._draw: ボタン押下時に _draw メソッドを呼ぶ
        tk.Button(
            self,
            text="  ドロー  ",
            font=(FONT_FAMILY, 13, "bold"),
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
        """ドローボタン押下時: デッキから13枚引いてカードに表示"""
        hand = draw_hand(self._deck)
        # zip: 2つのリストを同時にループする関数
        # cards[0]とhand[0], cards[1]とhand[1]... を対にして処理
        for card, (_, _, display_name) in zip(self.cards, hand):
            card.frame.configure(bg=BG_CARD)
            card.label.configure(text=display_name, bg=BG_CARD)


# __name__ == "__main__": このファイルが直接実行された時だけ True
# 他のファイルから import された時は実行されない（テスト時などに便利）
if __name__ == "__main__":
    # mainloop(): ウィンドウを表示し、ユーザー操作を待ち続ける
    App().mainloop()