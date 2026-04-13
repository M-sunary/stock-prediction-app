"""
左侧边栏 - 今日高概率股票列表 + 板块概况
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QAbstractScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ..styles.theme import (
    C_SURFACE, C_SURFACE2, C_BORDER2, C_BORDER,
    C_RED, C_RED_GLOW, C_GREEN, C_GOLD,
    C_TEXT, C_TEXT2, C_TEXT3
)
from ...core.config_manager import get_config
from ...data.demo_data import get_stock_params
from ...data.cache_manager import get_cache


class StockListItem(QWidget):
    """单个股票条目（用 QWidget，避免 QFrame QSS 继承问题）"""
    clicked = pyqtSignal(str, str, float)

    def __init__(self, code: str, name: str, prob: float, parent=None):
        super().__init__(parent)
        self.code = code
        self.name = name
        self.prob = prob
        self._active = False
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self._init_ui(code, name, prob)
        self._apply_style()

    def _init_ui(self, code, name, prob):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)

        code_lbl = QLabel(code)
        code_lbl.setFont(QFont('Menlo', 11))
        code_lbl.setFixedWidth(52)
        code_lbl.setStyleSheet(f'color:{C_TEXT2}; background:transparent;')

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:13px; background:transparent;')

        # 概率徽章
        if prob >= 65:
            badge_bg, badge_fg = f'{C_GREEN}28', C_GREEN
        elif prob >= 50:
            badge_bg, badge_fg = f'{C_GOLD}28', C_GOLD
        else:
            badge_bg, badge_fg = f'{C_RED}28', C_RED

        prob_lbl = QLabel(f'{prob:.0f}%')
        prob_lbl.setFont(QFont('Menlo', 11, QFont.Bold))
        prob_lbl.setFixedSize(40, 20)
        prob_lbl.setAlignment(Qt.AlignCenter)
        prob_lbl.setStyleSheet(f'background:{badge_bg}; color:{badge_fg}; border-radius:10px;')

        layout.addWidget(code_lbl)
        layout.addWidget(name_lbl, 1)
        layout.addWidget(prob_lbl)

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QWidget {{
                    background: {C_RED_GLOW};
                    border-left: 2px solid {C_RED};
                    border-radius: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QWidget {{
                    background: transparent;
                    border: none;
                    border-radius: 6px;
                }}
                QWidget:hover {{
                    background: rgba(255,255,255,30);
                }}
            """)

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.code, self.name, self.prob)
        super().mousePressEvent(event)


class SectorRow(QWidget):
    def __init__(self, name: str, pct: float, hot: bool, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet('background:transparent;')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)

        dot = QLabel('●' if hot else '○')
        dot.setFixedWidth(10)
        dot.setStyleSheet(f'color:{C_RED}; font-size:7px; background:transparent;' if hot
                          else f'color:{C_TEXT3}; font-size:7px; background:transparent;')

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f'color:{C_TEXT2}; font-size:12px; background:transparent;')

        sign = '+' if pct >= 0 else ''
        color = C_RED if pct >= 0 else C_GREEN
        pct_lbl = QLabel(f'{sign}{pct:.2f}%')
        pct_lbl.setFont(QFont('Menlo', 11))
        pct_lbl.setStyleSheet(f'color:{color}; background:transparent;')
        pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(dot)
        layout.addWidget(name_lbl, 1)
        layout.addWidget(pct_lbl)


class SectionLabel(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(f'background:transparent; border-bottom:1px solid {C_BORDER};')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; background:transparent;')
        layout.addWidget(lbl)


class Sidebar(QWidget):
    stock_selected = pyqtSignal(str, str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._stock_items = []
        self._current_code = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"""
            QWidget#sidebar_root {{
                background: {C_SURFACE};
                border-right: 1px solid {C_BORDER2};
            }}
        """)
        self.setObjectName('sidebar_root')

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # 明确设置 viewport 和 scroll 背景
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: {C_SURFACE}; border: none; }}
            QScrollArea > QWidget {{ background: {C_SURFACE}; }}
        """)
        scroll.viewport().setStyleSheet(f'background: {C_SURFACE};')

        content = QWidget()
        content.setStyleSheet(f'background: {C_SURFACE};')
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(4, 8, 4, 8)
        self._content_layout.setSpacing(0)

        # 今日高概率 section
        self._content_layout.addWidget(SectionLabel('今日高概率'))
        self._stock_container = QVBoxLayout()
        self._stock_container.setSpacing(1)
        self._content_layout.addLayout(self._stock_container)

        self._content_layout.addSpacing(12)

        # 板块概况 section
        self._content_layout.addWidget(SectionLabel('板块概况'))
        self._sector_container = QVBoxLayout()
        self._sector_container.setSpacing(0)
        self._content_layout.addLayout(self._sector_container)
        self._content_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

        # 加载默认数据
        self._load_defaults()

    def _load_defaults(self):
        config = get_config()
        cache = get_cache()
        stocks = []
        for code in config.watchlist:
            # 名称：缓存优先，其次 demo 参数
            name = code
            cached_info = cache.get(f"info_{code}", max_age_hours=24 * 7)
            if cached_info and cached_info.get('name') and cached_info['name'] != code:
                name = cached_info['name']
            else:
                params = get_stock_params(code)
                if params.get('name') and params['name'] != code:
                    name = params['name']

            # 概率：最近一次预测历史，无则默认 50
            history = cache.get_prediction_history(code, limit=1)
            prob = history[0]['probability'] if history else 50.0
            stocks.append((code, name, prob))

        self.update_stock_list(stocks)

        self.update_sector_list([
            ('银行', 1.82, True), ('白酒', 0.94, True),
            ('新能源', -0.62, False), ('医药', 0.31, False),
            ('科技', 1.12, True), ('地产', -1.43, False),
        ])

    def update_stock_list(self, stocks: list):
        # 清除旧 widget
        while self._stock_container.count():
            item = self._stock_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._stock_items.clear()

        for code, name, prob in sorted(stocks, key=lambda x: x[2], reverse=True):
            item = StockListItem(code, name, prob)
            item.clicked.connect(self._on_item_click)
            self._stock_container.addWidget(item)
            self._stock_items.append(item)

        # 默认激活第一个
        if self._stock_items and self._current_code is None:
            self._stock_items[0].set_active(True)
            self._current_code = self._stock_items[0].code

    def update_sector_list(self, sectors: list):
        while self._sector_container.count():
            item = self._sector_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for name, pct, hot in sectors:
            self._sector_container.addWidget(SectorRow(name, pct, hot))

    def _on_item_click(self, code: str, name: str, prob: float):
        for item in self._stock_items:
            item.set_active(item.code == code)
        self._current_code = code
        self.stock_selected.emit(code, name, prob)

    def filter_stocks(self, keyword: str):
        """按关键词过滤，无匹配时显示全部"""
        keyword = keyword.strip().lower()
        if not keyword:
            for item in self._stock_items:
                item.setVisible(True)
            return
        matched = [
            item for item in self._stock_items
            if keyword in item.code.lower() or keyword in item.name
        ]
        # 如果没有匹配则不隐藏全部（避免侧边栏全空）
        if matched:
            for item in self._stock_items:
                item.setVisible(item in matched)
        else:
            for item in self._stock_items:
                item.setVisible(True)
