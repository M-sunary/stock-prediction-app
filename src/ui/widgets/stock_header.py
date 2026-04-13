"""
股票标题栏 + KPI 磁贴 + 特征重要性图
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QSizePolicy, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QLinearGradient, QBrush, QPen
from ..styles.theme import (
    C_SURFACE, C_SURFACE2, C_BORDER, C_BORDER2,
    C_RED, C_RED_HOVER, C_GREEN, C_GOLD, C_BLUE,
    C_TEXT, C_TEXT2, C_TEXT3
)


class StockHeader(QWidget):
    """股票标题栏"""
    refresh_clicked = pyqtSignal()
    watchlist_clicked = pyqtSignal(str)  # code
    run_prediction_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._code = ''
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 左侧信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self._name_lbl = QLabel('--')
        self._name_lbl.setFont(QFont('PingFang SC', 22, QFont.Bold))
        self._name_lbl.setStyleSheet(f'color:{C_TEXT};')

        self._meta_lbl = QLabel('-- · -- · --')
        self._meta_lbl.setFont(QFont('Menlo', 12))
        self._meta_lbl.setStyleSheet(f'color:{C_TEXT3};')

        info_layout.addWidget(self._name_lbl)
        info_layout.addWidget(self._meta_lbl)

        # 价格区域
        price_widget = QWidget()
        price_layout = QVBoxLayout(price_widget)
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(2)

        self._price_lbl = QLabel('--')
        self._price_lbl.setFont(QFont('Menlo', 28, QFont.Bold))
        self._price_lbl.setStyleSheet(f'color:{C_RED};')

        self._change_lbl = QLabel('▲ -- (+--%) 今日')
        self._change_lbl.setFont(QFont('Menlo', 13))
        self._change_lbl.setStyleSheet(f'color:{C_GREEN};')

        price_layout.addWidget(self._price_lbl)
        price_layout.addWidget(self._change_lbl)

        # 按钮组
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        btn_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        refresh_btn = QPushButton('↺  刷新预测')
        refresh_btn.setFixedHeight(32)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_clicked)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT2};
                border: 1px solid {C_BORDER2};
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{ color:{C_TEXT}; border-color:{C_TEXT3}; }}
        """)

        self._watchlist_btn = QPushButton('+ 加入自选')
        self._watchlist_btn.setFixedHeight(32)
        self._watchlist_btn.setCursor(Qt.PointingHandCursor)
        self._watchlist_btn.clicked.connect(lambda: self.watchlist_clicked.emit(self._code))
        self._watchlist_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT2};
                border: 1px solid {C_BORDER2};
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{ color:{C_TEXT}; border-color:{C_TEXT3}; }}
        """)

        run_btn = QPushButton('▶  运行预测')
        run_btn.setObjectName('btnPrimary')
        run_btn.setFixedHeight(32)
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.clicked.connect(self.run_prediction_clicked)
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_RED};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background:{C_RED_HOVER}; }}
        """)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(self._watchlist_btn)
        btn_layout.addWidget(run_btn)

        layout.addWidget(info_widget)
        layout.addWidget(price_widget)
        layout.addStretch()
        layout.addWidget(btn_widget)

    def update_stock(self, name: str, code: str, market: str, industry: str,
                     price: float, change: float, pct_chg: float):
        self._code = code
        self._name_lbl.setText(name)
        self._meta_lbl.setText(f'{code} · {market} · {industry}')
        self._price_lbl.setText(f'{price:.2f}')
        color = C_RED if pct_chg >= 0 else C_GREEN
        arrow = '▲' if pct_chg >= 0 else '▼'
        sign = '+' if pct_chg >= 0 else ''
        self._price_lbl.setStyleSheet(f'color:{color}; font-family:Menlo; font-size:28px; font-weight:700;')
        self._change_lbl.setText(f'{arrow} {change:+.2f} ({sign}{pct_chg:.2f}%) 今日')
        self._change_lbl.setStyleSheet(f'color:{color}; font-family:Menlo; font-size:13px;')


class KPITile(QFrame):
    """单个 KPI 磁贴"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card2')
        self.setFixedHeight(80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        self._label = QLabel('')
        self._label.setStyleSheet(f'color:{C_TEXT3}; font-size:11px;')

        self._value = QLabel('--')
        self._value.setFont(QFont('Menlo', 14, QFont.Bold))

        self._sub = QLabel('')
        self._sub.setStyleSheet(f'color:{C_TEXT3}; font-size:11px;')

        layout.addWidget(self._label)
        layout.addWidget(self._value)
        layout.addWidget(self._sub)

        self.setStyleSheet(f"""
            QFrame#card2 {{
                background: {C_SURFACE2};
                border: 1px solid {C_BORDER};
                border-radius: 6px;
            }}
        """)

    def set_data(self, label: str, value: str, sub: str, value_color: str = C_TEXT):
        self._label.setText(label)
        self._value.setText(value)
        self._value.setStyleSheet(f'color:{value_color}; font-family:Menlo; font-size:14px; font-weight:700;')
        self._sub.setText(sub)


class KPITilesWidget(QWidget):
    """4 个 KPI 磁贴垂直排列"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._tiles = [KPITile() for _ in range(4)]
        for tile in self._tiles:
            layout.addWidget(tile)
        layout.addStretch()

    def update_kpis(self, stats: dict, accuracy: dict, quote: dict):
        tiles_data = [
            ('今日收盘', f"{quote.get('price', 0):.2f}",
             f"成交额 {quote.get('amount', 0) / 1e8:.1f}亿", C_RED),
            ('52周高 / 低',
             f"{stats.get('high_52w', 0):.2f} / {stats.get('low_52w', 0):.2f}",
             f"当前位于 {stats.get('pct_52w', 0):.0f}% 分位", C_GOLD),
            ('市盈率 PE', f"{stats.get('pe', 0):.1f}x",
             '行业均值 6.2x', C_GOLD),
            ('近30天准确率',
             f"{accuracy.get('accuracy', 0)*100:.1f}%",
             f"{accuracy.get('wins', 0)}胜 / {accuracy.get('losses', 0)}负 / 0平", C_GREEN),
        ]
        for tile, (label, value, sub, color) in zip(self._tiles, tiles_data):
            tile.set_data(label, value, sub, color)


class FeatureImportancePanel(QFrame):
    """特征重要性水平条形图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self._items = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QLabel('FEATURE IMPORTANCE · 特征重要性（Top 10）')
        header.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px;')
        layout.addWidget(header)

        self._bars_layout = QVBoxLayout()
        self._bars_layout.setSpacing(6)
        layout.addLayout(self._bars_layout)

        self.setStyleSheet(f"""
            QFrame#card {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

    def update_importance(self, items: list):
        """items: [{'feature': str, 'importance': float}, ...]"""
        while self._bars_layout.count():
            item = self._bars_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        colors = [C_BLUE, C_BLUE, C_GREEN, C_GREEN, C_GOLD, C_GOLD, C_GOLD, C_RED, C_RED, C_RED]
        feature_names_map = {
            'ma_diff_5_20': 'MA差离率(5/20)',
            'macd_hist': 'MACD Histogram',
            'vol_ratio': '成交量比',
            'rsi14': 'RSI-14',
            'boll_pct': '布林带位置',
            'ret_1d': '1日收益率',
            'ret_5d': '5日收益率',
            'ret_20d': '20日收益率',
            'amplitude': '振幅',
            'turnover': '换手率',
            'macd_golden_cross': 'MACD金叉',
            'kdj_k': 'KDJ-K',
        }

        if not items:
            # 默认展示
            items = [
                {'feature': 'MA差离率(5/20)', 'importance': 18},
                {'feature': 'MACD Histogram', 'importance': 14},
                {'feature': '成交量比', 'importance': 12},
                {'feature': 'RSI-14', 'importance': 9},
                {'feature': '布林带位置', 'importance': 8},
            ]

        for i, item in enumerate(items[:10]):
            color = colors[i] if i < len(colors) else C_TEXT3
            feature_name = feature_names_map.get(item['feature'], item['feature'])
            importance = item['importance']

            row = QWidget()
            row.setFixedHeight(24)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            rank_lbl = QLabel(f'{i+1:2d}')
            rank_lbl.setFixedWidth(16)
            rank_lbl.setFont(QFont('Menlo', 10))
            rank_lbl.setStyleSheet(f'color:{C_TEXT3};')

            name_lbl = QLabel(feature_name)
            name_lbl.setFixedWidth(140)
            name_lbl.setStyleSheet(f'color:{C_TEXT2}; font-size:12px;')

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(importance))
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{ background:#1e2030; border-radius:3px; border:none; }}
                QProgressBar::chunk {{ background:{color}; border-radius:3px; }}
            """)

            pct_lbl = QLabel(f'{importance:.1f}%')
            pct_lbl.setFixedWidth(36)
            pct_lbl.setFont(QFont('Menlo', 11))
            pct_lbl.setStyleSheet(f'color:{color};')
            pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            row_layout.addWidget(rank_lbl)
            row_layout.addWidget(name_lbl)
            row_layout.addWidget(bar)
            row_layout.addWidget(pct_lbl)

            self._bars_layout.addWidget(row)
