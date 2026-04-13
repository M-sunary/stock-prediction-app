"""
图标导航栏 - 左侧64px宽的图标按钮导航
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ..styles.theme import C_BG, C_SURFACE, C_BORDER2, C_RED, C_RED_GLOW, C_TEXT2, C_TEXT3


PAGES = [
    ('◈', '预测看板', 'dashboard'),
    ('★', '自选股', 'watchlist'),
    ('⟲', '回测中心', 'backtest'),
    ('⊞', '因子分析', 'factor'),
    ('◎', '新闻情感', 'news'),
    ('⊛', '选股雷达', 'screener'),
]


class NavButton(QPushButton):
    def __init__(self, icon: str, tip: str, page_id: str, parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self.setFixedSize(44, 44)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tip)
        self.setText(icon)
        self.setFont(QFont('Arial', 16))
        self._badge_lbl = None
        self._active = False
        self._update_style()

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def set_badge(self, count: int):
        if self._badge_lbl is None:
            self._badge_lbl = QLabel(self.parent())
            self._badge_lbl.setFixedSize(16, 16)
            self._badge_lbl.setAlignment(Qt.AlignCenter)
            self._badge_lbl.setStyleSheet(f"""
                QLabel {{
                    background: {C_RED};
                    color: white;
                    border-radius: 8px;
                    font-size: 9px;
                    font-weight: 700;
                }}
            """)
        self._badge_lbl.setText(str(count))
        self._badge_lbl.move(self.x() + 26, self.y() + 4)
        self._badge_lbl.setVisible(count > 0)

    def _update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {C_RED_GLOW};
                    color: {C_RED};
                    border: none;
                    border-radius: 10px;
                    border-left: 3px solid {C_RED};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C_TEXT3};
                    border: none;
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,0.05);
                    color: {C_TEXT2};
                }}
            """)


class IconRail(QWidget):
    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(64)
        self.setObjectName('iconrail')
        self._buttons = {}
        self._current = 'dashboard'
        self._init_ui()
        self._set_active('dashboard')

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)

        for icon, tip, page_id in PAGES:
            btn = NavButton(icon, tip, page_id, self)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_click(pid))
            self._buttons[page_id] = btn
            layout.addWidget(btn, 0, Qt.AlignHCenter)

        layout.addStretch()

        # 底部设置按钮
        settings_btn = NavButton('⊙', '设置', 'settings', self)
        settings_btn.clicked.connect(lambda: self._on_click('settings'))
        self._buttons['settings'] = settings_btn
        layout.addWidget(settings_btn, 0, Qt.AlignHCenter)

        self.setStyleSheet(f"""
            QWidget#iconrail {{
                background: {C_SURFACE};
                border-right: 1px solid {C_BORDER2};
            }}
        """)

    def _on_click(self, page_id: str):
        if page_id == 'settings':
            self.page_changed.emit('settings')
            return
        self._set_active(page_id)
        self.page_changed.emit(page_id)

    def _set_active(self, page_id: str):
        for pid, btn in self._buttons.items():
            btn.set_active(pid == page_id)
        self._current = page_id

    def set_watchlist_count(self, count: int):
        if 'watchlist' in self._buttons:
            self._buttons['watchlist'].set_badge(count)
