"""
顶部导航栏组件
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
from ..styles.theme import (
    C_BG, C_SURFACE, C_BORDER2, C_RED, C_RED_GLOW,
    C_GREEN, C_GOLD, C_TEXT, C_TEXT2, C_TEXT3
)


class MarketPill(QFrame):
    """大盘指数小药丸"""
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 10, 0)
        layout.setSpacing(5)

        # 状态点
        self._dot = QLabel('●')
        self._dot.setFont(QFont('Arial', 7))
        self._dot.setFixedWidth(10)

        # 名称
        self._name_lbl = QLabel(name)
        self._name_lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:12px;')

        # 数值
        self._val_lbl = QLabel('--')
        self._val_lbl.setFont(QFont('Menlo', 12))
        self._val_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:12px;')

        # 涨跌幅
        self._chg_lbl = QLabel('+0.00%')
        self._chg_lbl.setFont(QFont('Menlo', 11))
        self._chg_lbl.setFixedWidth(60)

        layout.addWidget(self._dot)
        layout.addWidget(self._name_lbl)
        layout.addWidget(self._val_lbl)
        layout.addWidget(self._chg_lbl)

        self.setStyleSheet(f"""
            QFrame {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER2};
                border-radius: 14px;
            }}
        """)

    def update_data(self, price: float, pct_chg: float):
        self._val_lbl.setText(f'{price:,.2f}')
        sign = '+' if pct_chg >= 0 else ''
        color = C_GREEN if pct_chg >= 0 else C_RED
        self._chg_lbl.setText(f'{sign}{pct_chg:.2f}%')
        self._chg_lbl.setStyleSheet(f'color:{color}; font-size:11px; font-family:Menlo;')
        self._dot.setStyleSheet(f'color:{color}; font-size:7px;')


class TopBar(QWidget):
    search_triggered = pyqtSignal(str)
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setObjectName('topbar')
        self._init_ui()
        self._init_style()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # ── Logo ───────────────────────────────────────────────────────────
        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)

        logo_mark = QLabel('⬡')
        logo_mark.setFont(QFont('Arial', 20))
        logo_mark.setStyleSheet(f'color:{C_RED};')
        logo_mark.setFixedSize(32, 32)
        logo_mark.setAlignment(Qt.AlignCenter)

        logo_text = QLabel('量策 <b>AI</b>')
        logo_text.setFont(QFont('PingFang SC', 16, QFont.Bold))
        logo_text.setStyleSheet(f'color:{C_TEXT};')

        logo_layout.addWidget(logo_mark)
        logo_layout.addWidget(logo_text)
        logo_widget.setFixedWidth(120)

        # ── 搜索框 ─────────────────────────────────────────────────────────
        self._search = QLineEdit()
        self._search.setPlaceholderText('  ⌕  搜索股票代码或名称... 如 000001 平安银行')
        self._search.setFixedHeight(34)
        self._search.setMaximumWidth(460)
        self._search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._search.returnPressed.connect(self._on_search)

        # ── 弹性空间 ───────────────────────────────────────────────────────
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ── 大盘指数 ───────────────────────────────────────────────────────
        self._sh_pill = MarketPill('沪指')
        self._sz_pill = MarketPill('深成')

        # ── 设置按钮 ───────────────────────────────────────────────────────
        settings_btn = QPushButton('⚙  配置')
        settings_btn.setFixedHeight(30)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.clicked.connect(self.settings_clicked)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT2};
                border: 1px solid {C_BORDER2};
                border-radius: 15px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {C_TEXT};
                border-color: {C_TEXT3};
            }}
        """)

        # ── 用户头像 ───────────────────────────────────────────────────────
        avatar = QLabel('王')
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background: {C_RED};
                color: white;
                border-radius: 16px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)

        layout.addWidget(logo_widget)
        layout.addWidget(self._search)
        layout.addWidget(spacer)
        layout.addWidget(self._sh_pill)
        layout.addWidget(self._sz_pill)
        layout.addWidget(settings_btn)
        layout.addWidget(avatar)

    def _init_style(self):
        self.setStyleSheet(f"""
            QWidget#topbar {{
                background: rgba(8,9,13,0.95);
                border-bottom: 1px solid {C_BORDER2};
            }}
            QLineEdit {{
                background: rgba(22,24,32,0.8);
                color: {C_TEXT2};
                border: 1px solid {C_BORDER2};
                border-radius: 17px;
                padding: 0 16px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {C_RED};
                color: {C_TEXT};
            }}
        """)

    def _on_search(self):
        text = self._search.text().strip()
        if text:
            self.search_triggered.emit(text)

    def update_market_data(self, data: dict):
        sh = data.get('sh', {})
        sz = data.get('sz', {})
        if sh:
            self._sh_pill.update_data(sh.get('price', 0), sh.get('pct_chg', 0))
        if sz:
            self._sz_pill.update_data(sz.get('price', 0), sz.get('pct_chg', 0))
