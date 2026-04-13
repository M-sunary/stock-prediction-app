"""
自选股页面（简版）
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QBrush
from ..styles.theme import (
    C_SURFACE, C_BORDER, C_RED, C_GREEN, C_GOLD,
    C_TEXT, C_TEXT2, C_TEXT3
)
from ...core.config_manager import get_config
from ...data.demo_data import get_stock_params
from ...data.cache_manager import get_cache
from ...core.prediction_engine import PredictionEngine


class ScanAllWorker(QThread):
    """依次对自选股运行预测，每完成一只发射 one_done 信号"""
    one_done = pyqtSignal(str, dict)   # code, result
    all_done = pyqtSignal()

    def __init__(self, codes: list):
        super().__init__()
        self._codes = codes

    def run(self):
        engine = PredictionEngine.instance()
        for code in self._codes:
            try:
                result = engine.run_prediction(code)
                self.one_done.emit(code, result)
            except Exception as e:
                print(f'[ScanAll] {code} 失败: {e}')
        self.all_done.emit()


class WatchlistPage(QWidget):
    stock_selected = pyqtSignal(str, str)  # code, name
    scan_done = pyqtSignal()               # 全部扫描完成

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = get_config()
        self._scan_worker = None
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel('自选股')
        title.setFont(QFont('PingFang SC', 20, QFont.Bold))
        title.setStyleSheet(f'color:{C_TEXT};')
        header.addWidget(title)
        header.addStretch()

        self._scan_btn = QPushButton('⚡ 一键扫描')
        self._scan_btn.setFixedHeight(34)
        self._scan_btn.setStyleSheet(f"""
            QPushButton {{
                background:{C_RED}; color:#fff;
                border:none; border-radius:6px;
                padding:0 16px; font-size:13px; font-weight:600;
            }}
            QPushButton:hover {{ background:#d93030; }}
            QPushButton:disabled {{ background:{C_BORDER}; color:{C_TEXT3}; }}
        """)
        self._scan_btn.clicked.connect(self._start_scan)
        header.addWidget(self._scan_btn)
        layout.addLayout(header)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(['代码', '名称', '预测概率', '操作'])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.setStyleSheet(f"""
            QTableWidget {{ background:transparent; border:none; font-size:13px; }}
            QTableWidget::item {{ border-bottom:1px solid {C_BORDER}; padding:8px; color:{C_TEXT}; }}
            QHeaderView::section {{
                background:transparent; color:{C_TEXT3}; border:none;
                border-bottom:1px solid {C_BORDER}; padding:8px;
                font-size:11px; font-weight:600; letter-spacing:1px;
            }}
        """)
        layout.addWidget(self._table)

    def refresh(self):
        watchlist = self._config.watchlist
        cache = get_cache()
        self._table.setRowCount(len(watchlist))
        for row, code in enumerate(watchlist):
            self._table.setRowHeight(row, 44)
            self._table.setItem(row, 0, QTableWidgetItem(code))

            # 名称：优先缓存的 stock_info，回退到 demo 参数
            name = '--'
            cached_info = cache.get(f"info_{code}", max_age_hours=24 * 7)
            if cached_info and cached_info.get('name') and cached_info['name'] != code:
                name = cached_info['name']
            else:
                params = get_stock_params(code)
                if params.get('name') and params['name'] != code:
                    name = params['name']
            self._table.setItem(row, 1, QTableWidgetItem(name))

            # 预测概率：取最近一条预测历史
            history = cache.get_prediction_history(code, limit=1)
            if history:
                last = history[0]
                prob = last.get('probability', 0)
                direction = last.get('direction', '')
                prob_text = f"{prob:.1f}%  {direction}"
                prob_item = QTableWidgetItem(prob_text)
                color = C_RED if direction == '看多' else C_GREEN
                prob_item.setForeground(QBrush(QColor(color)))
            else:
                prob_item = QTableWidgetItem('--')
            self._table.setItem(row, 2, prob_item)

            rm_btn = QPushButton('移除')
            rm_btn.setStyleSheet(f"""
                QPushButton {{
                    background:transparent; color:{C_TEXT3};
                    border:1px solid {C_BORDER}; border-radius:4px;
                    padding:4px 10px; font-size:12px;
                }}
                QPushButton:hover {{ color:{C_RED}; border-color:{C_RED}; }}
            """)
            rm_btn.clicked.connect(lambda _, c=code: self._remove(c))
            self._table.setCellWidget(row, 3, rm_btn)

    def _remove(self, code: str):
        self._config.remove_from_watchlist(code)
        self.refresh()

    def _start_scan(self):
        codes = list(self._config.watchlist)
        if not codes:
            return
        self._scan_btn.setEnabled(False)
        self._scan_btn.setText('扫描中...')
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.terminate()
        self._scan_worker = ScanAllWorker(codes)
        self._scan_worker.one_done.connect(self._on_one_scanned)
        self._scan_worker.all_done.connect(self._on_scan_done)
        self._scan_worker.start()

    def _on_one_scanned(self, code: str, result: dict):
        self.refresh()

    def _on_scan_done(self):
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText('⚡ 一键扫描')
        self.refresh()
        self.scan_done.emit()
