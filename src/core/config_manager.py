"""
配置管理器 - 读写 config/settings.json
"""
import json
import os
from typing import Any


_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'config', 'settings.json'
)

_defaults = {
    "data_source": "akshare",
    "tushare_token": "",
    "prediction_model": "ensemble",
    "history_years": 3,
    "enable_sentiment": True,
    "enable_northbound": True,
    "auto_refresh": False,
    "push_notification": True,
    "red_threshold": 0.5,
    "watchlist": ["000001", "600519", "000858", "300750"],
    "theme": "dark",
    "language": "zh_CN",
}


class ConfigManager:
    def __init__(self):
        self._data = dict(_defaults)
        self._load()

    def _load(self):
        if os.path.exists(_CONFIG_PATH):
            try:
                with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                self._data.update(loaded)
            except Exception:
                pass

    def save(self):
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def get_all(self) -> dict:
        return dict(self._data)

    # 快捷属性
    @property
    def watchlist(self) -> list:
        return self._data.get('watchlist', [])

    def add_to_watchlist(self, code: str):
        wl = self.watchlist
        if code not in wl:
            wl.append(code)
            self.set('watchlist', wl)
            self.save()

    def remove_from_watchlist(self, code: str):
        wl = self.watchlist
        if code in wl:
            wl.remove(code)
            self.set('watchlist', wl)
            self.save()


# 全局单例
_instance = None

def get_config() -> ConfigManager:
    global _instance
    if _instance is None:
        _instance = ConfigManager()
    return _instance
