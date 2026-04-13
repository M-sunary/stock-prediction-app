"""
演示数据生成器 - 网络不可用时提供真实感的模拟数据
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# 各股票的真实基准参数（扩充常见股票）
_STOCK_PARAMS = {
    # 银行
    '000001': {'name': '平安银行',  'price': 11.42, 'industry': '银行', 'market': 'SZ', 'pe': 5.8},
    '600036': {'name': '招商银行',  'price': 32.18, 'industry': '银行', 'market': 'SH', 'pe': 6.4},
    '601398': {'name': '工商银行',  'price': 6.28,  'industry': '银行', 'market': 'SH', 'pe': 5.2},
    '601288': {'name': '农业银行',  'price': 4.85,  'industry': '银行', 'market': 'SH', 'pe': 4.8},
    '600000': {'name': '浦发银行',  'price': 8.92,  'industry': '银行', 'market': 'SH', 'pe': 4.5},
    # 白酒
    '600519': {'name': '贵州茅台',  'price': 1680.0,'industry': '白酒', 'market': 'SH', 'pe': 26.5},
    '000858': {'name': '五粮液',    'price': 125.80,'industry': '白酒', 'market': 'SZ', 'pe': 18.6},
    '000568': {'name': '泸州老窖',  'price': 108.40,'industry': '白酒', 'market': 'SZ', 'pe': 17.2},
    '000596': {'name': '古井贡酒',  'price': 168.20,'industry': '白酒', 'market': 'SZ', 'pe': 22.1},
    # 新能源/科技
    '300750': {'name': '宁德时代',  'price': 218.34,'industry': '新能源', 'market': 'SZ', 'pe': 32.1},
    '002594': {'name': '比亚迪',    'price': 295.40,'industry': '汽车', 'market': 'SZ', 'pe': 22.7},
    '601012': {'name': '隆基绿能',  'price': 18.56, 'industry': '光伏', 'market': 'SH', 'pe': 15.3},
    '600941': {'name': '中国移动',  'price': 95.40, 'industry': '通信', 'market': 'SH', 'pe': 11.8},
    '000725': {'name': '京东方A',   'price': 4.12,  'industry': '面板', 'market': 'SZ', 'pe': 12.4},
    # 保险/金融
    '601318': {'name': '中国平安',  'price': 45.68, 'industry': '保险', 'market': 'SH', 'pe': 9.2},
    '601628': {'name': '中国人寿',  'price': 31.20, 'industry': '保险', 'market': 'SH', 'pe': 14.1},
    '600030': {'name': '中信证券',  'price': 22.45, 'industry': '证券', 'market': 'SH', 'pe': 16.8},
    # 消费/家电
    '000333': {'name': '美的集团',  'price': 56.22, 'industry': '家电', 'market': 'SZ', 'pe': 14.5},
    '000651': {'name': '格力电器',  'price': 38.50, 'industry': '家电', 'market': 'SZ', 'pe': 11.2},
    '600887': {'name': '伊利股份',  'price': 27.80, 'industry': '食品', 'market': 'SH', 'pe': 18.6},
    '002352': {'name': '顺丰控股',  'price': 42.60, 'industry': '物流', 'market': 'SZ', 'pe': 20.3},
    # 医药
    '600276': {'name': '恒瑞医药',  'price': 38.90, 'industry': '医药', 'market': 'SH', 'pe': 45.2},
    '300015': {'name': '爱尔眼科',  'price': 18.42, 'industry': '医疗', 'market': 'SZ', 'pe': 32.8},
    '603259': {'name': '药明康德',  'price': 52.30, 'industry': '医药', 'market': 'SH', 'pe': 28.4},
    # 地产/建筑
    '000002': {'name': '万科A',     'price': 7.85,  'industry': '地产', 'market': 'SZ', 'pe': 8.2},
    '600048': {'name': '保利发展',  'price': 8.92,  'industry': '地产', 'market': 'SH', 'pe': 6.5},
    # 有色/资源
    '600900': {'name': '长江电力',  'price': 26.80, 'industry': '电力', 'market': 'SH', 'pe': 22.5},
    '601899': {'name': '紫金矿业',  'price': 14.32, 'industry': '有色', 'market': 'SH', 'pe': 16.2},
    '601088': {'name': '中国神华',  'price': 38.60, 'industry': '煤炭', 'market': 'SH', 'pe': 10.8},
    # 互联网/软件
    '688111': {'name': '金山办公',  'price': 168.50,'industry': '软件', 'market': 'SH', 'pe': 55.2},
    '300059': {'name': '东方财富',  'price': 19.42, 'industry': '互联网金融', 'market': 'SZ', 'pe': 28.6},
}

_DEFAULT_PARAMS = {'name': '--', 'price': 10.0, 'industry': '--', 'market': 'SZ', 'pe': 10.0}


def get_stock_params(code: str) -> dict:
    return _STOCK_PARAMS.get(code, {**_DEFAULT_PARAMS, 'name': code})


def generate_daily_data(code: str, years: int = 3) -> pd.DataFrame:
    """生成真实感的历史日线数据"""
    params = get_stock_params(code)
    base_price = params['price']
    n = years * 252

    # 用 code 作为随机种子，保证同一股票每次生成相同数据
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(code))
    rng = np.random.default_rng(seed)

    # 随机游走（含均值回归）
    drift = 0.0002
    vol = 0.018
    shocks = rng.normal(drift, vol, n)

    # 添加一些趋势和周期性
    t = np.linspace(0, 4 * np.pi, n)
    trend = np.sin(t) * 0.003  # 波浪趋势
    shocks = shocks + trend

    # 价格序列（从过去推算到现在）
    log_returns = np.cumsum(shocks)
    close = base_price * np.exp(log_returns - log_returns[-1])  # 终点对齐到 base_price

    # OHLC
    daily_vol = rng.uniform(0.008, 0.025, n)
    high = close * (1 + daily_vol)
    low = close * (1 - daily_vol)
    open_noise = rng.normal(0, 0.006, n)
    open_price = np.roll(close, 1) * (1 + open_noise)
    open_price[0] = close[0]

    # 量能（成交量与价格波动相关）
    base_vol = base_price * 5e6
    vol_factor = 1 + np.abs(shocks) * 20
    volume = base_vol * vol_factor * rng.uniform(0.6, 1.4, n)
    amount = close * volume
    pct_chg = np.diff(close, prepend=close[0]) / np.maximum(np.roll(close, 1), 0.01) * 100
    pct_chg[0] = 0
    turnover = rng.uniform(0.3, 2.5, n)

    # 生成交易日期（到今天为止）
    end_date = datetime.now().date()
    dates = pd.bdate_range(end=end_date, periods=n)

    df = pd.DataFrame({
        'date': dates,
        'open': np.round(open_price, 2),
        'high': np.round(high, 2),
        'low': np.round(low, 2),
        'close': np.round(close, 2),
        'volume': np.round(volume).astype(int),
        'amount': np.round(amount, 0),
        'pct_chg': np.round(pct_chg, 2),
        'turnover': np.round(turnover, 2),
    })
    # 确保 high >= max(open, close) 等合理性
    df['high'] = df[['high', 'open', 'close']].max(axis=1)
    df['low'] = df[['low', 'open', 'close']].min(axis=1)
    return df.reset_index(drop=True)


def generate_realtime_quote(code: str) -> dict:
    """生成实时行情快照"""
    params = get_stock_params(code)
    price = params['price']
    rng = np.random.default_rng()
    pct = rng.uniform(-2.5, 2.5)
    change = round(price * pct / 100, 2)

    return {
        'code': code,
        'name': params['name'],
        'price': price,
        'pct_chg': round(pct, 2),
        'change': change,
        'volume': int(rng.uniform(2e7, 8e7)),
        'amount': round(price * rng.uniform(2e8, 8e8), 0),
        'turnover': round(rng.uniform(0.3, 2.0), 2),
        'high': round(price * (1 + abs(rng.normal(0, 0.01))), 2),
        'low': round(price * (1 - abs(rng.normal(0, 0.01))), 2),
        'open': round(price * (1 + rng.normal(0, 0.005)), 2),
        'prev_close': round(price - change, 2),
        'market_cap': round(price * rng.uniform(1e10, 5e11), 0),
        'pe': params['pe'],
        'industry': params['industry'],
    }


def generate_market_index() -> dict:
    """模拟大盘指数"""
    rng = np.random.default_rng()
    return {
        'sh': {'name': '上证指数', 'price': 3127.46, 'pct_chg': round(rng.uniform(-1.5, 1.5), 2), 'change': 0},
        'sz': {'name': '深证成指', 'price': 9891.23, 'pct_chg': round(rng.uniform(-1.8, 1.8), 2), 'change': 0},
    }


def generate_sector_data() -> list:
    """模拟板块数据"""
    sectors = [
        ('银行', 1.82, True), ('白酒', 0.94, True),
        ('新能源', -0.62, False), ('医药', 0.31, False),
        ('科技', 1.12, True), ('地产', -1.43, False),
        ('消费', 0.55, False), ('半导体', 2.18, True),
    ]
    return [{'name': n, 'pct_chg': p, 'hot': h} for n, p, h in sectors]


def generate_prediction_history(code: str) -> list:
    """生成近期预测历史"""
    seed = sum(ord(c) for c in code)
    rng = np.random.default_rng(seed)
    history = []
    for i in range(6):
        day = datetime.now() - timedelta(days=i + 1)
        # 跳过周末
        while day.weekday() >= 5:
            day -= timedelta(days=1)
        prob = int(rng.uniform(40, 80))
        direction = '看多' if prob >= 50 else '看空'
        actual_pct = round(rng.uniform(-2.5, 2.5), 2)
        actual = f'红盘 +{actual_pct}%' if actual_pct >= 0 else f'绿盘 {actual_pct}%'
        correct = (direction == '看多' and actual_pct >= 0) or (direction == '看空' and actual_pct < 0)
        history.append({
            'date': day.strftime('%m-%d'),
            'probability': prob,
            'direction': direction,
            'actual_result': actual,
            'actual_pct': actual_pct,
            'correct': correct,
        })
    return history
