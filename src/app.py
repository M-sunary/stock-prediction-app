"""
应用程序入口类
"""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from .ui.main_window import MainWindow


class StockApp:
    def __init__(self):
        self._window = None

    def show(self):
        self._window = MainWindow()
        self._window.show()
        return self._window
