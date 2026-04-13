"""
暗黑主题样式系统
严格按照设计文档的色彩规范实现
"""

# ── 色彩系统 ──────────────────────────────────────────────────────────────────
COLORS = {
    'bg':          '#08090d',
    'surface':     '#0f1117',
    'surface2':    '#161820',
    'border':      'rgba(255,255,255,0.06)',
    'border2':     'rgba(255,255,255,0.12)',
    'red':         '#f03e3e',
    'red_glow':    'rgba(240,62,62,0.15)',
    'green':       '#20c984',
    'green_glow':  'rgba(32,201,132,0.15)',
    'gold':        '#e8a838',
    'gold_glow':   'rgba(232,168,56,0.15)',
    'blue':        '#4a9eff',
    'blue_glow':   'rgba(74,158,255,0.12)',
    'text':        '#e8eaf0',
    'text2':       '#8b8fa8',
    'text3':       '#4a4e68',
}

# Qt 中不支持 rgba()，使用 QColor 等效值
# border:   rgba(255,255,255,0.06) → QColor(255,255,255,15)
# border2:  rgba(255,255,255,0.12) → QColor(255,255,255,31)
C_BG          = '#08090d'
C_SURFACE     = '#0f1117'
C_SURFACE2    = '#161820'
C_BORDER      = '#1a1b23'       # border 近似值
C_BORDER2     = '#252733'       # border2 近似值
C_RED         = '#f03e3e'
C_RED_HOVER   = '#d63232'
C_RED_GLOW    = '#1a0808'       # 深红背景用于高亮行
C_GREEN       = '#20c984'
C_GREEN_GLOW  = '#0a1f15'
C_GOLD        = '#e8a838'
C_GOLD_GLOW   = '#1f1708'
C_BLUE        = '#4a9eff'
C_TEXT        = '#e8eaf0'
C_TEXT2       = '#8b8fa8'
C_TEXT3       = '#4a4e68'

SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background: {C_BG};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER2};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C_TEXT3};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {C_BG};
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {C_BORDER2};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""

TOOLTIP_STYLE = f"""
QToolTip {{
    background: {C_SURFACE2};
    color: {C_TEXT};
    border: 1px solid {C_BORDER2};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""

APP_STYLE = f"""
/* ── 全局 ── */
QWidget {{
    background-color: {C_BG};
    color: {C_TEXT};
    font-family: "PingFang SC", "Helvetica Neue", Arial;
    font-size: 13px;
    selection-background-color: {C_RED};
    selection-color: white;
}}

/* ── 通用 Panel/Card ── */
QFrame#card {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
}}

QFrame#card2 {{
    background: {C_SURFACE2};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
}}

/* ── 按钮 ── */
QPushButton {{
    background: transparent;
    color: {C_TEXT2};
    border: 1px solid {C_BORDER2};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
}}
QPushButton:hover {{
    border-color: {C_TEXT3};
    color: {C_TEXT};
}}
QPushButton#btnPrimary {{
    background: {C_RED};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#btnPrimary:hover {{
    background: {C_RED_HOVER};
}}
QPushButton#btnPrimary:pressed {{
    background: #b82b2b;
}}

/* ── 搜索框 ── */
QLineEdit {{
    background: {C_SURFACE2};
    color: {C_TEXT};
    border: 1px solid {C_BORDER2};
    border-radius: 6px;
    padding: 6px 12px;
    font-family: "Menlo", "Monaco";
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {C_RED};
}}
QLineEdit::placeholder {{
    color: {C_TEXT3};
}}

/* ── 下拉框 ── */
QComboBox {{
    background: {C_SURFACE2};
    color: {C_TEXT};
    border: 1px solid {C_BORDER2};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
}}
QComboBox:hover {{
    border-color: {C_TEXT3};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {C_SURFACE2};
    color: {C_TEXT};
    border: 1px solid {C_BORDER2};
    selection-background-color: {C_RED_GLOW};
    selection-color: {C_TEXT};
    outline: none;
}}

/* ── 表格 ── */
QTableWidget {{
    background: transparent;
    border: none;
    gridline-color: {C_BORDER};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {C_BORDER};
}}
QTableWidget::item:selected {{
    background: {C_RED_GLOW};
    color: {C_TEXT};
}}
QHeaderView::section {{
    background: {C_SURFACE2};
    color: {C_TEXT3};
    border: none;
    border-bottom: 1px solid {C_BORDER2};
    padding: 6px 8px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── 标签 ── */
QLabel {{
    background: transparent;
    color: {C_TEXT};
}}
QLabel#labelMuted {{
    color: {C_TEXT2};
    font-size: 12px;
}}
QLabel#labelTitle {{
    color: {C_TEXT3};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
}}

/* ── 切换开关（QCheckBox 模拟）── */
QCheckBox {{
    color: {C_TEXT2};
    font-size: 13px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 36px;
    height: 20px;
    border-radius: 10px;
    background: {C_SURFACE2};
    border: 1px solid {C_BORDER2};
}}
QCheckBox::indicator:checked {{
    background: {C_RED};
    border-color: {C_RED};
}}

/* ── 分割线 ── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {C_BORDER};
}}

/* ── 滚动条 ── */
{SCROLLBAR_STYLE}

/* ── Tooltip ── */
{TOOLTIP_STYLE}
"""
