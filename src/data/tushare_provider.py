"""
Tushare 数据提供者 - AKShare 不可用时的备用数据源
需要 tushare_token 配置
"""
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

_COOLDOWN_SECS = 300


def _ts_code(code: str) -> str:
    """000001 → 000001.SZ, 600519 → 600519.SH"""
    if code.startswith(('0', '2', '3')):
        return f"{code}.SZ"
    return f"{code}.SH"


class TushareProvider:
    def __init__(self, token: str):
        self._token = token
        self._pro = None
        self._offline_until = 0.0

    @property
    def _network_ok(self) -> bool:
        return time.time() >= self._offline_until

    def _get_pro(self):
        if self._pro is None:
            import tushare as ts
            ts.set_token(self._token)
            self._pro = ts.pro_api()
        return self._pro

    def _mark_offline(self, method: str, err: Exception):
        was_ok = time.time() >= self._offline_until
        self._offline_until = time.time() + _COOLDOWN_SECS
        if was_ok:
            print(f"[Tushare] 请求失败（{method}），{_COOLDOWN_SECS // 60} 分钟后自动重试。"
                  f"原因: {type(err).__name__}: {err}")

    def get_stock_daily(self, code: str, years: int = 3) -> Optional[pd.DataFrame]:
        if not self._network_ok:
            return None
        try:
            pro = self._get_pro()
            end = datetime.now().strftime('%Y%m%d')
            start = (datetime.now() - timedelta(days=years * 365)).strftime('%Y%m%d')
            df = pro.daily(ts_code=_ts_code(code), start_date=start, end_date=end)
            if df is None or df.empty:
                return None
            df = df.rename(columns={
                'trade_date': 'date', 'vol': 'volume',
                'amount': 'amount', 'pct_chg': 'pct_chg',
                'turnover_rate': 'turnover',
            })
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            # 确保必要列存在
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col not in df.columns:
                    df[col] = 0.0
            return df[['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']]
        except Exception as e:
            self._mark_offline('get_stock_daily', e)
            return None

    def get_realtime_quote(self, code: str) -> Optional[dict]:
        """用 Tushare 最新日线数据近似实时行情"""
        if not self._network_ok:
            return None
        try:
            import tushare as ts
            ts.set_token(self._token)
            df = ts.get_realtime_quotes(code)
            if df is None or df.empty:
                return self._quote_from_daily(code)
            r = df.iloc[0]
            price = float(r.get('price', 0) or 0)
            pre_close = float(r.get('pre_close', price) or price)
            pct = round((price - pre_close) / pre_close * 100, 2) if pre_close else 0
            return {
                'code': code,
                'name': r.get('name', ''),
                'price': price,
                'pct_chg': pct,
                'change': round(price - pre_close, 2),
                'volume': float(str(r.get('volume', 0)).replace(',', '') or 0),
                'amount': float(str(r.get('amount', 0)).replace(',', '') or 0),
                'high': float(r.get('high', 0) or 0),
                'low': float(r.get('low', 0) or 0),
                'open': float(r.get('open', 0) or 0),
                'prev_close': pre_close,
                'market_cap': 0,
                'pe': 0,
                'industry': '',
                'turnover': 0,
            }
        except Exception:
            return self._quote_from_daily(code)

    def _quote_from_daily(self, code: str) -> Optional[dict]:
        """用最新日线替代实时行情"""
        try:
            pro = self._get_pro()
            end = datetime.now().strftime('%Y%m%d')
            start = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            df = pro.daily(ts_code=_ts_code(code), start_date=start, end_date=end)
            if df is None or df.empty:
                return None
            r = df.iloc[0]
            price = float(r['close'])
            pre = float(r['pre_close']) if 'pre_close' in r else price
            return {
                'code': code, 'name': '', 'price': price,
                'pct_chg': float(r.get('pct_chg', 0)),
                'change': round(price - pre, 2),
                'volume': float(r.get('vol', 0)) * 100,
                'amount': float(r.get('amount', 0)) * 1000,
                'high': float(r.get('high', 0)),
                'low': float(r.get('low', 0)),
                'open': float(r.get('open', 0)),
                'prev_close': pre, 'market_cap': 0, 'pe': 0,
                'industry': '', 'turnover': 0,
            }
        except Exception as e:
            self._mark_offline('_quote_from_daily', e)
            return None

    def get_stock_info(self, code: str) -> dict:
        if not self._network_ok:
            return {'code': code, 'name': code}
        try:
            pro = self._get_pro()
            df = pro.stock_basic(ts_code=_ts_code(code),
                                 fields='ts_code,name,industry,list_date')
            if df is None or df.empty:
                return {'code': code, 'name': code}
            r = df.iloc[0]
            return {
                'code': code,
                'name': r.get('name', ''),
                'industry': r.get('industry', ''),
                'list_date': r.get('list_date', ''),
            }
        except Exception as e:
            self._mark_offline('get_stock_info', e)
            return {'code': code, 'name': code}
