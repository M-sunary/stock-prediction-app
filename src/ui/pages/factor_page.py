"""
因子分析页面 - 特征重要性排行 + 因子说明
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QComboBox, QScrollArea, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from ..styles.theme import (
    C_SURFACE, C_BORDER, C_RED, C_GREEN, C_GOLD, C_BLUE,
    C_TEXT, C_TEXT2, C_TEXT3
)
from ...core.config_manager import get_config
from ...core.prediction_engine import PredictionEngine
from ...data.demo_data import get_stock_params


# 因子中文名 + 说明
FEATURE_META = {
    'ma_diff_5_20':      ('MA差离率(5/20)',  '短期均线与中期均线的偏离程度，反映趋势强度'),
    'ma_diff_5_60':      ('MA差离率(5/60)',  '短期与长期均线偏离，用于判断长期趋势'),
    'macd_hist':         ('MACD柱',          'MACD快慢线差值，量化多空动能'),
    'macd':              ('MACD线',          'DIF线，12日与26日EMA之差'),
    'macd_signal':       ('MACD信号线',      'DEA线，MACD的9日EMA'),
    'vol_ratio':         ('量比',             '当日成交量相对近期均量的比值，放量信号'),
    'rsi14':             ('RSI-14',          '相对强弱指数，50以上偏多，70以上超买'),
    'rsi6':              ('RSI-6',           '短周期RSI，对价格变化更敏感'),
    'kdj_k':             ('KDJ-K',           'KDJ指标K值，随机震荡基准'),
    'kdj_d':             ('KDJ-D',           'KDJ指标D值，K的移动平均'),
    'kdj_j':             ('KDJ-J',           'KDJ指标J值，超买超卖最敏感'),
    'boll_pct':          ('布林带位置',       '价格在布林带中的相对位置(0=下轨,1=上轨)'),
    'boll_width':        ('布林带宽',         '布林带宽度，衡量近期波动性'),
    'ret_1d':            ('1日涨跌幅',        '前1日收益率，短线动量'),
    'ret_5d':            ('5日累计涨跌',      '近5日累计涨跌幅，短期趋势'),
    'ret_20d':           ('20日累计涨跌',     '近20日累计涨跌幅，中期趋势'),
    'amplitude':         ('当日振幅',         '(最高-最低)/前收，衡量日内波动'),
    'turnover':          ('换手率',           '成交量/流通股，资金活跃度'),
    'obv':               ('OBV趋势',         '能量潮，量价结合判断趋势'),
    'vol_10d':           ('10日波动率',       '近10日收益率标准差，风险度量'),
    'ma5':               ('MA5',             '5日移动平均线，短期趋势'),
    'ma10':              ('MA10',            '10日移动平均线'),
    'ma20':              ('MA20',            '20日移动平均线，中期支撑/压力'),
    'ma60':              ('MA60',            '60日移动平均线，长期趋势'),
    'cci20':             ('CCI-20',          '顺势指标，价格偏离均值程度'),
    'macd_golden_cross': ('MACD金叉',        '快线由下向上穿越慢线（买入信号）'),
    'vol_ma5_ratio':     ('量/均量比',        '成交量与5日均量之比'),
}

_RANK_COLORS = [C_RED, C_RED, C_RED, C_RED, C_RED,   # top 5
                C_GREEN, C_GREEN, C_GREEN, C_GREEN, C_GREEN,  # 6-10
                C_GOLD, C_GOLD, C_GOLD, C_GOLD, C_GOLD]      # 11-15


class ImportanceBar(QFrame):
    """单条特征重要性行"""
    def __init__(self, rank: int, feature: str, importance: float, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setStyleSheet(f'QFrame {{ border-bottom:1px solid {C_BORDER}; background:transparent; }}')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        color = _RANK_COLORS[min(rank, len(_RANK_COLORS) - 1)]
        meta = FEATURE_META.get(feature, (feature, ''))
        display_name = meta[0]

        rank_lbl = QLabel(f'#{rank + 1}')
        rank_lbl.setFixedWidth(24)
        rank_lbl.setFont(QFont('Menlo', 10))
        rank_lbl.setStyleSheet(f'color:{color}; background:transparent;')

        name_lbl = QLabel(display_name)
        name_lbl.setFixedWidth(110)
        name_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:12px; background:transparent;')

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
        pct_lbl.setFixedWidth(40)
        pct_lbl.setFont(QFont('Menlo', 10))
        pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pct_lbl.setStyleSheet(f'color:{color}; background:transparent;')

        layout.addWidget(rank_lbl)
        layout.addWidget(name_lbl)
        layout.addWidget(bar, 1)
        layout.addWidget(pct_lbl)


class DescriptionRow(QFrame):
    """因子说明行"""
    def __init__(self, rank: int, feature: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        color = _RANK_COLORS[min(rank, len(_RANK_COLORS) - 1)]
        self.setStyleSheet(f"""
            QFrame {{
                border-left:3px solid {color};
                border-bottom:1px solid {C_BORDER};
                background:transparent;
                padding-left:8px;
            }}
        """)

        meta = FEATURE_META.get(feature, (feature, '指标说明暂缺'))
        name, desc = meta

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:12px; font-weight:600; background:transparent;')

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f'color:{C_TEXT2}; font-size:11px; background:transparent;')
        desc_lbl.setWordWrap(True)

        layout.addWidget(name_lbl)
        layout.addWidget(desc_lbl)


class FactorPage(QWidget):
    """因子分析页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = get_config()
        self._current_code = ''
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── 标题栏 ─────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel('因子分析')
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

        # ── 内容区：重要性条 + 说明 ────────────────────────────────────────
        content = QHBoxLayout()
        content.setSpacing(16)

        # 左：重要性排行
        bars_card = QFrame()
        bars_card.setObjectName('card')
        bars_card.setStyleSheet(f"""
            QFrame#card {{
                background:{C_SURFACE};
                border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)
        bars_layout = QVBoxLayout(bars_card)
        bars_layout.setContentsMargins(0, 12, 0, 8)
        bars_layout.setSpacing(0)
        bars_hdr = QLabel('FEATURE IMPORTANCE · 特征重要性 Top 15')
        bars_hdr.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; padding:0 16px 8px 16px;')
        bars_layout.addWidget(bars_hdr)
        self._bars_container = QVBoxLayout()
        self._bars_container.setSpacing(0)
        bars_layout.addLayout(self._bars_container)
        bars_layout.addStretch()
        content.addWidget(bars_card, 55)

        # 右：因子说明（可滚动）
        desc_card = QFrame()
        desc_card.setObjectName('card')
        desc_card.setStyleSheet(f"""
            QFrame#card {{
                background:{C_SURFACE};
                border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)
        desc_outer = QVBoxLayout(desc_card)
        desc_outer.setContentsMargins(0, 12, 0, 0)
        desc_outer.setSpacing(0)
        desc_hdr = QLabel('FACTOR GUIDE · 因子说明')
        desc_hdr.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; padding:0 16px 8px 16px;')
        desc_outer.addWidget(desc_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f'QScrollArea {{ background:transparent; border:none; }}')
        self._desc_content = QWidget()
        self._desc_content.setStyleSheet('background:transparent;')
        self._desc_layout = QVBoxLayout(self._desc_content)
        self._desc_layout.setContentsMargins(0, 0, 0, 0)
        self._desc_layout.setSpacing(0)
        scroll.setWidget(self._desc_content)
        desc_outer.addWidget(scroll)
        content.addWidget(desc_card, 45)

        layout.addLayout(content, 1)
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

    def load_stock(self, code: str):
        self._current_code = code
        self._refresh_selector()
        for i in range(self._selector.count()):
            if self._selector.itemData(i) == code:
                self._selector.blockSignals(True)
                self._selector.setCurrentIndex(i)
                self._selector.blockSignals(False)
                break

        engine = PredictionEngine.instance()
        items = engine.get_cached_feature_importance(code)
        if not items:
            items = self._default_importance()

        # 更新重要性条
        while self._bars_container.count():
            item = self._bars_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for rank, item in enumerate(items[:15]):
            bar = ImportanceBar(rank, item['feature'], item['importance'])
            self._bars_container.addWidget(bar)

        # 更新因子说明
        while self._desc_layout.count():
            item = self._desc_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for rank, item in enumerate(items[:15]):
            row = DescriptionRow(rank, item['feature'])
            self._desc_layout.addWidget(row)
        self._desc_layout.addStretch()

    def _default_importance(self) -> list:
        """无缓存时的默认展示数据"""
        defaults = [
            ('ma_diff_5_20', 18.0), ('macd_hist', 14.0), ('vol_ratio', 12.0),
            ('rsi14', 9.0), ('boll_pct', 8.0), ('ret_5d', 8.0),
            ('ret_1d', 7.0), ('turnover', 7.0), ('kdj_j', 6.0),
            ('vol_10d', 5.0), ('amplitude', 4.0), ('ret_20d', 4.0),
            ('macd_golden_cross', 3.0), ('cci20', 2.0), ('obv', 1.0),
        ]
        return [{'feature': f, 'importance': v} for f, v in defaults]
