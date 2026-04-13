"""
K线图组件 - 基于 pyqtgraph，支持 demo 模式
"""
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from ..styles.theme import (
    C_SURFACE, C_BORDER, C_BORDER2,
    C_RED, C_GREEN, C_GOLD, C_BLUE,
    C_TEXT, C_TEXT2, C_TEXT3
)

try:
    import pyqtgraph as pg
    pg.setConfigOption('background', '#0f1117')
    pg.setConfigOption('foreground', '#4a4e68')
    pg.setConfigOption('antialias', True)
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False


class CandlestickItem(pg.GraphicsObject if HAS_PYQTGRAPH else QWidget):
    """K 线蜡烛图"""
    def __init__(self):
        if not HAS_PYQTGRAPH:
            return
        super().__init__()
        self._data = []
        self._pic = None

    def set_data(self, ohlcv: list):
        self._data = ohlcv
        self._rebuild()
        self.informViewBoundsChanged()

    def _rebuild(self):
        from PyQt5.QtGui import QPicture, QPainter
        self._pic = QPicture()
        if not self._data:
            return
        p = QPainter(self._pic)
        w = 0.38
        for i, o, h, l, c, _v in self._data:
            color = QColor(C_RED) if c >= o else QColor(C_GREEN)
            p.setPen(pg.mkPen(color, width=1))
            p.setBrush(pg.mkBrush(color))
            # 影线
            p.drawLine(pg.QtCore.QPointF(i, l), pg.QtCore.QPointF(i, h))
            # 实体
            body_h = abs(c - o) or 0.001
            p.drawRect(pg.QtCore.QRectF(i - w, min(o, c), w * 2, body_h))
        p.end()

    def paint(self, p, *args):
        if self._pic:
            p.drawPicture(0, 0, self._pic)

    def boundingRect(self):
        if self._pic:
            return pg.QtCore.QRectF(self._pic.boundingRect())
        return pg.QtCore.QRectF(0, 0, 1, 1)


class ChartPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('chart_card')
        self._df = None
        self._current_tab = 'daily'
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(8)

        # ── 标题 + 标签切换 ──────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel('K线走势')
        title.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; background:transparent;')
        header.addWidget(title)
        header.addStretch()

        self._tabs = {}
        tab_def = [('日K', 'daily'), ('周K', 'weekly'), ('月K', 'monthly'),
                   ('MACD', 'macd'), ('RSI', 'rsi')]
        for label, key in tab_def:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            # 根据字符数自适应宽度：中文2字 or 英文4字 MACD
            btn.setMinimumWidth(46)
            btn.setMaximumWidth(64)
            btn.setCheckable(True)
            btn.setChecked(key == 'daily')
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _checked, k=key: self._switch_tab(k))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C_TEXT3};
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                }}
                QPushButton:checked {{
                    background: {C_RED}33;
                    color: {C_RED};
                    font-weight: 600;
                }}
                QPushButton:hover:!checked {{
                    color: {C_TEXT2};
                }}
            """)
            self._tabs[key] = btn
            header.addWidget(btn)
        layout.addLayout(header)

        # ── 图表区域 ─────────────────────────────────────────────────────
        if HAS_PYQTGRAPH:
            chart_area = QWidget()
            chart_area.setStyleSheet('background:transparent;')
            cl = QVBoxLayout(chart_area)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(2)

            # 主 K 线图
            self._plot = pg.PlotWidget()
            self._plot.setMinimumHeight(180)
            self._plot.setMouseEnabled(x=True, y=False)
            self._plot.showGrid(x=False, y=True, alpha=0.12)
            self._plot.setBackground('#0f1117')
            # 隐藏顶部 / 右侧轴
            self._plot.showAxis('top', False)
            self._plot.showAxis('right', False)
            self._plot.getAxis('left').setTextPen(pg.mkPen(C_TEXT3))
            self._plot.getAxis('bottom').setTextPen(pg.mkPen(C_TEXT3))
            self._plot.getAxis('left').setStyle(tickFont=QFont('Menlo', 9))
            self._plot.getAxis('bottom').setStyle(tickFont=QFont('Menlo', 9))

            self._candle = CandlestickItem()
            self._plot.addItem(self._candle)
            self._ma5 = self._plot.plot(pen=pg.mkPen(C_BLUE, width=1.2), name='MA5')
            self._ma20 = self._plot.plot(pen=pg.mkPen(C_GOLD, width=1.2), name='MA20')

            # 成交量子图
            self._vplt = pg.PlotWidget()
            self._vplt.setFixedHeight(48)
            self._vplt.setXLink(self._plot)
            self._vplt.setBackground('#0f1117')
            self._vplt.showAxis('top', False)
            self._vplt.showAxis('right', False)
            self._vplt.showAxis('left', False)
            self._vplt.showGrid(x=False, y=False)
            self._vbars = pg.BarGraphItem(x=[], height=[], width=0.75, brushes=[])
            self._vplt.addItem(self._vbars)

            cl.addWidget(self._plot)
            cl.addWidget(self._vplt)
            layout.addWidget(chart_area)
        else:
            lbl = QLabel('图表库未安装\npip install pyqtgraph')
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:13px;')
            lbl.setMinimumHeight(200)
            layout.addWidget(lbl)

        self.setStyleSheet(f"""
            QFrame#chart_card {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

    def _switch_tab(self, key: str):
        self._current_tab = key
        for k, btn in self._tabs.items():
            btn.setChecked(k == key)
        if self._df is not None:
            self._render(self._df, key)

    def update_chart(self, df: pd.DataFrame):
        self._df = df
        if df is not None and not df.empty:
            self._render(df, self._current_tab)

    def _render(self, df: pd.DataFrame, mode: str):
        if not HAS_PYQTGRAPH:
            return
        if mode == 'daily':
            data = df.tail(90).copy()
        elif mode == 'weekly':
            data = self._resample(df, 'W').tail(52)
        elif mode == 'monthly':
            data = self._resample(df, 'ME').tail(36)
        elif mode == 'macd':
            self._render_oscillator(df.tail(90), 'macd_hist', 'macd', 'macd_signal')
            return
        elif mode == 'rsi':
            self._render_line(df.tail(90), 'rsi14', [30, 70])
            return
        else:
            data = df.tail(90).copy()
        self._render_kline(data)

    def _render_kline(self, df: pd.DataFrame):
        df = df.reset_index(drop=True)
        n = len(df)
        ohlcv = []
        for i, row in enumerate(df.itertuples()):
            ohlcv.append((i,
                          float(getattr(row, 'open', 0)),
                          float(getattr(row, 'high', 0)),
                          float(getattr(row, 'low', 0)),
                          float(getattr(row, 'close', 0)),
                          float(getattr(row, 'volume', 0))))
        self._candle.set_data(ohlcv)

        xs = list(range(n))
        if 'ma5' in df.columns:
            vals = df['ma5'].ffill().tolist()
            self._ma5.setData(xs, vals)
        else:
            self._ma5.setData([], [])

        if 'ma20' in df.columns:
            vals = df['ma20'].ffill().tolist()
            self._ma20.setData(xs, vals)
        else:
            self._ma20.setData([], [])

        # 成交量
        vols = df['volume'].tolist() if 'volume' in df.columns else [0] * n
        closes = df['close'].tolist()
        opens = df['open'].tolist()
        brushes = [
            pg.mkBrush(QColor(C_RED)) if closes[i] >= opens[i]
            else pg.mkBrush(QColor(C_GREEN))
            for i in range(n)
        ]
        self._vbars.setOpts(x=xs, height=vols, width=0.75, brushes=brushes,
                            pens=[pg.mkPen(None)] * n)

        # X 轴时间标签
        ticks = []
        step = max(1, n // 8)
        for i in range(0, n, step):
            d = df.iloc[i].get('date', '')
            ticks.append((i, str(d)[:10] if d else ''))
        self._plot.getAxis('bottom').setTicks([ticks])

        # 自动调整 Y 轴范围（避免 0 开始）
        prices = [v for o in ohlcv for v in (o[2], o[3])]  # highs and lows
        if prices:
            ymin, ymax = min(prices), max(prices)
            pad = (ymax - ymin) * 0.05 or ymax * 0.02
            self._plot.setYRange(ymin - pad, ymax + pad, padding=0)

    def _render_oscillator(self, df, hist_col, fast_col, slow_col):
        """MACD 柱状图"""
        n = len(df)
        xs = list(range(n))
        self._candle.set_data([])
        self._ma5.setData(xs, df[fast_col].fillna(0).tolist() if fast_col in df.columns else [0]*n)
        self._ma20.setData(xs, df[slow_col].fillna(0).tolist() if slow_col in df.columns else [0]*n)
        if hist_col in df.columns:
            h = df[hist_col].fillna(0).tolist()
            brushes = [pg.mkBrush(QColor(C_RED)) if v >= 0 else pg.mkBrush(QColor(C_GREEN))
                       for v in h]
            self._vbars.setOpts(x=xs, height=h, width=0.75, brushes=brushes,
                                pens=[pg.mkPen(None)]*n)
        self._plot.setYRange(-0.2, 0.2, padding=0.1)

    def _render_line(self, df, col, hlines=None):
        n = len(df)
        xs = list(range(n))
        self._candle.set_data([])
        self._ma5.setData(xs, df[col].fillna(50).tolist() if col in df.columns else [50]*n)
        self._ma20.setData([], [])
        if hlines:
            for y in hlines:
                self._plot.addLine(y=y, pen=pg.mkPen(C_TEXT3, style=Qt.DashLine))
        self._vbars.setOpts(x=[], height=[], width=0.75, brushes=[])
        self._plot.setYRange(0, 100, padding=0)

    def _resample(self, df: pd.DataFrame, rule: str) -> pd.DataFrame:
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        agg = {'open': 'first', 'high': 'max', 'low': 'min',
               'close': 'last', 'volume': 'sum'}
        return df.resample(rule).agg(agg).dropna().reset_index()
