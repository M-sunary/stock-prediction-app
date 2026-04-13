"""
风险因子面板 + 预测历史表格
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
from ..styles.theme import (
    C_SURFACE, C_BORDER, C_RED, C_GREEN, C_GOLD,
    C_TEXT, C_TEXT2, C_TEXT3
)


class RiskFactorRow(QFrame):
    def __init__(self, name: str, value: int, label: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        name_lbl = QLabel(name)
        name_lbl.setFixedWidth(110)
        name_lbl.setStyleSheet(f'color:{C_TEXT2}; font-size:12px;')

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(value)
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        color = C_GREEN if value <= 30 else (C_GOLD if value <= 60 else C_RED)
        bar.setStyleSheet(f"""
            QProgressBar {{ background:#1e2030; border-radius:3px; border:none; }}
            QProgressBar::chunk {{ background:{color}; border-radius:3px; }}
        """)

        val_lbl = QLabel(f'{value}%')
        val_lbl.setFixedWidth(32)
        val_lbl.setFont(QFont('Menlo', 11))
        val_lbl.setStyleSheet(f'color:{C_TEXT}; font-size:11px;')

        risk_lbl = QLabel(label)
        risk_lbl.setFixedSize(28, 16)
        risk_lbl.setAlignment(Qt.AlignCenter)
        risk_lbl.setStyleSheet(f"""
            QLabel {{
                background: {color}22;
                color: {color};
                border-radius: 8px;
                font-size: 10px;
            }}
        """)

        layout.addWidget(name_lbl)
        layout.addWidget(bar)
        layout.addWidget(val_lbl)
        layout.addWidget(risk_lbl)

        self.setStyleSheet(f'QFrame {{ border-bottom:1px solid {C_BORDER}; }}')


class RiskFactorsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self._init_ui()

    def _init_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 12, 0, 4)
        self._layout.setSpacing(0)

        header = QLabel('RISK FACTORS · 风险因子')
        header.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; padding:0 16px 8px 16px;')
        self._layout.addWidget(header)

        self._rows_container = QVBoxLayout()
        self._rows_container.setSpacing(0)
        self._layout.addLayout(self._rows_container)
        self._layout.addStretch()

        self.setStyleSheet(f"""
            QFrame#card {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

    def update_risks(self, factors: list):
        while self._rows_container.count():
            item = self._rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for f in factors:
            row = RiskFactorRow(f['name'], f['value'], f['label'])
            self._rows_container.addWidget(row)


class PredictionHistoryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QLabel('HISTORY · 近期预测记录')
        header.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px;')
        layout.addWidget(header)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(['日期', '预测概率', '预测方向', '实际结果', ''])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.NoSelection)
        self._table.setFixedHeight(240)
        self._table.setAlternatingRowColors(False)
        self._table.setShowGrid(False)

        self._table.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                border: none;
                font-size: 12px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid {C_BORDER};
                padding: 4px 6px;
                color: {C_TEXT};
            }}
            QHeaderView::section {{
                background: transparent;
                color: {C_TEXT3};
                border: none;
                border-bottom: 1px solid {C_BORDER};
                padding: 4px 6px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
        """)
        layout.addWidget(self._table)

        self.setStyleSheet(f"""
            QFrame#card {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

    def update_history(self, history: list):
        # 如果空，显示默认数据
        if not history:
            history = [
                {'date': '06-11', 'probability': 72, 'direction': '看多', 'actual_result': '红盘 +1.28%', 'correct': True},
                {'date': '06-10', 'probability': 61, 'direction': '看多', 'actual_result': '绿盘 -0.35%', 'correct': False},
                {'date': '06-09', 'probability': 58, 'direction': '看多', 'actual_result': '红盘 +0.91%', 'correct': True},
                {'date': '06-06', 'probability': 44, 'direction': '看空', 'actual_result': '绿盘 -0.72%', 'correct': True},
                {'date': '06-05', 'probability': 67, 'direction': '看多', 'actual_result': '红盘 +1.83%', 'correct': True},
            ]

        self._table.setRowCount(len(history))
        for row, h in enumerate(history):
            self._table.setRowHeight(row, 36)
            date_item = QTableWidgetItem(str(h.get('date', ''))[:5])
            date_item.setFont(QFont('Menlo', 11))
            self._table.setItem(row, 0, date_item)

            prob = h.get('probability', 0)
            prob_item = QTableWidgetItem(f"{prob:.0f}%" if isinstance(prob, float) else f"{prob}%")
            prob_item.setFont(QFont('Menlo', 11))
            prob_color = QColor(C_GREEN if prob >= 65 else (C_GOLD if prob >= 50 else C_RED))
            prob_item.setForeground(QBrush(prob_color))
            self._table.setItem(row, 1, prob_item)

            direction = h.get('direction', '--')
            dir_item = QTableWidgetItem(direction)
            dir_color = QColor(C_RED if direction == '看多' else C_GREEN)
            dir_item.setForeground(QBrush(dir_color))
            self._table.setItem(row, 2, dir_item)

            actual = h.get('actual_result', '--')
            act_item = QTableWidgetItem(actual)
            if actual and '+' in str(actual):
                act_item.setForeground(QBrush(QColor(C_RED)))
            elif actual and '-' in str(actual):
                act_item.setForeground(QBrush(QColor(C_GREEN)))
            self._table.setItem(row, 3, act_item)

            correct = h.get('correct')
            if correct is True:
                correct_item = QTableWidgetItem('✓')
                correct_item.setForeground(QBrush(QColor(C_GREEN)))
            elif correct is False:
                correct_item = QTableWidgetItem('✗')
                correct_item.setForeground(QBrush(QColor(C_RED)))
            else:
                correct_item = QTableWidgetItem('--')
                correct_item.setForeground(QBrush(QColor(C_TEXT3)))
            correct_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 4, correct_item)
