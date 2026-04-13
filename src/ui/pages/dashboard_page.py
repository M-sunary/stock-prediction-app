"""
预测看板主页面 - 整合所有 UI 组件
"""
import datetime
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from ..widgets.stock_header import StockHeader, KPITilesWidget, FeatureImportancePanel
from ..widgets.prediction_hero import PredictionHero
from ..widgets.chart_panel import ChartPanel
from ..widgets.indicator_panels import TechIndicatorPanel, SentimentPanel
from ..widgets.risk_history import RiskFactorsPanel, PredictionHistoryPanel
from ..styles.theme import C_BG, C_BORDER


class LoadingOverlay(QWidget):
    """加载遮罩层"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._label = QLabel('正在加载...')
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet(f'color:#8b8fa8; font-size:14px;')
        layout.addWidget(self._label)

        self.setStyleSheet(f'background:rgba(8,9,13,0.85); border-radius:8px;')
        self.hide()

    def show_message(self, msg: str):
        self._label.setText(msg)
        self.show()
        self.raise_()

    def hide_loading(self):
        self.hide()


class DashboardPage(QWidget):
    """预测看板主页面"""
    request_prediction = pyqtSignal(str, str)   # code, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_code = ''
        self._current_name = ''
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 滚动容器 ────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # ── 1. 股票标题栏 ────────────────────────────────────────────────────
        self._header = StockHeader()
        self._header.run_prediction_clicked.connect(self._on_run_prediction)
        self._header.refresh_clicked.connect(self._on_run_prediction)
        content_layout.addWidget(self._header)

        # ── 2. 预测英雄区 ─────────────────────────────────────────────────
        self._prediction_hero = PredictionHero()
        content_layout.addWidget(self._prediction_hero)

        # ── 3. K线图 + KPI 磁贴 ───────────────────────────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        self._chart = ChartPanel()
        self._chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._chart.setMinimumHeight(310)
        self._kpi_tiles = KPITilesWidget()
        self._kpi_tiles.setFixedWidth(200)

        row3.addWidget(self._chart, 2)
        row3.addWidget(self._kpi_tiles, 1)
        content_layout.addLayout(row3)

        # ── 4. 技术指标 + 情感分析 ─────────────────────────────────────────
        row4 = QHBoxLayout()
        row4.setSpacing(16)
        self._tech_panel = TechIndicatorPanel()
        self._sentiment_panel = SentimentPanel()
        row4.addWidget(self._tech_panel, 1)
        row4.addWidget(self._sentiment_panel, 1)
        content_layout.addLayout(row4)

        # ── 5. 风险因子 + 预测历史 ─────────────────────────────────────────
        row5 = QHBoxLayout()
        row5.setSpacing(16)
        self._risk_panel = RiskFactorsPanel()
        self._history_panel = PredictionHistoryPanel()
        row5.addWidget(self._risk_panel, 1)
        row5.addWidget(self._history_panel, 1)
        content_layout.addLayout(row5)

        # ── 6. 特征重要性 ──────────────────────────────────────────────────
        self._feature_panel = FeatureImportancePanel()
        content_layout.addWidget(self._feature_panel)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)  # stretch=1 填满剩余高度

        # ── 加载遮罩 ────────────────────────────────────────────────────────
        self._loading = LoadingOverlay(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._loading.setGeometry(self.rect())

    def load_stock(self, code: str, name: str, prob: float = 50):
        """从侧边栏选中股票时调用"""
        self._current_code = code
        self._current_name = name
        # 立即更新标题（用默认值，等待真实数据）
        self._header.update_stock(name, code, 'SZ' if code.startswith('0') else 'SH',
                                  '--', 0, 0, 0)
        # 请求完整预测数据
        self.request_prediction.emit(code, name)

    def show_loading(self, msg: str = '正在加载...'):
        self._loading.show_message(msg)

    def hide_loading(self):
        self._loading.hide_loading()

    def update_all(self, data: dict):
        """用预测结果更新所有组件"""
        if data.get('error'):
            self.hide_loading()
            return

        code = data.get('code', '')
        name = data.get('name', '')
        quote = data.get('quote', {})
        df = data.get('df_ta')
        prediction = data.get('prediction', {})
        signals = data.get('signals', [])
        indicators = data.get('indicators', [])
        sentiment_score = data.get('sentiment_score', 0.0)
        news = data.get('news', [])
        risk_factors = data.get('risk_factors', [])
        feature_importance = data.get('feature_importance', [])
        history = data.get('history', [])
        accuracy = data.get('accuracy', {})
        stats = data.get('stats', {})

        now_str = datetime.datetime.now().strftime('%H:%M · %Y-%m-%d')

        # 1. 更新标题
        market = 'SZ' if code.startswith('0') or code.startswith('3') else 'SH'
        industry = quote.get('industry', '--')
        self._header.update_stock(
            name, code, market, industry,
            quote.get('price', 0),
            quote.get('change', 0),
            quote.get('pct_chg', 0)
        )

        # 2. 预测英雄区
        self._prediction_hero.update_prediction(prediction, signals, accuracy, now_str)

        # 3. K线图
        if df is not None and not df.empty:
            self._chart.update_chart(df)

        # 4. KPI 磁贴
        self._kpi_tiles.update_kpis(stats, accuracy, quote)

        # 5. 技术指标
        if indicators:
            self._tech_panel.update_indicators(indicators)

        # 6. 情感分析
        self._sentiment_panel.update_sentiment(sentiment_score, news)

        # 7. 风险因子
        if risk_factors:
            self._risk_panel.update_risks(risk_factors)

        # 8. 预测历史
        self._history_panel.update_history(history)

        # 9. 特征重要性
        self._feature_panel.update_importance(feature_importance)

        self.hide_loading()

    def _on_run_prediction(self):
        if self._current_code:
            self.show_loading('运行预测模型...')
            self.request_prediction.emit(self._current_code, self._current_name)
