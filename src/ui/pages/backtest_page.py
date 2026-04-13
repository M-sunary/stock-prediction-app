"""
回测中心页面 - 预测历史统计 + 模拟收益曲线
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush

from ..styles.theme import (
    C_SURFACE, C_BORDER, C_RED, C_GREEN, C_GOLD, C_BLUE,
    C_TEXT, C_TEXT2, C_TEXT3, C_BG
)
from ...core.config_manager import get_config
from ...data.cache_manager import get_cache
from ...data.demo_data import get_stock_params, generate_prediction_history


class StatTile(QFrame):
    """统计数字磁贴"""
    def __init__(self, label: str, value: str = '--', color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName('stat_tile')
        self.setFixedHeight(80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self._val_lbl = QLabel(value)
        self._val_lbl.setFont(QFont('Menlo', 22, QFont.Bold))
        self._val_lbl.setAlignment(Qt.AlignCenter)
        self._val_lbl.setStyleSheet(f'color:{color or C_TEXT}; background:transparent;')

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:11px; background:transparent;')

        layout.addWidget(self._val_lbl)
        layout.addWidget(lbl)
        self.setStyleSheet(f"""
            QFrame#stat_tile {{
                background:{C_SURFACE};
                border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)

    def set_value(self, value: str, color: str = None):
        self._val_lbl.setText(value)
        if color:
            self._val_lbl.setStyleSheet(f'color:{color}; font-size:22px; font-weight:700; background:transparent;')


class EquityCurveChart(QFrame):
    """模拟收益曲线（QPainter 手绘折线图）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self.setMinimumHeight(200)
        self._values = []
        self.setStyleSheet(f"""
            QFrame#card {{
                background:{C_SURFACE};
                border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)

    def set_data(self, values: list):
        self._values = values
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            w, h = self.width(), self.height()
            pad_l, pad_r, pad_t, pad_b = 52, 16, 24, 32

            # 标题
            painter.setPen(QPen(QColor(C_TEXT3)))
            painter.setFont(QFont('Arial', 9))
            painter.drawText(pad_l, 14, 'EQUITY CURVE · 模拟收益曲线')

            vals = self._values
            if len(vals) < 2:
                painter.setPen(QPen(QColor(C_TEXT3)))
                painter.setFont(QFont('PingFang SC', 12))
                painter.drawText(0, 0, w, h, Qt.AlignCenter, '运行预测后查看收益曲线')
                return

            vmin, vmax = min(vals), max(vals)
            vrange = (vmax - vmin) or 1

            def to_xy(i, val):
                x = pad_l + (i / (len(vals) - 1)) * (w - pad_l - pad_r)
                y = pad_t + (1 - (val - vmin) / vrange) * (h - pad_t - pad_b)
                return x, y

            # 基准线（100 起点）
            base_y = pad_t + (1 - (100 - vmin) / vrange) * (h - pad_t - pad_b)
            painter.setPen(QPen(QColor(C_TEXT3), 1, Qt.DashLine))
            painter.drawLine(int(pad_l), int(base_y), int(w - pad_r), int(base_y))

            # 填充区域
            final_color = C_GREEN if vals[-1] >= 100 else C_RED
            fill_color = QColor(final_color)
            fill_color.setAlpha(30)
            xs = [to_xy(i, vals[i])[0] for i in range(len(vals))]
            ys = [to_xy(i, vals[i])[1] for i in range(len(vals))]

            from PyQt5.QtGui import QPainterPath
            path = QPainterPath()
            path.moveTo(xs[0], h - pad_b)
            path.lineTo(xs[0], ys[0])
            for i in range(1, len(vals)):
                path.lineTo(xs[i], ys[i])
            path.lineTo(xs[-1], h - pad_b)
            path.closeSubpath()
            painter.fillPath(path, QBrush(fill_color))

            # 折线
            painter.setPen(QPen(QColor(final_color), 2))
            for i in range(1, len(vals)):
                x0, y0 = to_xy(i - 1, vals[i - 1])
                x1, y1 = to_xy(i, vals[i])
                painter.drawLine(int(x0), int(y0), int(x1), int(y1))

            # Y 轴标签
            painter.setPen(QPen(QColor(C_TEXT3)))
            painter.setFont(QFont('Menlo', 8))
            for lv in [vmin, (vmin + vmax) / 2, vmax]:
                _, y = to_xy(0, lv)
                painter.drawText(2, int(y) - 6, int(pad_l) - 6, 14,
                                 Qt.AlignRight | Qt.AlignVCenter, f'{lv:.1f}')

            # X 轴标签（首尾）
            painter.drawText(int(xs[0]) - 10, h - 4, '起始')
            painter.drawText(int(xs[-1]) - 20, h - 4, '最新')

        finally:
            painter.end()


class BacktestPage(QWidget):
    """回测中心页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = get_config()
        self._cache = get_cache()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── 标题栏 ─────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel('回测中心')
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

        # ── 统计磁贴 ───────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._tile_total = StatTile('总预测次数')
        self._tile_wins = StatTile('胜', color=C_GREEN)
        self._tile_losses = StatTile('负', color=C_RED)
        self._tile_acc = StatTile('准确率', color=C_GOLD)
        for tile in [self._tile_total, self._tile_wins, self._tile_losses, self._tile_acc]:
            stats_row.addWidget(tile)
        layout.addLayout(stats_row)

        # ── 曲线 + 历史表 ──────────────────────────────────────────────────
        row = QHBoxLayout()
        row.setSpacing(16)

        self._equity_chart = EquityCurveChart()
        self._equity_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._equity_chart.setMinimumHeight(240)
        row.addWidget(self._equity_chart, 3)

        # 历史表
        hist_card = QFrame()
        hist_card.setObjectName('card')
        hist_card.setStyleSheet(f"""
            QFrame#card {{
                background:{C_SURFACE};
                border:1px solid {C_BORDER};
                border-radius:8px;
            }}
        """)
        hist_layout = QVBoxLayout(hist_card)
        hist_layout.setContentsMargins(0, 12, 0, 0)
        hist_layout.setSpacing(0)
        hist_hdr = QLabel('PREDICTION LOG · 预测记录')
        hist_hdr.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; padding:0 16px 8px 16px;')
        hist_layout.addWidget(hist_hdr)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(['日期', '概率', '方向', '实际', '✓'])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.NoSelection)
        self._table.setShowGrid(False)
        self._table.setStyleSheet(f"""
            QTableWidget {{ background:transparent; border:none; font-size:12px; }}
            QTableWidget::item {{ border-bottom:1px solid {C_BORDER}; padding:4px 6px; color:{C_TEXT}; }}
            QHeaderView::section {{
                background:transparent; color:{C_TEXT3}; border:none;
                border-bottom:1px solid {C_BORDER}; padding:4px 6px;
                font-size:10px; font-weight:600; letter-spacing:1px;
            }}
        """)
        hist_layout.addWidget(self._table)
        row.addWidget(hist_card, 2)
        layout.addLayout(row)
        layout.addStretch()

        self._refresh_selector()

    def _refresh_selector(self):
        self._selector.blockSignals(True)
        prev = self._selector.currentText()[:6] if self._selector.currentText() else ''
        self._selector.clear()
        for code in self._config.watchlist:
            params = get_stock_params(code)
            name = params.get('name', code) if params.get('name') != code else code
            self._selector.addItem(f'{code}  {name}', code)
        # 恢复之前选中的股票
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
        self._refresh_selector()
        # 同步 selector
        for i in range(self._selector.count()):
            if self._selector.itemData(i) == code:
                self._selector.blockSignals(True)
                self._selector.setCurrentIndex(i)
                self._selector.blockSignals(False)
                break

        history = self._cache.get_prediction_history(code, limit=60)
        if not history:
            history = generate_prediction_history(code)

        accuracy = self._cache.get_accuracy_stats(code, days=60)
        if not accuracy.get('wins') and not accuracy.get('losses'):
            wins = sum(1 for h in history if h.get('correct'))
            losses = len(history) - wins
            accuracy = {
                'wins': wins, 'losses': losses,
                'accuracy': wins / len(history) if history else 0
            }

        total = len(history)
        wins = accuracy.get('wins', 0)
        losses = accuracy.get('losses', 0)
        acc = accuracy.get('accuracy', 0) * 100

        self._tile_total.set_value(str(total))
        self._tile_wins.set_value(str(wins), C_GREEN)
        self._tile_losses.set_value(str(losses), C_RED)
        self._tile_acc.set_value(f'{acc:.1f}%', C_GREEN if acc >= 55 else C_GOLD)

        self._update_table(history)
        self._update_equity(history)

    def _update_table(self, history: list):
        self._table.setRowCount(len(history))
        for row, h in enumerate(history):
            self._table.setRowHeight(row, 34)

            date_item = QTableWidgetItem(str(h.get('date', ''))[:5])
            date_item.setFont(QFont('Menlo', 10))
            self._table.setItem(row, 0, date_item)

            prob = h.get('probability', 0)
            prob_item = QTableWidgetItem(f"{prob:.0f}%")
            prob_item.setFont(QFont('Menlo', 10))
            prob_item.setForeground(QBrush(QColor(
                C_GREEN if prob >= 65 else (C_GOLD if prob >= 50 else C_RED)
            )))
            self._table.setItem(row, 1, prob_item)

            direction = h.get('direction', '--')
            dir_item = QTableWidgetItem(direction)
            dir_item.setForeground(QBrush(QColor(C_RED if direction == '看多' else C_GREEN)))
            self._table.setItem(row, 2, dir_item)

            actual = h.get('actual_result', '--') or '--'
            act_item = QTableWidgetItem(actual)
            if '+' in str(actual):
                act_item.setForeground(QBrush(QColor(C_RED)))
            elif '-' in str(actual):
                act_item.setForeground(QBrush(QColor(C_GREEN)))
            self._table.setItem(row, 3, act_item)

            correct = h.get('correct')
            mark = '✓' if correct is True else ('✗' if correct is False else '--')
            c_item = QTableWidgetItem(mark)
            c_item.setTextAlignment(Qt.AlignCenter)
            c_item.setForeground(QBrush(QColor(
                C_GREEN if correct is True else (C_RED if correct is False else C_TEXT3)
            )))
            self._table.setItem(row, 4, c_item)

    def _update_equity(self, history: list):
        """从最老到最新模拟累计收益（从100起）"""
        ordered = list(reversed(history))
        equity = [100.0]
        for h in ordered:
            pct = h.get('actual_pct')
            correct = h.get('correct')
            if pct is None:
                # 无验证数据，用 ±1% 代替
                delta = 1.0 if correct else -1.0
            else:
                delta = abs(float(pct)) if correct else -abs(float(pct))
            equity.append(equity[-1] + delta)
        self._equity_chart.set_data(equity)
