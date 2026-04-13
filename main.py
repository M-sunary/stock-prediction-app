#!/usr/bin/env python3
"""
量策 AI · 次日红盘预测系统
Desktop Application Entry Point
"""
import sys
import os

# ── 绕过系统代理（避免 AKShare 被代理拦截）────────────────────────────────
# 必须在任何 requests/httpx 导入之前执行
for _k in ['https_proxy', 'HTTPS_PROXY', 'http_proxy', 'HTTP_PROXY',
           'all_proxy', 'ALL_PROXY', 'ftp_proxy', 'FTP_PROXY']:
    os.environ.pop(_k, None)
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# macOS 上 requests 会额外读取系统网络代理（System Preferences → Network），
# 仅靠 env var 无法屏蔽，需要 patch Session.trust_env
import requests as _requests
_orig_session_init = _requests.Session.__init__
def _no_proxy_session_init(self, *args, **kw):
    _orig_session_init(self, *args, **kw)
    self.trust_env = False          # 禁用 env + 系统代理检测
    self.proxies.update({'http': '', 'https': ''})
_requests.Session.__init__ = _no_proxy_session_init

# 确保 src 在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont, QFontDatabase
from src.app import StockApp


def main():
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("量策 AI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LiangceAI")

    # 设置全局默认字体
    font = QFont("PingFang SC", 13)
    app.setFont(font)

    window = StockApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
