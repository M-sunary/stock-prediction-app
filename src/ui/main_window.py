"""
主窗口 - 三栏 Grid 布局
TopBar | IconRail | Sidebar | MainPanel
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

from .widgets.topbar import TopBar
from .widgets.icon_rail import IconRail
from .widgets.sidebar import Sidebar
from .pages.dashboard_page import DashboardPage
from .pages.watchlist_page import WatchlistPage
from .pages.backtest_page import BacktestPage
from .pages.factor_page import FactorPage
from .pages.news_page import NewsPage
from .pages.screener_page import ScreenerPage
from .dialogs.settings_dialog import SettingsDialog
from .styles.theme import APP_STYLE
from ..core.prediction_engine import PredictionWorker
from ..data.data_manager import get_data_manager
from ..core.config_manager import get_config



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('量策 AI · 次日红盘预测系统')
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)

        self._config = get_config()
        self._data = get_data_manager(self._config)
        self._worker = None

        self._init_ui()
        self._connect_signals()
        self._init_market_timer()
        self._load_initial_stock()

    def _init_ui(self):
        self.setStyleSheet(APP_STYLE)

        central = QWidget()
        self.setCentralWidget(central)

        # ── 外层垂直布局（顶栏 + 主体）────────────────────────────────────
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # TopBar
        self._topbar = TopBar()
        outer.addWidget(self._topbar)

        # 主体（Icon Rail + Sidebar + 内容区）
        body = QWidget()
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Icon Rail（64px）
        self._icon_rail = IconRail()
        body_layout.addWidget(self._icon_rail)

        # Sidebar（220px）
        self._sidebar = Sidebar()
        body_layout.addWidget(self._sidebar)

        # 内容区（剩余宽度）
        self._stack = QStackedWidget()
        self._dashboard = DashboardPage()
        self._watchlist = WatchlistPage()
        self._backtest = BacktestPage()
        self._factor = FactorPage()
        self._news = NewsPage()

        self._stack.addWidget(self._dashboard)    # 0: dashboard
        self._stack.addWidget(self._watchlist)    # 1: watchlist
        self._stack.addWidget(self._backtest)     # 2: backtest
        self._stack.addWidget(self._factor)       # 3: factor
        self._stack.addWidget(self._news)         # 4: news
        self._screener = ScreenerPage()
        self._stack.addWidget(self._screener)     # 5: screener
        body_layout.addWidget(self._stack, 1)

        outer.addWidget(body, 1)   # stretch=1 占据剩余全部高度

        # 更新侧边栏自选股数
        self._icon_rail.set_watchlist_count(len(self._config.watchlist))

    def _connect_signals(self):
        # TopBar
        self._topbar.search_triggered.connect(self._on_search)
        self._topbar.settings_clicked.connect(self._open_settings)

        # IconRail 页面切换
        self._icon_rail.page_changed.connect(self._switch_page)

        # Sidebar 股票选中
        self._sidebar.stock_selected.connect(self._on_stock_selected)

        # DashboardPage 请求预测
        self._dashboard.request_prediction.connect(self._run_prediction)

        # 自选股变化
        self._dashboard._header.watchlist_clicked.connect(self._add_to_watchlist)

        # 自选股扫描完成后刷新侧边栏
        self._watchlist.scan_done.connect(self._sidebar._load_defaults)

        # 选股雷达跳转到 dashboard
        self._screener.jump_requested.connect(self._on_screener_jump)

    def _init_market_timer(self):
        """每5分钟刷新大盘指数"""
        self._update_market_indices()
        self._market_timer = QTimer(self)
        self._market_timer.timeout.connect(self._update_market_indices)
        self._market_timer.start(5 * 60 * 1000)

    def _update_market_indices(self):
        from ..data.demo_data import generate_market_index
        try:
            data = self._data.get_market_index()
            if not data:
                data = generate_market_index()
            self._topbar.update_market_data(data)
        except Exception:
            self._topbar.update_market_data(generate_market_index())

    def _load_initial_stock(self):
        """启动时加载第一只股票"""
        QTimer.singleShot(500, lambda: self._on_stock_selected('000001', '平安银行', 75))

    @pyqtSlot(str, str, float)
    def _on_stock_selected(self, code: str, name: str, prob: float):
        self._stack.setCurrentIndex(0)
        self._dashboard.load_stock(code, name, prob)

    @pyqtSlot(str, str)
    def _run_prediction(self, code: str, name: str):
        """在后台线程中运行预测"""
        if self._worker and self._worker.isRunning():
            self._worker.terminate()

        self._dashboard.show_loading('正在获取数据...')
        self._worker = PredictionWorker(code, name)
        self._worker.result_ready.connect(self._on_prediction_done)
        self._worker.error_occurred.connect(self._on_prediction_error)
        self._worker.progress.connect(self._dashboard.show_loading)
        self._worker.start()

    @pyqtSlot(dict)
    def _on_prediction_done(self, data: dict):
        self._dashboard.update_all(data)

        code = data.get('code', '')
        # 更新侧边栏
        for item in self._sidebar._stock_items:
            if item.code == code:
                self._sidebar._load_defaults()
                break

        try:
            sectors = self._data.get_sector_data()
            if sectors:
                self._sidebar.update_sector_list(
                    [(s['name'], s['pct_chg'], s['hot']) for s in sectors]
                )
        except Exception:
            pass

        # 刷新当前可见页面
        idx = self._stack.currentIndex()
        if idx == 1:
            self._watchlist.refresh()
        elif idx == 2:
            self._backtest.load_stock(code)
        elif idx == 3:
            self._factor.load_stock(code)
        elif idx == 4:
            news = data.get('news', [])
            self._news.load_stock(code, data.get('name', ''), news if news else None)

    @pyqtSlot(str)
    def _on_prediction_error(self, msg: str):
        self._dashboard.hide_loading()
        print(f"[Prediction Error] {msg}")

    @pyqtSlot(str)
    def _on_search(self, keyword: str):
        self._sidebar.filter_stocks(keyword)
        if keyword.isdigit() and len(keyword) == 6:
            from ..data.demo_data import get_stock_params
            params = get_stock_params(keyword)
            name = params.get('name', keyword)
            self._on_stock_selected(keyword, name, 50)

    @pyqtSlot(str)
    def _switch_page(self, page_id: str):
        page_map = {
            'dashboard': 0,
            'watchlist': 1,
            'backtest': 2,
            'factor': 3,
            'news': 4,
            'screener': 5,
            'settings': None,
        }
        if page_id == 'settings':
            self._open_settings()
            return
        idx = page_map.get(page_id, 0)
        self._stack.setCurrentIndex(idx)

        current_code = getattr(self._dashboard, '_current_code', '')
        if page_id == 'watchlist':
            self._watchlist.refresh()
        elif page_id == 'backtest' and current_code:
            self._backtest.load_stock(current_code)
        elif page_id == 'factor' and current_code:
            self._factor.load_stock(current_code)
        elif page_id == 'news' and current_code:
            self._news.load_stock(current_code)
        elif page_id == 'screener':
            self._screener.refresh()

    @pyqtSlot()
    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec_()

    @pyqtSlot(dict)
    def _on_settings_saved(self, settings: dict):
        print('[Settings] Saved:', settings)

    @pyqtSlot(str)
    def _add_to_watchlist(self, code: str):
        self._config.add_to_watchlist(code)
        self._icon_rail.set_watchlist_count(len(self._config.watchlist))
        self._watchlist.refresh()
        self._sidebar._load_defaults()  # 自选变化时同步侧边栏

    @pyqtSlot(str, str)
    def _on_screener_jump(self, code: str, name: str):
        """从选股雷达跳转到 Dashboard 并加载对应股票"""
        self._icon_rail._set_active('dashboard')
        self._on_stock_selected(code, name, 50.0)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
        super().closeEvent(event)
