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
TENPAI_BORDER    = "#ffa500"   # テンパイ時の枠色（オレンジ）

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


def assign_yaku_tenpai_indices(hand, units):
    """インスタンス別に役/テンパイを割り当て。重複コピー考慮。

    Returns:
        yaku_idx: set[int]       - 役タイルのhand内インデックス
        tenpai_idx: set[int]     - テンパイタイルのhand内インデックス
        yaku_unit_map: dict      - インデックス→ユニット番号（ソート用）
        completed: list[str]     - 完成ユニット名リスト
        tenpai: dict[str, int]   - テンパイユニット名→不足ID
    """
    # ID → hand内インデックスリスト
    id_map = {}
    for i, tile in enumerate(hand):
        id_map.setdefault(tile[0], []).append(i)

    # 未割り当てコピーの追跡
    remaining = {tid: list(idxs) for tid, idxs in id_map.items()}

    yaku_idx = set()
    tenpai_idx = set()
    yaku_unit_map = {}
    completed = []
    tenpai = {}

    # 完成ユニット処理（全メンバーに残コピーあり）
    for unit_order, (name, members) in enumerate(units.items()):
        if all(remaining.get(mid) for mid in members):
            for mid in members:
                idx = remaining[mid].pop(0)
                yaku_idx.add(idx)
                yaku_unit_map[idx] = unit_order
            completed.append(name)

    # テンパイ処理（ちょうど1メンバーが手牌に不在、残コピーで他は賄える）
    for name, members in units.items():
        absent = [mid for mid in members if not id_map.get(mid)]
        present_ids = [mid for mid in members if id_map.get(mid)]
        if len(absent) == 1 and all(remaining.get(mid) for mid in present_ids):
            tenpai[name] = absent[0]
            for mid in present_ids:
                tenpai_idx.add(remaining[mid].pop(0))

    return yaku_idx, tenpai_idx, yaku_unit_map, completed, tenpai


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
        self.update_idletasks()
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}")

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
            # expand=True: 親フレーム内で中央配置。padx/pady で frame.bg が帯として見える
            label.pack(expand=True, padx=4, pady=4)

            self.cards.append(CardWidget(frame=frame, label=label))

        # column 12を1枚分の隙間として確保
        self.tile_frame.columnconfigure(12, minsize=122)

        self.yaku_label = tk.Label(
            self,
            text="役: ―",
            font=(FONT_FAMILY, 12),
            bg=BG_MAIN,
            fg="#8888aa",
            anchor="w",
            wraplength=1650,
        )
        self.yaku_label.pack(pady=(4, 0), fill="x", padx=24)

        self.tenpai_label = tk.Label(
            self,
            text="テンパイ: ―",
            font=(FONT_FAMILY, 12),
            bg=BG_MAIN,
            fg="#8888aa",
            anchor="w",
            wraplength=1650,
        )
        self.tenpai_label.pack(pady=(2, 0), fill="x", padx=24)

        _btn_frame = tk.Frame(self, bg=BG_MAIN)
        _btn_frame.pack(pady=(16, 24))

        _btn_opts = dict(
            font=(FONT_FAMILY, 20, "bold"),
            bg=BTN_BG,
            fg="white",
            activebackground=BTN_ACTIVE,
            activeforeground="white",
            relief="flat",
            padx=24,
            pady=8,
            cursor="hand2",
        )
        self._draw12_btn = tk.Button(
            _btn_frame, text="  ドロー  ", command=self._draw_12, **_btn_opts
        )
        self._draw12_btn.pack(side=tk.LEFT, padx=8)

        self._draw13_btn = tk.Button(
            _btn_frame, text="  13枚目を引く  ", command=self._draw_13,
            **_btn_opts
        )
        self._draw13_btn.pack(side=tk.LEFT, padx=8)

    def _apply_card_style(self, card, tile_id, attribute, is_yaku=False, is_tenpai=False):
        """カード枠スタイルを適用（役=金帯、テンパイ=橙細枠、通常=属性細枠）"""
        attr_color = SPECIAL_BORDER.get(tile_id) or ATTR_COLORS.get(attribute, BG_CARD)
        if is_yaku:
            card.frame.configure(bg=HIGHLIGHT_BORDER, highlightbackground=HIGHLIGHT_BORDER, highlightthickness=5)
            card.label.configure(bg=BG_MAIN)
        elif is_tenpai:
            card.frame.configure(bg=attr_color, highlightbackground=TENPAI_BORDER, highlightthickness=2)
            card.label.configure(bg=BG_CARD)
        else:
            card.frame.configure(bg=BG_CARD, highlightbackground=attr_color, highlightthickness=2)
            card.label.configure(bg=BG_CARD)

    def _draw_12(self):
        """デッキから12枚ドロー。役・テンパイ・属性を枠色で表示"""
        hand12 = random.sample(self._deck, 12)
        yaku_idx, tenpai_idx, yaku_unit_map, yaku_names, tenpai_names = \
            assign_yaku_tenpai_indices(hand12, self._units)

        # 役グループ左寄せ・テンパイは非左寄せ
        sorted_pos = sorted(range(len(hand12)), key=lambda i: (
            (0, yaku_unit_map.get(i, 0), hand12[i][0]) if i in yaku_idx
            else (1, 0, hand12[i][0])
        ))
        pos_map = {old: new for new, old in enumerate(sorted_pos)}
        hand12 = [hand12[i] for i in sorted_pos]
        yaku_idx = {pos_map[i] for i in yaku_idx}
        tenpai_idx = {pos_map[i] for i in tenpai_idx}

        self._hand12 = hand12

        for i, (card, (tile_id, _, display_name, attribute)) in enumerate(zip(self.cards[:12], hand12)):
            card.label.configure(text=display_name)
            self._apply_card_style(card, tile_id, attribute,
                                   is_yaku=i in yaku_idx,
                                   is_tenpai=i in tenpai_idx)

        # 13枚目スロットをクリア
        c13 = self.cards[12]
        c13.frame.configure(bg=BG_CARD_EMPTY, highlightbackground=BG_CARD_EMPTY, highlightthickness=2)
        c13.label.configure(text="", bg=BG_CARD_EMPTY)

        self.yaku_label.configure(
            text="役: " + " / ".join(yaku_names) if yaku_names else "役: なし",
            fg=FG_TITLE if yaku_names else "#8888aa",
        )
        tenpai_texts = [
            f"{n}（あと{self._id_to_name.get(mid, str(mid))}）"
            for n, mid in tenpai_names.items()
        ]
        self.tenpai_label.configure(
            text="テンパイ: " + " / ".join(tenpai_texts) if tenpai_texts else "テンパイ: なし",
            fg="#ffa500" if tenpai_texts else "#8888aa",
        )

    def _draw_13(self):
        """残りデッキから1枚ドロー。hand12がなければ先に12枚を自動ドロー。"""
        if self._hand12 is None:
            hand12 = random.sample(self._deck, 12)
            yaku_idx_12, tenpai_idx_12, yaku_unit_map_12, _, _ = \
                assign_yaku_tenpai_indices(hand12, self._units)
            sorted_pos = sorted(range(len(hand12)), key=lambda i: (
                (0, yaku_unit_map_12.get(i, 0), hand12[i][0]) if i in yaku_idx_12
                else (1, 0, hand12[i][0])
            ))
            pos_map = {old: new for new, old in enumerate(sorted_pos)}
            hand12 = [hand12[i] for i in sorted_pos]
            yaku_idx_12 = {pos_map[i] for i in yaku_idx_12}
            tenpai_idx_12 = {pos_map[i] for i in tenpai_idx_12}
            self._hand12 = hand12
            for i, (card, (tile_id, _, display_name, attribute)) in enumerate(
                    zip(self.cards[:12], hand12)):
                card.label.configure(text=display_name)
                self._apply_card_style(card, tile_id, attribute,
                                       is_yaku=i in yaku_idx_12,
                                       is_tenpai=i in tenpai_idx_12)

        remaining = list(self._deck)
        for tile in self._hand12:
            remaining.remove(tile)
        card13 = random.choice(remaining)

        full = self._hand12 + [card13]
        yaku_idx, tenpai_idx, _, yaku_all, tenpai_all = \
            assign_yaku_tenpai_indices(full, self._units)

        # 12枚を再スタイル適用
        for i, (card, (tile_id, _, display_name, attribute)) in enumerate(
                zip(self.cards[:12], self._hand12)):
            self._apply_card_style(card, tile_id, attribute,
                                   is_yaku=i in yaku_idx,
                                   is_tenpai=i in tenpai_idx)

        # 13枚目スタイル適用
        tile_id, _, display_name, attribute = card13
        c13 = self.cards[12]
        c13.label.configure(text=display_name)
        self._apply_card_style(c13, tile_id, attribute,
                               is_yaku=12 in yaku_idx,
                               is_tenpai=12 in tenpai_idx)

        _, _, _, yaku_12, _ = assign_yaku_tenpai_indices(self._hand12, self._units)
        by_13 = [y for y in yaku_all if y not in yaku_12]

        parts = []
        if yaku_12: parts.append("役(12枚): " + " / ".join(yaku_12))
        if by_13:   parts.append("13枚目で完成: " + " / ".join(by_13))
        self.yaku_label.configure(
            text=" | ".join(parts) if parts else "役: なし",
            fg=FG_TITLE if parts else "#8888aa",
        )
        tenpai_texts = [
            f"{n}（あと{self._id_to_name.get(mid, str(mid))}）"
            for n, mid in tenpai_all.items()
        ]
        self.tenpai_label.configure(
            text="惜しい: " + " / ".join(tenpai_texts) if tenpai_texts else "テンパイ: なし",
            fg="#ffa500" if tenpai_texts else "#8888aa",
        )
        self._hand12 = None


# __name__ == "__main__": 直接実行時のみ True
# import 時は実行されない
if __name__ == "__main__":
    # mainloop(): ウィンドウ表示・操作待機ループ
    App().mainloop()
