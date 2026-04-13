"""
技术指标面板 + 情感分析面板
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ..styles.theme import (
    C_SURFACE, C_BORDER, C_RED, C_GREEN, C_GOLD, C_BLUE,
    C_TEXT, C_TEXT2, C_TEXT3, C_SURFACE2, C_BORDER2
)


def _color_for(color_key: str) -> str:
    return {'green': C_GREEN, 'red': C_RED, 'gold': C_GOLD, 'blue': C_BLUE}.get(color_key, C_TEXT2)


class IndicatorRow(QFrame):
    def __init__(self, name: str, value: str, signal: str, color: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        name_lbl = QLabel(name)
        name_lbl.setFixedWidth(70)
        name_lbl.setStyleSheet(f'color:{C_TEXT2}; font-size:12px;')

        val_lbl = QLabel(value)
        val_lbl.setFont(QFont('Menlo', 11))
        val_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:11px;')

        c = _color_for(color)
        sig_lbl = QLabel(signal)
        sig_lbl.setFixedSize(48, 18)
        sig_lbl.setAlignment(Qt.AlignCenter)
        sig_lbl.setStyleSheet(f"""
            QLabel {{
                background: {c}22;
                color: {c};
                border-radius: 9px;
                font-size: 10px;
                font-weight: 600;
            }}
        """)

        layout.addWidget(name_lbl)
        layout.addWidget(val_lbl)
        layout.addStretch()
        layout.addWidget(sig_lbl)

        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-bottom: 1px solid {C_BORDER};
            }}
            QFrame:hover {{
                background: rgba(255,255,255,0.03);
            }}
        """)


class TechIndicatorPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(0)

        # 标题
        header = QLabel('TECH INDICATORS · 技术指标')
        header.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; padding:0 16px 8px 16px;')
        layout.addWidget(header)

        self._rows_container = QVBoxLayout()
        self._rows_container.setSpacing(0)
        layout.addLayout(self._rows_container)

        # 综合评分
        self._summary = QLabel('综合技术评分 -- · --')
        self._summary.setContentsMargins(12, 8, 12, 0)
        self._summary.setFixedHeight(32)
        self._summary.setAlignment(Qt.AlignCenter)
        self._summary.setStyleSheet(f"""
            QLabel {{
                background: {C_GREEN}15;
                color: {C_GREEN};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                margin: 4px 12px;
            }}
        """)
        layout.addWidget(self._summary)

        self.setStyleSheet(f"""
            QFrame#card {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

    def update_indicators(self, indicators: list):
        while self._rows_container.count():
            item = self._rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for ind in indicators:
            row = IndicatorRow(
                ind['name'], ind['value'],
                ind['signal'], ind['color']
            )
            self._rows_container.addWidget(row)

        # 综合评分
        buy_count = sum(1 for i in indicators if i['signal'] in ('BUY', '金叉', '放量', '↑趋势'))
        total = len(indicators) or 1
        score = int(buy_count / total * 10)
        direction = '偏多' if score >= 6 else ('偏空' if score <= 4 else '中性')
        color = C_GREEN if score >= 6 else (C_RED if score <= 4 else C_GOLD)
        self._summary.setText(f'综合技术评分 {score} / 10 · {direction}')
        self._summary.setStyleSheet(f"""
            QLabel {{
                background: {color}15;
                color: {color};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                margin: 4px 12px;
            }}
        """)


class NewsItem(QFrame):
    def __init__(self, title: str, source: str, time: str,
                 sentiment: float, tag: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        # 标题
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(False)
        title_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:12px;')
        title_lbl.setMaximumWidth(380)

        # 来源行
        color = C_GREEN if sentiment > 0.3 else (C_RED if sentiment < -0.3 else C_TEXT3)
        meta = QLabel(f'{source}  ·  {time}  ·  情感 {"+":s}{sentiment:.2f}' if sentiment >= 0
                      else f'{source}  ·  {time}  ·  情感 {sentiment:.2f}')
        meta.setStyleSheet(f'color:{C_TEXT3}; font-size:11px;')

        layout.addWidget(title_lbl)
        layout.addWidget(meta)

        border_color = color
        self.setStyleSheet(f"""
            QFrame {{
                border-left: 2px solid {border_color};
                background: transparent;
                padding-left: 8px;
            }}
            QFrame:hover {{
                background: rgba(255,255,255,0.03);
            }}
        """)


class SentimentPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QLabel('SENTIMENT · 市场情感')
        header.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px;')
        layout.addWidget(header)

        # 情感仪表条
        bar_widget = QWidget()
        bar_layout = QVBoxLayout(bar_widget)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(4)

        self._sentiment_bar = QProgressBar()
        self._sentiment_bar.setRange(0, 100)
        self._sentiment_bar.setValue(50)
        self._sentiment_bar.setFixedHeight(8)
        self._sentiment_bar.setTextVisible(False)
        self._sentiment_bar.setStyleSheet(f"""
            QProgressBar {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {C_RED}, stop:0.5 {C_GOLD}, stop:1 {C_GREEN});
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: transparent;
                border-right: 3px solid white;
                border-radius: 4px;
            }}
        """)
        self._sentiment_score_lbl = QLabel('情感分数：--')
        self._sentiment_score_lbl.setFont(QFont('Menlo', 13, QFont.Bold))
        self._sentiment_score_lbl.setAlignment(Qt.AlignCenter)

        bar_layout.addWidget(self._sentiment_bar)
        bar_layout.addWidget(self._sentiment_score_lbl)
        layout.addWidget(bar_widget)

        # 新闻列表
        self._news_container = QVBoxLayout()
        self._news_container.setSpacing(4)
        layout.addLayout(self._news_container)

        self.setStyleSheet(f"""
            QFrame#card {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

    def update_sentiment(self, score: float, news: list):
        # 更新仪表条（-1~+1 → 0~100）
        pct = int((score + 1) / 2 * 100)
        self._sentiment_bar.setValue(pct)

        color = C_GREEN if score > 0.3 else (C_RED if score < -0.3 else C_GOLD)
        sign = '+' if score >= 0 else ''
        label = '偏乐观' if score > 0.3 else ('偏悲观' if score < -0.3 else '中性')
        self._sentiment_score_lbl.setText(f'{sign}{score:.2f}  {label}')
        self._sentiment_score_lbl.setStyleSheet(f'color:{color}; font-size:13px; font-weight:600;')

        # 更新新闻列表
        while self._news_container.count():
            item = self._news_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for n in news[:4]:
            item = NewsItem(
                n.get('title', ''), n.get('source', ''),
                n.get('time', ''), n.get('sentiment', 0), n.get('tag', 'neut')
            )
            self._news_container.addWidget(item)
