"""
选股雷达页面 - A 股市场实时行情多条件筛选
数据来源：AKShare stock_zh_a_spot_em（降级至合成演示数据）
"""
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QBrush

from ..styles.theme import (
    C_SURFACE, C_SURFACE2, C_BORDER, C_BORDER2,
    C_RED, C_RED_HOVER, C_RED_GLOW, C_GREEN, C_GREEN_GLOW, C_GOLD,
    C_TEXT, C_TEXT2, C_TEXT3,
)
from ...data.demo_data import _STOCK_PARAMS

MAX_DISPLAY = 200   # 最多渲染行数

# QColor 常量（避免重复构造）
_QC_RED    = QColor('#f03e3e')
_QC_GREEN  = QColor('#20c984')
_QC_GOLD   = QColor('#e8a838')
_QC_TEXT2  = QColor('#8b8fa8')
_QC_TEXT3  = QColor('#4a4e68')
_QC_RED_BG   = QColor(240, 62,  62,  35)   # C_RED  @ ~14% alpha
_QC_GREEN_BG = QColor(32,  201, 132, 35)   # C_GREEN @ ~14% alpha


# ── 演示数据（AKShare 不可用时的回退）────────────────────────────────────────

def _generate_demo_snapshot() -> pd.DataFrame:
    """基于 demo_data 生成当天固定的合成行情快照"""
    from datetime import date
    rng = np.random.default_rng(int(date.today().strftime('%Y%m%d')))
    rows = []
    for code, p in _STOCK_PARAMS.items():
        base   = p['price']
        pct    = round(float(rng.uniform(-5.0, 7.0)), 2)
        price  = round(base * (1 + pct / 100), 2)
        vr     = round(float(rng.uniform(0.3, 4.0)), 2)
        to     = round(float(rng.uniform(0.1, 6.0)), 2)
        amount = round(base * 5e7 * vr * float(rng.uniform(0.5, 2.0)))
        rows.append({'code': code, 'name': p['name'], 'price': price,
                     'pct_chg': pct, 'vol_ratio': vr,
                     'turnover': to, 'amount': amount})
    return pd.DataFrame(rows)


# ── 后台拉取线程 ──────────────────────────────────────────────────────────────

class MarketFetchWorker(QThread):
    data_ready  = pyqtSignal(object, bool)  # df, is_demo
    fetch_error = pyqtSignal(str)

    def run(self):
        # 优先通过 DataManager（带缓存 + 冷却感知），避免重复建立连接
        try:
            from ...data.data_manager import get_data_manager
            df = get_data_manager().get_market_snapshot()
            if df is not None and not df.empty:
                self.data_ready.emit(df, False)
                return
        except Exception as exc:
            print(f'[MarketFetchWorker] DataManager 获取失败: {exc}')

        # DataManager 也失败时降级到演示数据
        try:
            self.data_ready.emit(_generate_demo_snapshot(), True)
        except Exception as e:
            self.fetch_error.emit(str(e))


# ── FilterChip / FilterGroup ──────────────────────────────────────────────────

class FilterChip(QPushButton):
    def __init__(self, label, parent=None):
        super().__init__(label, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(26)
        self._update_style()
        self.toggled.connect(lambda _: self._update_style())

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background:{C_RED}; color:white; border:none;
                    border-radius:13px; padding:0 12px;
                    font-size:12px; font-weight:600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:{C_SURFACE2}; color:{C_TEXT2};
                    border:1px solid {C_BORDER2}; border-radius:13px;
                    padding:0 12px; font-size:12px;
                }}
                QPushButton:hover {{ border-color:{C_TEXT3}; color:{C_TEXT}; }}
            """)


class FilterGroup(QWidget):
    changed = pyqtSignal()

    def __init__(self, label, options, parent=None):
        super().__init__(parent)
        self._chips = {}
        self._active = options[0]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel(label)
        lbl.setFixedWidth(52)
        lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:11px; font-weight:600;')
        layout.addWidget(lbl)

        for opt in options:
            chip = FilterChip(opt)
            chip.setChecked(opt == options[0])
            chip.clicked.connect(lambda _, o=opt: self._select(o))
            self._chips[opt] = chip
            layout.addWidget(chip)

        layout.addStretch()

    def _select(self, option):
        self._active = option
        for opt, chip in self._chips.items():
            chip.blockSignals(True)
            chip.setChecked(opt == option)
            chip.blockSignals(False)
            chip._update_style()
        self.changed.emit()

    @property
    def active(self):
        return self._active


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _fmt_amount(val):
    try:
        v = float(val)
    except Exception:
        return '--'
    if v >= 1e8:
        return f'{v / 1e8:.1f}亿'
    if v >= 1e4:
        return f'{v / 1e4:.0f}万'
    return f'{int(v)}'


def _safe(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if f != f else f   # NaN → None
    except Exception:
        return None


def _rank_color(rank: int) -> QColor:
    if rank < 5:   return _QC_RED
    if rank < 10:  return _QC_GOLD
    return _QC_GREEN


# ── 主页面 ────────────────────────────────────────────────────────────────────

class ScreenerPage(QWidget):
    """选股雷达 — A 股市场条件筛选"""
    jump_requested = pyqtSignal(str, str)   # code, name → 跳转 Dashboard

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df_raw   = None
        self._is_demo  = False
        self._fetch_worker = None
        self._init_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel('选股雷达')
        title.setFont(QFont('PingFang SC', 20, QFont.Bold))
        title.setStyleSheet(f'color:{C_TEXT};')
        header.addWidget(title)
        header.addStretch()

        self._status_lbl = QLabel('行情未加载')
        self._status_lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:12px;')
        header.addWidget(self._status_lbl)

        self._refresh_btn = QPushButton('⟳ 刷新行情')
        self._refresh_btn.setFixedHeight(34)
        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background:{C_RED}; color:#fff; border:none;
                border-radius:6px; padding:0 16px;
                font-size:13px; font-weight:600;
            }}
            QPushButton:hover {{ background:{C_RED_HOVER}; }}
            QPushButton:disabled {{ background:{C_BORDER2}; color:{C_TEXT3}; }}
        """)
        self._refresh_btn.clicked.connect(self._start_fetch)
        header.addWidget(self._refresh_btn)
        layout.addLayout(header)

        # 筛选卡片
        filter_card = QFrame()
        filter_card.setObjectName('card')
        filter_card.setStyleSheet(f"""
            QFrame#card {{
                background:{C_SURFACE}; border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)
        fl = QVBoxLayout(filter_card)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(8)

        self._f_chg = FilterGroup('涨跌', ['全部', '上涨', '下跌', '涨停', '跌停'])
        self._f_vol = FilterGroup('量比', ['全部', '>1.5 温和放量', '>2 明显放量', '>3 大幅放量'])
        self._f_to  = FilterGroup('换手', ['全部', '>1%', '>3%', '>5%'])
        self._f_mkt = FilterGroup('板块', ['全部', '沪主板', '深主板', '创业板', '科创板'])
        self._f_srt = FilterGroup('排序', ['涨幅↓', '涨幅↑', '量比↓', '换手↓'])

        for fg in (self._f_chg, self._f_vol, self._f_to, self._f_mkt, self._f_srt):
            fg.changed.connect(self._apply_filters)
            fl.addWidget(fg)

        layout.addWidget(filter_card)

        # 结果表格
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels(
            ['#', '代码', '名称', '最新价', '涨跌幅', '量比', '换手率', '成交额', '操作']
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setFocusPolicy(Qt.NoFocus)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)    # #
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)    # 代码
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)  # 名称 — 填满剩余
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)    # 最新价
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)    # 涨跌幅
        hdr.setSectionResizeMode(5, QHeaderView.Fixed)    # 量比
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)    # 换手率
        hdr.setSectionResizeMode(7, QHeaderView.Fixed)    # 成交额
        hdr.setSectionResizeMode(8, QHeaderView.Fixed)    # 操作
        hdr.setHighlightSections(False)

        self._table.setColumnWidth(0, 44)
        self._table.setColumnWidth(1, 80)
        self._table.setColumnWidth(3, 82)
        self._table.setColumnWidth(4, 92)
        self._table.setColumnWidth(5, 64)
        self._table.setColumnWidth(6, 80)
        self._table.setColumnWidth(7, 92)
        self._table.setColumnWidth(8, 72)

        self._table.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                border: 1px solid {C_BORDER};
                border-radius: 8px;
                font-size: 13px;
                outline: none;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid {C_BORDER};
                padding: 0 8px;
                color: {C_TEXT};
            }}
            QTableWidget::item:hover {{
                background: {C_SURFACE2};
            }}
            QHeaderView::section {{
                background: {C_SURFACE2};
                color: {C_TEXT3};
                border: none;
                border-bottom: 1px solid {C_BORDER2};
                padding: 0 8px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1px;
                height: 32px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {C_BORDER2};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        layout.addWidget(self._table, 1)

        # 初始占位（0行）
        self._table.setRowCount(0)

    # ── 数据拉取 ──────────────────────────────────────────────────────────────

    def refresh(self):
        """切换到本页时调用：首次自动加载，已有数据则复用"""
        if self._df_raw is not None:
            self._apply_filters()
            return
        self._start_fetch()

    def _start_fetch(self):
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText('加载中...')
        self._status_lbl.setText('正在拉取 A 股行情...')

        if self._fetch_worker and self._fetch_worker.isRunning():
            self._fetch_worker.terminate()

        self._fetch_worker = MarketFetchWorker()
        self._fetch_worker.data_ready.connect(self._on_data_ready)
        self._fetch_worker.fetch_error.connect(self._on_fetch_error)
        self._fetch_worker.start()

    def _on_data_ready(self, df, is_demo):
        self._df_raw  = df
        self._is_demo = is_demo
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText('⟳ 刷新行情')
        self._apply_filters()

    def _on_fetch_error(self, msg):
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText('⟳ 刷新行情')
        self._status_lbl.setText(f'获取失败：{msg[:50]}')

    # ── 筛选 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _market_of(code):
        c = str(code)
        if c.startswith('688'): return '科创板'
        if c.startswith('3'):   return '创业板'
        if c.startswith('6'):   return '沪主板'
        return '深主板'

    def _apply_filters(self):
        if self._df_raw is None:
            return

        df = self._df_raw.copy()

        chg = self._f_chg.active
        if chg == '上涨':   df = df[df['pct_chg'] > 0]
        elif chg == '下跌': df = df[df['pct_chg'] < 0]
        elif chg == '涨停': df = df[df['pct_chg'] >= 9.9]
        elif chg == '跌停': df = df[df['pct_chg'] <= -9.9]

        vol_map = {'>1.5 温和放量': 1.5, '>2 明显放量': 2.0, '>3 大幅放量': 3.0}
        vt = vol_map.get(self._f_vol.active)
        if vt and 'vol_ratio' in df.columns:
            df = df[df['vol_ratio'] >= vt]

        to_map = {'>1%': 1.0, '>3%': 3.0, '>5%': 5.0}
        tt = to_map.get(self._f_to.active)
        if tt and 'turnover' in df.columns:
            df = df[df['turnover'] >= tt]

        mkt = self._f_mkt.active
        if mkt != '全部':
            df = df[df['code'].astype(str).apply(self._market_of) == mkt]

        srt_map = {
            '涨幅↓': ('pct_chg', False),
            '涨幅↑': ('pct_chg', True),
            '量比↓': ('vol_ratio', False),
            '换手↓': ('turnover', False),
        }
        col, asc = srt_map.get(self._f_srt.active, ('pct_chg', False))
        if col in df.columns:
            df = df.sort_values(col, ascending=asc, na_position='last')

        total = len(df)
        df = df.head(MAX_DISPLAY).reset_index(drop=True)

        note = '  [演示数据]' if self._is_demo else ''
        self._status_lbl.setText(f'共筛出 {total} 只，显示 {len(df)} 只{note}')
        self._rebuild_rows(df)

    # ── 表格渲染 ──────────────────────────────────────────────────────────────

    def _rebuild_rows(self, df):
        self._table.setUpdatesEnabled(False)
        self._table.clearContents()
        self._table.setRowCount(len(df))

        for i, row in enumerate(df.itertuples(index=False)):
            self._table.setRowHeight(i, 50)

            code  = str(getattr(row, 'code', ''))
            name  = str(getattr(row, 'name', ''))
            price = _safe(getattr(row, 'price', None))
            pct   = _safe(getattr(row, 'pct_chg', None))
            vr    = _safe(getattr(row, 'vol_ratio', None))
            to    = _safe(getattr(row, 'turnover', None))
            amt   = getattr(row, 'amount', None)

            up        = (pct is None or pct >= 0)
            chg_color = _QC_RED if up else _QC_GREEN
            chg_bg    = _QC_RED_BG if up else _QC_GREEN_BG
            rc        = _rank_color(i)

            mono11 = QFont('Menlo', 11)
            mono12b = QFont('Menlo', 12, QFont.Bold)
            mono11b = QFont('Menlo', 11, QFont.Bold)

            def item(text, align=Qt.AlignVCenter | Qt.AlignLeft, fg=None, bg=None, font=None):
                it = QTableWidgetItem(text)
                it.setTextAlignment(align)
                if fg:   it.setForeground(QBrush(fg))
                if bg:   it.setBackground(QBrush(bg))
                if font: it.setFont(font)
                return it

            center = Qt.AlignVCenter | Qt.AlignCenter
            right  = Qt.AlignVCenter | Qt.AlignRight

            # 0 排名
            self._table.setItem(i, 0, item(f'#{i+1}', center, rc, font=QFont('Menlo', 10, QFont.Bold)))

            # 1 代码
            self._table.setItem(i, 1, item(code, Qt.AlignVCenter | Qt.AlignLeft, font=mono11))

            # 2 名称（Stretch）
            self._table.setItem(i, 2, item(name, Qt.AlignVCenter | Qt.AlignLeft, _QC_TEXT2))

            # 3 最新价
            p_text = f'{price:.2f}' if price else '--'
            self._table.setItem(i, 3, item(p_text, right, chg_color, font=mono12b))

            # 4 涨跌幅（带背景色）
            if pct is not None:
                pct_text = f'+{pct:.2f}%' if pct >= 0 else f'{pct:.2f}%'
            else:
                pct_text = '--'
            self._table.setItem(i, 4, item(pct_text, center, chg_color, chg_bg, mono11b))

            # 5 量比
            vr_color = _QC_RED if (vr is not None and vr > 2) else _QC_TEXT2
            self._table.setItem(i, 5, item(f'{vr:.2f}' if vr is not None else '--', center, vr_color, font=mono11))

            # 6 换手率
            self._table.setItem(i, 6, item(f'{to:.2f}%' if to is not None else '--', center, _QC_TEXT2, font=mono11))

            # 7 成交额
            self._table.setItem(i, 7, item(_fmt_amount(amt), center, _QC_TEXT2, font=mono11))

            # 8 操作（按钮）
            btn_w = QWidget()
            btn_w.setStyleSheet('background:transparent;')
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(8, 8, 8, 8)
            btn = QPushButton('预测')
            btn.setFixedSize(52, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:transparent; color:{C_TEXT3};
                    border:1px solid {C_BORDER2}; border-radius:4px; font-size:12px;
                }}
                QPushButton:hover {{ color:{C_RED}; border-color:{C_RED}; }}
            """)
            btn.clicked.connect(lambda _, c=code, n=name: self.jump_requested.emit(c, n))
            btn_l.addWidget(btn)
            self._table.setCellWidget(i, 8, btn_w)

        self._table.setUpdatesEnabled(True)

    def closeEvent(self, event):
        if self._fetch_worker and self._fetch_worker.isRunning():
            self._fetch_worker.terminate()
            self._fetch_worker.wait()
        super().closeEvent(event)
