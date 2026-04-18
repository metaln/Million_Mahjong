# tkinter: Python標準GUIライブラリ（画面構築用）
import tkinter as tk
# csv: CSV（カンマ区切り）読み込みライブラリ
import csv
# random: ランダム抽出用
import random
import os
# @dataclass: クラス定義を短縮（後述）
from dataclasses import dataclass

# --- 画面の色を定数管理（変更1箇所） ---
BG_MAIN = "#1a1a2e"
BG_CARD = "#16213e"
BG_CARD_EMPTY = "#0f1b30"
FG_NAME = "#ffffff"
FG_TITLE = "#e94560"
BTN_BG = "#e94560"
BTN_ACTIVE = "#c73652"
FONT_FAMILY      = "Meiryo UI"
HIGHLIGHT_BORDER = "#ffd700"   # 役構成アイドルの枠色（金）

# 属性名→枠色（アイドル牌・属性牌共通）
ATTR_COLORS = {
    "Princess": "#ff69b4",
    "Fairy":    "#64b5f6",
    "Angel":    "#ffd54f",
}

# ID→枠色（個別特別色）
SPECIAL_BORDER = {
    53: "#4caf50",  # 青羽美咲 → 緑
}

# __file__ = スクリプト自身のパス。同フォルダのCSVを指定
CSV_PATH   = os.path.join(os.path.dirname(__file__), "idols.csv")
UNITS_PATH = os.path.join(os.path.dirname(__file__), "units.csv")

# 属性牌データ。各要素は (ID, 内部名, 表示名, 属性) のタプル
ATTRIBUTE_TILES = [
    (101, "Princess", "Princess", "Princess"),
    (102, "Fairy",    "Fairy",    "Fairy"),
    (103, "Angel",    "Angel",    "Angel"),
]


# @dataclass: __init__ 自動生成
# 普通のクラスの frame=frame, label=label 定型コードが不要
@dataclass
class CardWidget:
    frame: tk.Frame
    label: tk.Label


def load_idols():
    """CSVからアイドルデータを読み込んで返す"""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"アイドルデータなし: {CSV_PATH}")
    idols = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.reader(f):
            # 3列以上かつ1列目が空でない行のみ処理
            if len(row) >= 3 and row[0].strip():
                try:
                    # (ID, 内部名, 表示名, 属性) タプルで追加
                    idols.append((int(row[0]), row[1], row[2], row[3] if len(row) >= 4 else ""))
                except ValueError:
                    # IDが数値でない行はスキップ
                    continue
    return idols


def load_units():
    """units.csvからユニット定義を読み込む。{ユニット名: frozenset(ID)} を返す"""
    if not os.path.exists(UNITS_PATH):
        return {}
    units = {}
    with open(UNITS_PATH, encoding="utf-8") as f:
        for row in csv.reader(f):
            # コメント行・空行をスキップ
            if not row or row[0].startswith("#") or not row[0].strip():
                continue
            try:
                name = row[0].strip()
                members = frozenset(int(x) for x in row[1:] if x.strip())
                if members:
                    units[name] = members
            except ValueError:
                continue
    return units


def check_tenpai(hand, units):
    """1枚欠けユニットを返す。{unit_name: missing_id} 辞書"""
    hand_ids = {tile[0] for tile in hand}
    return {
        name: next(iter(members - hand_ids))
        for name, members in units.items()
        if len(members - hand_ids) == 1
    }


def get_contributing_ids(hand, units):
    """完成またはテンパイのユニットに属するIDセットを返す"""
    hand_ids = {tile[0] for tile in hand}
    result = set()
    for members in units.values():
        if len(members - hand_ids) <= 1:
            result |= (members & hand_ids)
    return result


def check_yaku(hand, units):
    """手牌に含まれるIDセットとユニット定義を照合し、成立ユニット名リストを返す"""
    hand_ids = {tile[0] for tile in hand}
    return [name for name, members in units.items() if members <= hand_ids]


def draw_hand(deck, n=13):
    """デッキからn枚ランダム抽出、ID順ソートして返す"""
    if len(deck) < n:
        raise ValueError(f"デッキ枚数({len(deck)})が手牌枚数({n})未満")
    # sample: 元リストを変えずn個ランダム選択
    hand = random.sample(deck, n)
    # lambda: 1行無名関数。x[0](=ID)基準でソート
    hand.sort(key=lambda x: x[0])
    return hand


# tk.Tk継承でメインウィンドウを構築
class App(tk.Tk):
    def __init__(self):
        # super().__init__(): tk.Tk の初期化を呼ぶ
        # 省略するとウィンドウが正しく生成されない
        super().__init__()
        self.title("ミリオンマージャン")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        idols = load_idols()
        # 53種×3枚＋属性牌3枚=162枚のデッキ
        self._deck = idols * 3 + ATTRIBUTE_TILES
        self._units = load_units()
        self._hand12 = None  # フェーズ管理（None = 未ドロー or 13枚目済み）
        self._id_to_name = {tile[0]: tile[2] for tile in self._deck}
        self._build_ui()

    def _build_ui(self):
        """UIウィジェット配置"""
        tk.Label(
            self,
            text="ミリオンマージャン",
            font=(FONT_FAMILY, 28, "bold"),
            bg=BG_MAIN,
            fg=FG_TITLE,
        ).pack(pady=(20, 4))

        tk.Label(
            self,
            text="53種×3枚+属性牌3枚のデッキから13枚ドロー",
            font=(FONT_FAMILY, 14),
            bg=BG_MAIN,
            fg="#8888aa",
        ).pack(pady=(0, 12))

        # 13枚横並びのコンテナ
        self.tile_frame = tk.Frame(self, bg=BG_MAIN)
        self.tile_frame.pack(padx=24, pady=4)

        self.cards = []
        for i in range(13):
            # 各カードの枠。width/height で固定サイズ
            frame = tk.Frame(
                self.tile_frame,
                bg=BG_CARD_EMPTY,
                highlightbackground=BG_CARD_EMPTY,
                highlightthickness=2,
                relief="flat",
                bd=0,
                width=112,
                height=200,
            )
            # 13枚目はcolumn 13に配置（column 12を隙間にする）
            col = i if i < 12 else 13
            # grid: 格子配置。row=0, column=col で横1列
            frame.grid(row=0, column=col, padx=5, pady=4)
            # pack_propagate(False): 子ウィジェットのサイズに枠が追従しないよう固定
            # ないと width/height が無視される
            frame.pack_propagate(False)

            label = tk.Label(frame, text="", font=(FONT_FAMILY, 14),
                             bg=BG_CARD_EMPTY, fg=FG_NAME, wraplength=100)
            # expand=True: 親フレーム内で中央配置
            label.pack(expand=True)

            self.cards.append(CardWidget(frame=frame, label=label))

        # column 12を1枚分の隙間として確保
        self.tile_frame.columnconfigure(12, minsize=122)

        self.yaku_label = tk.Label(
            self,
            text="役: ―",
            font=(FONT_FAMILY, 12),
            bg=BG_MAIN,
            fg="#8888aa",
        )
        self.yaku_label.pack(pady=(4, 0))

        self.tenpai_label = tk.Label(
            self,
            text="テンパイ: ―",
            font=(FONT_FAMILY, 12),
            bg=BG_MAIN,
            fg="#8888aa",
        )
        self.tenpai_label.pack(pady=(2, 0))

        # command=self._draw: ボタン押下で _draw を呼ぶ
        self._draw_btn = tk.Button(
            self,
            text="  ドロー  ",
            font=(FONT_FAMILY, 20, "bold"),
            bg=BTN_BG,
            fg="white",
            activebackground=BTN_ACTIVE,
            activeforeground="white",
            relief="flat",
            padx=24,
            pady=8,
            cursor="hand2",
            command=self._draw,
        )
        self._draw_btn.pack(pady=(16, 24))

    def _draw(self):
        """ドローボタン押下: フェーズに応じて12枚 or 13枚目を引く"""
        if self._hand12 is None:
            self._draw_12()
        else:
            self._draw_13()

    def _draw_12(self):
        """デッキから12枚ドロー。役構成アイドルを金枠・左寄せで表示"""
        hand12 = random.sample(self._deck, 12)
        contributing = get_contributing_ids(hand12, self._units)
        # 役構成を左に、それぞれID順ソート
        hand12.sort(key=lambda x: (0 if x[0] in contributing else 1, x[0]))
        self._hand12 = hand12

        for card, (tile_id, _, display_name, attribute) in zip(self.cards[:12], hand12):
            border = SPECIAL_BORDER.get(tile_id) or ATTR_COLORS.get(attribute, BG_CARD)
            if tile_id in contributing:
                hbg, ht = HIGHLIGHT_BORDER, 4
            else:
                hbg, ht = border, 2
            card.frame.configure(bg=BG_CARD, highlightbackground=hbg, highlightthickness=ht)
            card.label.configure(text=display_name, bg=BG_CARD)

        # 13枚目スロットをクリア
        c13 = self.cards[12]
        c13.frame.configure(bg=BG_CARD_EMPTY, highlightbackground=BG_CARD_EMPTY, highlightthickness=2)
        c13.label.configure(text="", bg=BG_CARD_EMPTY)

        yaku = check_yaku(hand12, self._units)
        tenpai = check_tenpai(hand12, self._units)
        self.yaku_label.configure(
            text="役: " + " / ".join(yaku) if yaku else "役: なし",
            fg=FG_TITLE if yaku else "#8888aa",
        )
        tenpai_texts = [
            f"{n}（あと{self._id_to_name.get(mid, str(mid))}）"
            for n, mid in tenpai.items()
        ]
        self.tenpai_label.configure(
            text="テンパイ: " + " / ".join(tenpai_texts) if tenpai_texts else "テンパイ: なし",
            fg="#ffa500" if tenpai_texts else "#8888aa",
        )
        self._draw_btn.configure(text="  13枚目を引く  ")

    def _draw_13(self):
        """残りデッキから1枚ドロー。役の完成状況を区別して表示"""
        remaining = list(self._deck)
        for tile in self._hand12:
            remaining.remove(tile)
        card13 = random.choice(remaining)

        tile_id, _, display_name, attribute = card13
        border = SPECIAL_BORDER.get(tile_id) or ATTR_COLORS.get(attribute, BG_CARD)
        c13 = self.cards[12]
        c13.frame.configure(bg=BG_CARD, highlightbackground=border, highlightthickness=2)
        c13.label.configure(text=display_name, bg=BG_CARD)

        yaku_12  = check_yaku(self._hand12, self._units)
        full     = self._hand12 + [card13]
        yaku_all = check_yaku(full, self._units)
        by_13    = [y for y in yaku_all if y not in yaku_12]
        tenpai   = check_tenpai(full, self._units)

        parts = []
        if yaku_12: parts.append("役(12枚): " + " / ".join(yaku_12))
        if by_13:   parts.append("13枚目で完成: " + " / ".join(by_13))
        self.yaku_label.configure(
            text=" | ".join(parts) if parts else "役: なし",
            fg=FG_TITLE if parts else "#8888aa",
        )
        tenpai_texts = [
            f"{n}（あと{self._id_to_name.get(mid, str(mid))}）"
            for n, mid in tenpai.items()
        ]
        self.tenpai_label.configure(
            text="惜しい: " + " / ".join(tenpai_texts) if tenpai_texts else "テンパイ: なし",
            fg="#ffa500" if tenpai_texts else "#8888aa",
        )
        self._hand12 = None
        self._draw_btn.configure(text="  ドロー  ")


# __name__ == "__main__": 直接実行時のみ True
# import 時は実行されない
if __name__ == "__main__":
    # mainloop(): ウィンドウ表示・操作待機ループ
    App().mainloop()
