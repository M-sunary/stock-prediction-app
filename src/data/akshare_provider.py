"""
AKShare 数据提供者
负责从 AKShare 获取股票行情、财务、资金等数据
"""
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


_COOLDOWN_SECS = 300   # 失败后 5 分钟再重试


class AKShareProvider:
    """AKShare 免费数据源封装"""

    def __init__(self):
        self._ak = None
        self._offline_until = 0.0   # epoch timestamp；0 表示可用

    @property
    def _network_ok(self) -> bool:
        return time.time() >= self._offline_until

    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    def _mark_offline(self, method: str, err: Exception):
        """失败时进入冷却，5 分钟后自动恢复重试"""
        was_ok = time.time() >= self._offline_until
        self._offline_until = time.time() + _COOLDOWN_SECS
        if was_ok:
            print(f"[AKShare] 请求失败（{method}），{_COOLDOWN_SECS // 60} 分钟后自动重试。"
                  f"原因: {type(err).__name__}: {err}")

    def get_stock_daily(self, code: str, years: int = 3) -> Optional[pd.DataFrame]:
        """获取个股日线数据（前复权）"""
        if not self._network_ok:
            return None
        try:
            ak = self._get_ak()
            end = datetime.now().strftime('%Y%m%d')
            start = (datetime.now() - timedelta(days=years * 365)).strftime('%Y%m%d')
            df = ak.stock_zh_a_hist(
                symbol=code, period='daily',
                start_date=start, end_date=end, adjust='qfq'
            )
            if df is None or df.empty:
                return None
            col_map = {
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume',
                '成交额': 'amount', '涨跌幅': 'pct_chg', '换手率': 'turnover'
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date').reset_index(drop=True)
        except Exception as e:
            self._mark_offline('get_stock_daily', e)
            return None

    def get_realtime_quote(self, code: str) -> Optional[dict]:
        """获取实时行情"""
        if not self._network_ok:
            return None
        try:
            ak = self._get_ak()
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None
            row = df[df['代码'] == code]
            if row.empty:
                return None
            r = row.iloc[0]
            return {
                'code': code,
                'name': r.get('名称', ''),
                'price': float(r.get('最新价', 0) or 0),
                'pct_chg': float(r.get('涨跌幅', 0) or 0),
                'change': float(r.get('涨跌额', 0) or 0),
                'volume': float(r.get('成交量', 0) or 0),
                'amount': float(r.get('成交额', 0) or 0),
                'turnover': float(r.get('换手率', 0) or 0),
                'high': float(r.get('最高', 0) or 0),
                'low': float(r.get('最低', 0) or 0),
                'open': float(r.get('今开', 0) or 0),
                'prev_close': float(r.get('昨收', 0) or 0),
                'market_cap': float(r.get('总市值', 0) or 0),
                'pe': float(r.get('市盈率-动态', 0) or 0),
            }
        except Exception as e:
            self._mark_offline('get_realtime_quote', e)
            return None

    def get_market_index(self) -> dict:
        """获取大盘指数"""
        if not self._network_ok:
            return {}
        try:
            ak = self._get_ak()
            df = ak.stock_zh_index_spot_em()
            result = {}
            targets = {'上证指数': 'sh', '深证成指': 'sz', '创业板指': 'cy'}
            for _, row in df.iterrows():
                name = row.get('名称', '')
                if name in targets:
                    result[targets[name]] = {
                        'name': name,
                        'price': float(row.get('最新价', 0) or 0),
                        'pct_chg': float(row.get('涨跌幅', 0) or 0),
                        'change': float(row.get('涨跌额', 0) or 0),
                    }
            return result
        except Exception as e:
            self._mark_offline('get_market_index', e)
            return {}

    def get_stock_info(self, code: str) -> dict:
        """获取股票基本信息（名称、行业）"""
        if not self._network_ok:
            return {'code': code, 'name': code}
        try:
            ak = self._get_ak()
            df = ak.stock_individual_info_em(symbol=code)
            if df is None or df.empty:
                return {}
            info = {}
            for _, row in df.iterrows():
                key = row.get('item', '')
                val = row.get('value', '')
                if '股票简称' in key or '名称' in key:
                    info['name'] = val
                elif '行业' in key:
                    info['industry'] = val
                elif '上市时间' in key:
                    info['list_date'] = val
            info['code'] = code
            return info
        except Exception as e:
            self._mark_offline('get_stock_info', e)
            return {'code': code, 'name': code}

    def get_market_snapshot(self) -> Optional[pd.DataFrame]:
        """获取全市场实时快照（返回原始 DataFrame，保留中文列名）"""
        if not self._network_ok:
            return None
        try:
            ak = self._get_ak()
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None
            return df
        except Exception as e:
            self._mark_offline('get_market_snapshot', e)
            return None

    def search_stocks(self, keyword: str) -> list:
        if not self._network_ok:
            return []
        try:
            ak = self._get_ak()
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return []
            mask = (
                df['代码'].str.contains(keyword, na=False) |
                df['名称'].str.contains(keyword, na=False)
            )
            results = []
            for _, row in df[mask].head(10).iterrows():
                results.append({
                    'code': row['代码'],
                    'name': row['名称'],
                    'price': float(row.get('最新价', 0) or 0),
                    'pct_chg': float(row.get('涨跌幅', 0) or 0),
                })
            return results
        except Exception as e:
            self._mark_offline('search_stocks', e)
            return []

    def get_northbound_flow(self) -> Optional[pd.DataFrame]:
        """获取北向资金数据"""
        if not self._network_ok:
            return None
        try:
            ak = self._get_ak()
            df = ak.stock_em_hsgt_north_acc_flow_in_em(symbol='北上')
            return df
        except Exception as e:
            self._mark_offline('get_northbound_flow', e)
            return None

    def get_sector_data(self) -> list:
        """获取板块涨跌情况"""
        if not self._network_ok:
            return []
        try:
            ak = self._get_ak()
            df = ak.stock_board_industry_name_em()
            if df is None or df.empty:
                return []
            results = []
            for _, row in df.head(20).iterrows():
                pct = float(row.get('涨跌幅', 0) or 0)
                results.append({
                    'name': row.get('板块名称', ''),
                    'pct_chg': pct,
                    'hot': abs(pct) > 1.5,
                })
            return sorted(results, key=lambda x: abs(x['pct_chg']), reverse=True)[:8]
        except Exception as e:
            self._mark_offline('get_sector_data', e)
            return []
