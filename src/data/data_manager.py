"""
数据管理器 - 统一数据获取入口，带缓存
优先级：AKShare → Tushare → Demo
"""
import pandas as pd
from typing import Optional
from .akshare_provider import AKShareProvider
from .cache_manager import get_cache


class DataManager:
    def __init__(self, config=None):
        self._config = config
        self._ak = AKShareProvider()
        self._ts = None          # 延迟初始化
        self._cache = get_cache()

    def _get_ts(self):
        """懒加载 Tushare（仅当 AKShare 失败时）"""
        if self._ts is None:
            token = ''
            if self._config:
                token = self._config.get('tushare_token', '')
            if not token:
                import os
                token = os.environ.get('TUSHARE_TOKEN', '')
            if token:
                from .tushare_provider import TushareProvider
                self._ts = TushareProvider(token)
                print('[DataManager] AKShare 冷却中，尝试 Tushare 备用数据源')
        return self._ts

    def get_stock_daily(self, code: str, years: int = 3,
                        use_cache: bool = True) -> Optional[pd.DataFrame]:
        cache_key = f"daily_{code}_{years}y"
        if use_cache:
            df = self._cache.get_df(cache_key, max_age_hours=6)
            if df is not None:
                return df

        # 1. 尝试 AKShare
        df = self._ak.get_stock_daily(code, years)

        # 2. 降级 Tushare
        if df is None and not self._ak._network_ok:
            ts = self._get_ts()
            if ts:
                df = ts.get_stock_daily(code, years)

        if df is not None:
            self._cache.set_df(cache_key, df)
        return df

    def get_realtime_quote(self, code: str) -> Optional[dict]:
        cache_key = f"quote_{code}"
        cached = self._cache.get(cache_key, max_age_hours=1/60)
        if cached:
            return cached

        data = self._ak.get_realtime_quote(code)

        if data is None and not self._ak._network_ok:
            ts = self._get_ts()
            if ts:
                data = ts.get_realtime_quote(code)

        if data:
            self._cache.set(cache_key, data)
        return data

    def get_market_index(self) -> dict:
        cache_key = "market_index"
        cached = self._cache.get(cache_key, max_age_hours=1/12)
        if cached:
            return cached
        data = self._ak.get_market_index()
        if data:
            self._cache.set(cache_key, data)
        return data

    def get_stock_info(self, code: str) -> dict:
        cache_key = f"info_{code}"
        cached = self._cache.get(cache_key, max_age_hours=24)
        if cached:
            return cached

        data = self._ak.get_stock_info(code)

        if (not data or not data.get('name')) and not self._ak._network_ok:
            ts = self._get_ts()
            if ts:
                data = ts.get_stock_info(code)

        if data:
            self._cache.set(cache_key, data)
        return data

    def get_market_snapshot(self) -> 'Optional[pd.DataFrame]':
        """获取全市场实时行情快照，5 分钟 DataFrame 缓存"""
        cache_key = 'market_snapshot'
        cached = self._cache.get_df(cache_key, max_age_hours=5 / 60)
        if cached is not None:
            return cached

        raw = self._ak.get_market_snapshot()
        if raw is None:
            return None

        col_map = {
            '代码': 'code',    '名称': 'name',
            '最新价': 'price', '涨跌幅': 'pct_chg',
            '量比': 'vol_ratio', '换手率': 'turnover',
            '成交额': 'amount',
        }
        avail = {k: v for k, v in col_map.items() if k in raw.columns}
        df = raw[list(avail.keys())].rename(columns=avail).copy()
        for col in ('price', 'pct_chg', 'vol_ratio', 'turnover', 'amount'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df[df['price'].notna() & (df['price'] > 0)].reset_index(drop=True)
        self._cache.set_df(cache_key, df)
        return df

    def search_stocks(self, keyword: str) -> list:
        return self._ak.search_stocks(keyword)

    def get_sector_data(self) -> list:
        cache_key = "sector_data"
        cached = self._cache.get(cache_key, max_age_hours=1)
        if cached:
            return cached
        data = self._ak.get_sector_data()
        if data:
            self._cache.set(cache_key, {'sectors': data})
            return data
        return []

    def get_prediction_history(self, code: str) -> list:
        return self._cache.get_prediction_history(code)

    def get_accuracy_stats(self, code: str) -> dict:
        return self._cache.get_accuracy_stats(code)

    def save_prediction(self, code: str, date: str, probability: float, direction: str):
        self._cache.save_prediction(code, date, probability, direction)


# 全局单例
_instance = None


def get_data_manager(config=None) -> DataManager:
    global _instance
    if _instance is None:
        _instance = DataManager(config)
    return _instance
