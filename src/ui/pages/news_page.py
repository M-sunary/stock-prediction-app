"""
新闻情感页面 - 情感概览 + 新闻列表
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QComboBox, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..styles.theme import (
    C_SURFACE, C_BORDER, C_RED, C_GREEN, C_GOLD, C_BLUE,
    C_TEXT, C_TEXT2, C_TEXT3
)
from ...core.config_manager import get_config
from ...data.demo_data import get_stock_params
from ...features.sentiment_analyzer import get_sentiment_analyzer


class SentimentMeter(QFrame):
    """综合情感得分仪（横向颜色条 + 数值）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            QFrame#card {{
                background:{C_SURFACE};
                border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(20)

        # 左：标签
        left = QVBoxLayout()
        left.setSpacing(4)
        title_lbl = QLabel('SENTIMENT SCORE · 综合情感得分')
        title_lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; background:transparent;')
        self._score_lbl = QLabel('0.00')
        self._score_lbl.setFont(QFont('Menlo', 26, QFont.Bold))
        self._score_lbl.setStyleSheet(f'color:{C_TEXT}; background:transparent;')
        left.addWidget(title_lbl)
        left.addWidget(self._score_lbl)

        # 右：三色分布条 + 标签
        right = QVBoxLayout()
        right.setSpacing(6)

        # 牛熊中性计数行
        count_row = QHBoxLayout()
        self._bull_lbl = QLabel('多头 0')
        self._bull_lbl.setStyleSheet(f'color:{C_GREEN}; font-size:12px; background:transparent;')
        self._neut_lbl = QLabel('中性 0')
        self._neut_lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:12px; background:transparent;')
        self._bear_lbl = QLabel('空头 0')
        self._bear_lbl.setStyleSheet(f'color:{C_RED}; font-size:12px; background:transparent;')
        count_row.addWidget(self._bull_lbl)
        count_row.addStretch()
        count_row.addWidget(self._neut_lbl)
        count_row.addStretch()
        count_row.addWidget(self._bear_lbl)

        # 分布条（3段彩色）
        self._bar_frame = QFrame()
        self._bar_frame.setFixedHeight(8)
        self._bar_frame.setStyleSheet(f'background:{C_BORDER}; border-radius:4px;')
        bar_row = QHBoxLayout(self._bar_frame)
        bar_row.setContentsMargins(0, 0, 0, 0)
        bar_row.setSpacing(0)
        self._bull_seg = QFrame()
        self._bull_seg.setFixedHeight(8)
        self._bull_seg.setStyleSheet(f'background:{C_GREEN}; border-radius:4px 0 0 4px;')
        self._neut_seg = QFrame()
        self._neut_seg.setFixedHeight(8)
        self._neut_seg.setStyleSheet(f'background:{C_GOLD};')
        self._bear_seg = QFrame()
        self._bear_seg.setFixedHeight(8)
        self._bear_seg.setStyleSheet(f'background:{C_RED}; border-radius:0 4px 4px 0;')
        bar_row.addWidget(self._bull_seg, 1)
        bar_row.addWidget(self._neut_seg, 1)
        bar_row.addWidget(self._bear_seg, 1)

        right.addLayout(count_row)
        right.addWidget(self._bar_frame)

        layout.addLayout(left, 1)
        layout.addLayout(right, 2)

    def update_data(self, news_list: list, score: float):
        bull = sum(1 for n in news_list if n.get('tag') == 'bull')
        neut = sum(1 for n in news_list if n.get('tag') == 'neut')
        bear = sum(1 for n in news_list if n.get('tag') == 'bear')
        total = max(bull + neut + bear, 1)

        color = C_GREEN if score > 0.2 else (C_RED if score < -0.2 else C_GOLD)
        self._score_lbl.setText(f'{score:+.2f}')
        self._score_lbl.setStyleSheet(f'color:{color}; font-family:Menlo; font-size:26px; font-weight:700; background:transparent;')

        self._bull_lbl.setText(f'多头 {bull}')
        self._neut_lbl.setText(f'中性 {neut}')
        self._bear_lbl.setText(f'空头 {bear}')

        self._bull_seg.setFixedWidth(0)
        self._neut_seg.setFixedWidth(0)
        self._bear_seg.setFixedWidth(0)
        # Use stretch ratios
        self._bull_seg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._neut_seg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._bear_seg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        bar_layout = self._bar_frame.layout()
        bar_layout.setStretch(0, max(bull, 1) if bull else 0)
        bar_layout.setStretch(1, max(neut, 1) if neut else 0)
        bar_layout.setStretch(2, max(bear, 1) if bear else 0)


class NewsCard(QFrame):
    """单条新闻卡片"""

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        tag = item.get('tag', 'neut')
        sentiment = item.get('sentiment', 0.0)

        if tag == 'bull':
            border_color = C_GREEN
            badge_bg = '#20c98428'
            badge_fg = C_GREEN
            badge_text = '多头'
        elif tag == 'bear':
            border_color = C_RED
            badge_bg = '#f03e3e28'
            badge_fg = C_RED
            badge_text = '空头'
        else:
            border_color = C_BORDER
            badge_bg = '#ffffff15'
            badge_fg = C_TEXT3
            badge_text = '中性'

        self.setStyleSheet(f"""
            QFrame {{
                border-left: 3px solid {border_color};
                border-bottom: 1px solid {C_BORDER};
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # 标题行
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        badge = QLabel(badge_text)
        badge.setFixedSize(34, 18)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background: {badge_bg};
                color: {badge_fg};
                border-radius: 9px;
                font-size: 10px;
                font-weight: 600;
            }}
        """)

        title_lbl = QLabel(item.get('title', ''))
        title_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:13px; background:transparent;')
        title_lbl.setWordWrap(True)

        title_row.addWidget(badge)
        title_row.addWidget(title_lbl, 1)

        # 元数据行
        meta_row = QHBoxLayout()
        source_lbl = QLabel(item.get('source', ''))
        source_lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:11px; background:transparent;')
        time_lbl = QLabel(item.get('time', ''))
        time_lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:11px; font-family:Menlo; background:transparent;')
        score_color = C_GREEN if sentiment > 0 else (C_RED if sentiment < 0 else C_TEXT3)
        score_lbl = QLabel(f'情感分 {sentiment:+.2f}')
        score_lbl.setStyleSheet(f'color:{score_color}; font-size:11px; font-family:Menlo; background:transparent;')

        meta_row.addWidget(source_lbl)
        meta_row.addSpacing(12)
        meta_row.addWidget(time_lbl)
        meta_row.addStretch()
        meta_row.addWidget(score_lbl)

        layout.addLayout(title_row)
        layout.addLayout(meta_row)


class NewsPage(QWidget):
    """新闻情感页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = get_config()
        self._analyzer = get_sentiment_analyzer()
        self._current_code = ''
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── 标题栏 ─────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel('新闻情感')
        title.setFont(QFont('PingFang SC', 20, QFont.Bold))
        title.setStyleSheet(f'color:{C_TEXT};')
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel('股票：'))
        self._selector = QComboBox()
        self._selector.setFixedWidth(180)
        self._selector.setStyleSheet(f"""
            QComboBox {{
                background:{C_SURFACE}; color:{C_TEXT}; border:1px solid {C_BORDER};
                border-radius:6px; padding:4px 8px; font-size:13px;
            }}
            QComboBox::drop-down {{ border:none; }}
            QComboBox QAbstractItemView {{ background:{C_SURFACE}; color:{C_TEXT}; selection-background-color:{C_RED}33; }}
        """)
        self._selector.currentIndexChanged.connect(self._on_selector_changed)
        header.addWidget(self._selector)
        layout.addLayout(header)

        # ── 情感得分仪 ────────────────────────────────────────────────────
        self._meter = SentimentMeter()
        layout.addWidget(self._meter)

        # ── 新闻列表（可滚动）────────────────────────────────────────────
        news_card = QFrame()
        news_card.setObjectName('card')
        news_card.setStyleSheet(f"""
            QFrame#card {{
                background:{C_SURFACE};
                border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)
        news_outer = QVBoxLayout(news_card)
        news_outer.setContentsMargins(0, 12, 0, 0)
        news_outer.setSpacing(0)

        news_hdr = QLabel('NEWS FEED · 最新资讯')
        news_hdr.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; padding:0 16px 8px 16px;')
        news_outer.addWidget(news_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background:transparent; border:none; }')
        self._news_content = QWidget()
        self._news_content.setStyleSheet('background:transparent;')
        self._news_layout = QVBoxLayout(self._news_content)
        self._news_layout.setContentsMargins(0, 0, 0, 0)
        self._news_layout.setSpacing(0)
        self._news_layout.addStretch()
        scroll.setWidget(self._news_content)
        news_outer.addWidget(scroll)

        layout.addWidget(news_card, 1)
        self._refresh_selector()

    def _refresh_selector(self):
        self._selector.blockSignals(True)
        prev = self._current_code
        self._selector.clear()
        for code in self._config.watchlist:
            params = get_stock_params(code)
            name = params.get('name', code) if params.get('name') != code else code
            self._selector.addItem(f'{code}  {name}', code)
        for i in range(self._selector.count()):
            if self._selector.itemData(i) == prev:
                self._selector.setCurrentIndex(i)
                break
        self._selector.blockSignals(False)

    def _on_selector_changed(self):
        code = self._selector.currentData()
        if code:
            self.load_stock(code)

    def load_stock(self, code: str, name: str = '', news_list: list = None):
        self._current_code = code
        self._refresh_selector()
        for i in range(self._selector.count()):
            if self._selector.itemData(i) == code:
                self._selector.blockSignals(True)
                self._selector.setCurrentIndex(i)
                self._selector.blockSignals(False)
                break

        if not name:
            params = get_stock_params(code)
            name = params.get('name', code)

        if news_list is None:
            news_list = self._analyzer.get_news_with_sentiment(code, name)

        score = self._analyzer.aggregate_score([n.get('sentiment', 0.0) for n in news_list])
        self._meter.update_data(news_list, score)
        self._rebuild_news(news_list)

    def _rebuild_news(self, news_list: list):
        # 清除旧条目（保留末尾 stretch）
        while self._news_layout.count() > 1:
            item = self._news_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in news_list:
            card = NewsCard(item)
            self._news_layout.insertWidget(self._news_layout.count() - 1, card)
