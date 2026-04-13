"""
预测仪表盘主组件 - 概率表盘 + 分模型得分 + 关键信号
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from ..styles.theme import (
    C_SURFACE, C_BORDER, C_BORDER2,
    C_RED, C_GREEN, C_GOLD,
    C_TEXT, C_TEXT2, C_TEXT3
)


class GaugeWidget(QWidget):
    """半圆仪表盘 - QPainter 绘制"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 130)
        self._target = 50.0
        self._display_value = 50.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate_step)

    def set_value(self, pct: float, animate: bool = True):
        self._target = max(0.0, min(100.0, float(pct)))
        if animate:
            self._timer.start(16)
        else:
            self._display_value = self._target
            self.update()

    def _animate_step(self):
        diff = self._target - self._display_value
        if abs(diff) < 0.5:
            self._display_value = self._target
            self._timer.stop()
        else:
            self._display_value += diff * 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx = w // 2
        cy = h - 18           # 圆心在底部留边距
        r = min(cx - 10, cy - 10)  # 半径
        lw = 14               # 线宽

        # Qt drawArc: 角度单位是 1/16°, 从3点钟方向逆时针
        # 半圆：从左端（180°）到右端（0°），顺时针 = -180 * 16
        start = 180 * 16     # 左端（9点钟方向）
        full = -180 * 16     # 顺时针半圆

        rect_x = cx - r
        rect_y = cy - r
        rect_w = r * 2
        rect_h = r * 2

        # ── 轨道背景（深灰色）─────────────────────────────────────────────
        pen = QPen(QColor('#252840'), lw, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(rect_x, rect_y, rect_w, rect_h, start, full)

        # ── 彩色进度弧（红→金→绿）─────────────────────────────────────────
        pct = max(0.0, min(1.0, self._display_value / 100.0))
        if pct > 0.005:
            if pct <= 0.5:
                t = pct * 2
                c = self._lerp_color((240, 62, 62), (232, 168, 56), t)
            else:
                t = (pct - 0.5) * 2
                c = self._lerp_color((232, 168, 56), (32, 201, 132), t)
            arc_color = QColor(*c)
            pen2 = QPen(arc_color, lw, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen2)
            painter.drawArc(rect_x, rect_y, rect_w, rect_h,
                            start, int(full * pct))

        # ── 数值文字 ────────────────────────────────────────────────────────
        v = self._display_value
        if v >= 65:
            text_color = QColor(C_GREEN)
        elif v >= 50:
            text_color = QColor(C_GOLD)
        else:
            text_color = QColor(C_RED)

        painter.setPen(QPen(text_color))
        painter.setFont(QFont('Menlo', 24, QFont.Bold))
        # 文字居中在圆心附近
        painter.drawText(0, cy - 40, w, 40,
                         Qt.AlignHCenter | Qt.AlignBottom,
                         f'{v:.0f}%')
        painter.end()

    @staticmethod
    def _lerp_color(c1, c2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


class ModelScoreBar(QFrame):
    """单个模型分数条"""
    def __init__(self, name: str, score: float, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet('QFrame { background: transparent; border: none; }')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        name_lbl = QLabel(name)
        name_lbl.setFixedWidth(72)
        name_lbl.setStyleSheet(f'color:{C_TEXT2}; font-size:12px; background:transparent;')

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(int(score))
        self._bar.setFixedHeight(5)
        self._bar.setTextVisible(False)
        self._set_bar_color(score)

        self._score_lbl = QLabel(f'{score:.0f}%')
        self._score_lbl.setFixedWidth(32)
        self._score_lbl.setFont(QFont('Menlo', 11))
        self._score_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._set_score_color(score)

        layout.addWidget(name_lbl)
        layout.addWidget(self._bar)
        layout.addWidget(self._score_lbl)

    def _color_for(self, score):
        return C_GREEN if score >= 65 else (C_GOLD if score >= 50 else C_RED)

    def _set_bar_color(self, score):
        color = self._color_for(score)
        self._bar.setStyleSheet(f"""
            QProgressBar {{ background:#252840; border-radius:2px; border:none; }}
            QProgressBar::chunk {{ background:{color}; border-radius:2px; }}
        """)

    def _set_score_color(self, score):
        color = self._color_for(score)
        self._score_lbl.setStyleSheet(f'color:{color}; font-family:Menlo; font-size:11px; background:transparent;')

    def update_score(self, score: float):
        self._bar.setValue(int(score))
        self._set_bar_color(score)
        self._score_lbl.setText(f'{score:.0f}%')
        self._set_score_color(score)


class SignalTag(QFrame):
    """单行信号标签（多头/空头/中性 + 描述文字）"""
    def __init__(self, tag: str, text: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.setStyleSheet('QFrame { background: transparent; border: none; }')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        if tag == 'bull':
            bg, fg, label = '#20c98428', C_GREEN, '多头'
        elif tag == 'bear':
            bg, fg, label = '#f03e3e28', C_RED, '空头'
        else:
            bg, fg, label = '#ffffff15', C_TEXT3, '中性'

        badge = QLabel(label)
        badge.setFixedSize(34, 18)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border-radius: 9px;
                font-size: 10px;
                font-weight: 600;
            }}
        """)

        desc = QLabel(text)
        desc.setStyleSheet(f'color:{C_TEXT2}; font-size:12px; background:transparent;')

        layout.addWidget(badge)
        layout.addWidget(desc)
        layout.addStretch()


class PredictionHero(QFrame):
    """预测英雄区 - 3 列等宽"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('hero_card')
        self.setMinimumHeight(220)
        self._score_bars = {}
        self._signal_widgets = []
        self._init_ui()
        self._init_style()

    def _init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 列1：概率表盘 ─────────────────────────────────────────────────
        col1 = QWidget()
        col1.setStyleSheet('background:transparent;')
        l1 = QVBoxLayout(col1)
        l1.setContentsMargins(20, 16, 20, 16)
        l1.setSpacing(4)
        l1.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self._gauge = GaugeWidget()

        lbl_title = QLabel('次日红盘概率')
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f'color:{C_TEXT2}; font-size:12px; background:transparent;')

        lbl_sub = QLabel('集成模型预测')
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet(f'color:{C_TEXT3}; font-size:11px; background:transparent;')

        self._update_time = QLabel('更新于 --')
        self._update_time.setAlignment(Qt.AlignCenter)
        self._update_time.setStyleSheet(f'color:{C_TEXT3}; font-size:11px; font-family:Menlo; background:transparent;')

        l1.addWidget(self._gauge, 0, Qt.AlignHCenter)
        l1.addWidget(lbl_title)
        l1.addWidget(lbl_sub)
        l1.addSpacing(4)
        l1.addWidget(self._update_time)

        # ── 分割线 ─────────────────────────────────────────────────────────
        div1 = self._make_divider()

        # ── 列2：分模型得分 ────────────────────────────────────────────────
        col2 = QWidget()
        col2.setStyleSheet('background:transparent;')
        l2 = QVBoxLayout(col2)
        l2.setContentsMargins(16, 16, 16, 16)
        l2.setSpacing(10)

        h2 = QLabel('分模型得分')
        h2.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; background:transparent;')
        l2.addWidget(h2)

        for name, score in [('XGBoost', 50), ('LightGBM', 50), ('LogReg', 50), ('集成', 50)]:
            bar = ModelScoreBar(name, score)
            l2.addWidget(bar)
            self._score_bars[name] = bar

        l2.addStretch()
        self._accuracy_lbl = QLabel('历史准确率：近30天 --')
        self._accuracy_lbl.setStyleSheet(f'color:{C_TEXT3}; font-size:11px; background:transparent;')
        l2.addWidget(self._accuracy_lbl)

        # ── 分割线 ─────────────────────────────────────────────────────────
        div2 = self._make_divider()

        # ── 列3：关键信号 ──────────────────────────────────────────────────
        col3 = QWidget()
        col3.setStyleSheet('background:transparent;')
        self._col3_layout = QVBoxLayout(col3)
        self._col3_layout.setContentsMargins(16, 16, 16, 16)
        self._col3_layout.setSpacing(6)

        h3 = QLabel('关键信号')
        h3.setStyleSheet(f'color:{C_TEXT3}; font-size:10px; font-weight:600; letter-spacing:1.5px; background:transparent;')
        self._col3_layout.addWidget(h3)
        self._col3_layout.addStretch()

        root.addWidget(col1, 1)
        root.addWidget(div1)
        root.addWidget(col2, 1)
        root.addWidget(div2)
        root.addWidget(col3, 1)

    def _make_divider(self):
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setFixedWidth(1)
        div.setStyleSheet(f'background:{C_BORDER2}; border:none;')
        return div

    def _init_style(self):
        self.setStyleSheet(f"""
            QFrame#hero_card {{
                background: {C_SURFACE};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
            }}
        """)

    def update_prediction(self, prediction: dict, signals: list,
                          accuracy: dict, update_time: str = ''):
        prob = float(prediction.get('probability', 50))
        xgb = float(prediction.get('xgboost', 50))
        lgb = float(prediction.get('lightgbm', 50))

        # 表盘动画
        self._gauge.set_value(prob)

        if update_time:
            self._update_time.setText(f'更新于 {update_time}')

        # 分模型分数条
        if 'XGBoost' in self._score_bars:
            self._score_bars['XGBoost'].update_score(xgb)
        if 'LightGBM' in self._score_bars:
            self._score_bars['LightGBM'].update_score(lgb)
        logreg = float(prediction.get('logreg', 50))
        if 'LogReg' in self._score_bars:
            self._score_bars['LogReg'].update_score(logreg)
        if '集成' in self._score_bars:
            self._score_bars['集成'].update_score(prob)

        # 准确率
        acc = accuracy.get('accuracy', 0) * 100
        wins = accuracy.get('wins', 0)
        losses = accuracy.get('losses', 0)
        self._accuracy_lbl.setText(f'历史准确率 {acc:.1f}%  {wins}胜/{losses}负')

        # 信号列表
        self._refresh_signals(signals)

    def _refresh_signals(self, signals: list):
        """移除旧信号，插入新信号（保留 header[0] 和 stretch[last]）"""
        layout = self._col3_layout
        # 移除中间的 SignalTag widgets（保留 index=0 的 header 和最后的 stretch）
        while layout.count() > 2:
            item = layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for i, sig in enumerate(signals[:6]):
            tag = SignalTag(sig.get('tag', 'neut'), sig.get('text', ''))
            layout.insertWidget(i + 1, tag)
