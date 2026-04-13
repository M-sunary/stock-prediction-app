"""
设置对话框
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QCheckBox,
    QFormLayout, QFrame, QSpinBox, QDoubleSpinBox,
    QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ..styles.theme import (
    C_SURFACE, C_SURFACE2, C_BORDER2, C_RED, C_RED_HOVER,
    C_TEXT, C_TEXT2, C_TEXT3, APP_STYLE
)
from ...core.config_manager import get_config


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('系统参数配置')
        self.setFixedSize(480, 580)
        self.setModal(True)
        self._config = get_config()
        self._init_ui()
        self._load_settings()
        self.setStyleSheet(f"""
            QDialog {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER2};
                border-radius: 12px;
            }}
            QLabel {{ color:{C_TEXT}; }}
            {APP_STYLE}
        """)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(52)
        title_bar.setStyleSheet(f'background:{C_SURFACE}; border-bottom:1px solid {C_BORDER2};')
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)

        title_lbl = QLabel('系统参数配置')
        title_lbl.setFont(QFont('PingFang SC', 15, QFont.Bold))
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT3};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{ color:{C_TEXT}; }}
        """)
        close_btn.clicked.connect(self.reject)

        title_layout.addWidget(title_lbl)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        layout.addWidget(title_bar)

        # 滚动内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        form = QFormLayout(content)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignLeft)

        label_style = f'color:{C_TEXT2}; font-size:13px;'

        # 数据源
        self._data_source = QComboBox()
        self._data_source.addItems(['AKShare（免费）', 'Tushare Pro（需Token）', '东方财富 API'])
        form.addRow(self._mk_label('数据源', label_style), self._data_source)

        # Tushare Token
        self._tushare_token = QLineEdit()
        self._tushare_token.setPlaceholderText('请输入 Tushare Token')
        self._tushare_token.setEchoMode(QLineEdit.Password)
        form.addRow(self._mk_label('Tushare Token', label_style), self._tushare_token)

        # 预测模型
        self._pred_model = QComboBox()
        self._pred_model.addItems([
            '集成模型（XGB + LGB）推荐',
            'XGBoost Only',
            'LightGBM Only',
            'LSTM 深度学习',
        ])
        form.addRow(self._mk_label('预测模型', label_style), self._pred_model)

        # 历史数据范围
        self._history_years = QComboBox()
        self._history_years.addItems(['近2年', '近3年', '近5年'])
        form.addRow(self._mk_label('历史数据范围', label_style), self._history_years)

        # 开关组
        self._enable_sentiment = self._mk_toggle('启用情感分析（新闻NLP）')
        self._enable_northbound = self._mk_toggle('北向资金因子')
        self._auto_refresh = self._mk_toggle('每日自动刷新（收盘后）')
        self._push_notify = self._mk_toggle('预测推送通知')

        form.addRow(self._enable_sentiment)
        form.addRow(self._enable_northbound)
        form.addRow(self._auto_refresh)
        form.addRow(self._push_notify)

        # 红盘阈值
        self._threshold = QDoubleSpinBox()
        self._threshold.setRange(0, 3)
        self._threshold.setSingleStep(0.1)
        self._threshold.setValue(0.5)
        self._threshold.setSuffix(' %')
        form.addRow(self._mk_label('红盘阈值（%）', label_style), self._threshold)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # 保存按钮
        footer = QWidget()
        footer.setFixedHeight(60)
        footer.setStyleSheet(f'background:{C_SURFACE}; border-top:1px solid {C_BORDER2};')
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)

        save_btn = QPushButton('保存配置')
        save_btn.setFixedHeight(36)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_RED};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background:{C_RED_HOVER}; }}
        """)

        footer_layout.addStretch()
        footer_layout.addWidget(save_btn)
        layout.addWidget(footer)

    def _mk_label(self, text: str, style: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(style)
        return lbl

    def _mk_toggle(self, text: str) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setStyleSheet(f'color:{C_TEXT2}; font-size:13px;')
        return cb

    def _load_settings(self):
        ds = self._config.get('data_source', 'akshare')
        ds_map = {'akshare': 0, 'tushare': 1, 'eastmoney': 2}
        self._data_source.setCurrentIndex(ds_map.get(ds, 0))

        self._tushare_token.setText(self._config.get('tushare_token', ''))

        pm = self._config.get('prediction_model', 'ensemble')
        pm_map = {'ensemble': 0, 'xgboost': 1, 'lightgbm': 2, 'lstm': 3}
        self._pred_model.setCurrentIndex(pm_map.get(pm, 0))

        yrs = self._config.get('history_years', 3)
        yrs_map = {2: 0, 3: 1, 5: 2}
        self._history_years.setCurrentIndex(yrs_map.get(yrs, 1))

        self._enable_sentiment.setChecked(self._config.get('enable_sentiment', True))
        self._enable_northbound.setChecked(self._config.get('enable_northbound', True))
        self._auto_refresh.setChecked(self._config.get('auto_refresh', False))
        self._push_notify.setChecked(self._config.get('push_notification', True))
        self._threshold.setValue(self._config.get('red_threshold', 0.5))

    def _save(self):
        ds_map = {0: 'akshare', 1: 'tushare', 2: 'eastmoney'}
        pm_map = {0: 'ensemble', 1: 'xgboost', 2: 'lightgbm', 3: 'lstm'}
        yrs_map = {0: 2, 1: 3, 2: 5}

        settings = {
            'data_source': ds_map[self._data_source.currentIndex()],
            'tushare_token': self._tushare_token.text(),
            'prediction_model': pm_map[self._pred_model.currentIndex()],
            'history_years': yrs_map[self._history_years.currentIndex()],
            'enable_sentiment': self._enable_sentiment.isChecked(),
            'enable_northbound': self._enable_northbound.isChecked(),
            'auto_refresh': self._auto_refresh.isChecked(),
            'push_notification': self._push_notify.isChecked(),
            'red_threshold': self._threshold.value(),
        }
        for k, v in settings.items():
            self._config.set(k, v)
        self._config.save()
        self.settings_saved.emit(settings)
        self.accept()
