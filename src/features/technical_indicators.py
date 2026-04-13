"""
技术指标特征工程
使用 pandas-ta 计算各类技术指标
"""
import pandas as pd
import numpy as np
from typing import Optional


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    在 df 上添加所有技术指标列
    输入 df 需包含: open, high, low, close, volume
    """
    df = df.copy()
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    # ── 移动平均 ──────────────────────────────────────────────────
    for n in [5, 10, 20, 60]:
        df[f'ma{n}'] = close.rolling(n).mean()
    df['ma_diff_5_20'] = (close - df['ma20']) / df['ma20']   # MA差离率

    # ── MACD ──────────────────────────────────────────────────────
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_golden_cross'] = (
        (df['macd'] > df['macd_signal']) &
        (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    ).astype(int)

    # ── RSI ───────────────────────────────────────────────────────
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['rsi14'] = 100 - 100 / (1 + rs)

    # ── KDJ ───────────────────────────────────────────────────────
    low_min = low.rolling(9).min()
    high_max = high.rolling(9).max()
    rsv = 100 * (close - low_min) / (high_max - low_min + 1e-9)
    df['kdj_k'] = rsv.ewm(com=2, adjust=False).mean()
    df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
    df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

    # ── BOLL 布林带 ───────────────────────────────────────────────
    boll_mid = close.rolling(20).mean()
    boll_std = close.rolling(20).std()
    df['boll_upper'] = boll_mid + 2 * boll_std
    df['boll_lower'] = boll_mid - 2 * boll_std
    df['boll_mid'] = boll_mid
    df['boll_pct'] = (close - df['boll_lower']) / (df['boll_upper'] - df['boll_lower'] + 1e-9)

    # ── 量比 / OBV ────────────────────────────────────────────────
    df['vol_ma5'] = volume.rolling(5).mean()
    df['vol_ratio'] = volume / df['vol_ma5'].replace(0, np.nan)  # 量比
    direction = np.sign(close.diff())
    df['obv'] = (volume * direction).cumsum()
    df['obv_ma5'] = df['obv'].rolling(5).mean()

    # ── 振幅 / 换手率 ─────────────────────────────────────────────
    df['amplitude'] = (high - low) / close.shift(1).replace(0, np.nan) * 100
    if 'turnover' not in df.columns:
        df['turnover'] = 0.0

    # ── 价格动量 ──────────────────────────────────────────────────
    for n in [1, 3, 5, 10, 20]:
        df[f'ret_{n}d'] = close.pct_change(n)

    # ── 历史波动率 ────────────────────────────────────────────────
    df['vol_10d'] = df['ret_1d'].rolling(10).std() * np.sqrt(252)

    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """构建最终特征矩阵（不含 label）"""
    df = add_technical_features(df)

    feature_cols = [
        'ma_diff_5_20', 'macd', 'macd_hist', 'macd_golden_cross',
        'rsi14', 'kdj_k', 'kdj_d', 'kdj_j',
        'boll_pct', 'vol_ratio', 'obv',
        'amplitude', 'turnover',
        'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'vol_10d',
    ]
    return df[[c for c in feature_cols if c in df.columns]]


def build_labeled_dataset(df: pd.DataFrame, threshold_pct: float = 0.0) -> pd.DataFrame:
    """
    构建带标签的训练集
    label=1：次日涨幅 > threshold_pct，否则 label=0
    """
    df = add_technical_features(df)
    df['next_ret'] = df['close'].pct_change(1).shift(-1) * 100
    df['label'] = (df['next_ret'] > threshold_pct).astype(int)

    feature_cols = [
        'ma_diff_5_20', 'macd', 'macd_hist', 'macd_golden_cross',
        'rsi14', 'kdj_k', 'kdj_d', 'kdj_j',
        'boll_pct', 'vol_ratio', 'obv',
        'amplitude', 'turnover',
        'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'vol_10d', 'label',
    ]
    result = df[[c for c in feature_cols if c in df.columns]].dropna()
    return result


def get_latest_signals(df: pd.DataFrame) -> list:
    """
    从最新一行数据提取关键信号列表
    返回: [{'tag': 'bull'|'bear'|'neut', 'text': '...'}]
    """
    df = add_technical_features(df)
    if df.empty:
        return []

    row = df.iloc[-1]
    signals = []

    # MACD 金叉
    if row.get('macd_golden_cross', 0):
        signals.append({'tag': 'bull', 'text': 'MACD金叉确认'})
    elif row.get('macd_hist', 0) > 0:
        signals.append({'tag': 'bull', 'text': f"MACD柱 +{row['macd_hist']:.3f}"})
    else:
        signals.append({'tag': 'bear', 'text': f"MACD柱 {row['macd_hist']:.3f}"})

    # 量比
    vr = row.get('vol_ratio', 1)
    if vr > 2:
        signals.append({'tag': 'bull', 'text': f'量比 {vr:.1f} 放量'})
    elif vr > 1.2:
        signals.append({'tag': 'neut', 'text': f'量比 {vr:.1f}'})
    else:
        signals.append({'tag': 'neut', 'text': f'量比 {vr:.1f} 缩量'})

    # RSI
    rsi = row.get('rsi14', 50)
    if rsi > 70:
        signals.append({'tag': 'bear', 'text': f'RSI {rsi:.1f}，超买警告'})
    elif rsi < 30:
        signals.append({'tag': 'bull', 'text': f'RSI {rsi:.1f}，超卖反弹'})
    else:
        signals.append({'tag': 'neut', 'text': f'RSI {rsi:.1f}，中性区间'})

    # BOLL 位置
    boll_pct = row.get('boll_pct', 0.5)
    if boll_pct > 0.8:
        signals.append({'tag': 'bear', 'text': f'接近布林上轨 ({boll_pct*100:.0f}%)'})
    elif boll_pct < 0.2:
        signals.append({'tag': 'bull', 'text': f'接近布林下轨，支撑位'})
    else:
        signals.append({'tag': 'neut', 'text': f'布林中轨区间'})

    # KDJ
    k = row.get('kdj_k', 50)
    if k > 80:
        signals.append({'tag': 'bear', 'text': f'KDJ-K {k:.1f}，超买'})
    elif k < 20:
        signals.append({'tag': 'bull', 'text': f'KDJ-K {k:.1f}，超卖'})

    return signals[:6]


def get_indicator_summary(df: pd.DataFrame) -> list:
    """
    返回技术指标评分列表，用于界面展示
    每项: {'name': 'MA5', 'value': '11.28', 'signal': 'BUY'|'SELL'|'HOLD', 'color': 'green'|'red'|'gold'}
    """
    df = add_technical_features(df)
    if df.empty:
        return []

    row = df.iloc[-1]
    close = row.get('close', 0)
    indicators = []

    def sig(val: float, buy_cond: bool, sell_cond: bool):
        if buy_cond:
            return 'BUY', 'green'
        elif sell_cond:
            return 'SELL', 'red'
        return 'HOLD', 'gold'

    # MA5
    ma5 = row.get('ma5', close)
    s, c = sig(ma5, close > ma5, close < ma5 * 0.98)
    indicators.append({'name': 'MA5', 'value': f'{ma5:.2f}', 'signal': s, 'color': c})

    # MA20
    ma20 = row.get('ma20', close)
    s, c = sig(ma20, close > ma20, close < ma20 * 0.97)
    indicators.append({'name': 'MA20', 'value': f'{ma20:.2f}', 'signal': s, 'color': c})

    # MACD
    macd = row.get('macd', 0)
    hist = row.get('macd_hist', 0)
    golden = bool(row.get('macd_golden_cross', False))
    if golden:
        indicators.append({'name': 'MACD', 'value': f'+{macd:.3f}', 'signal': '金叉', 'color': 'green'})
    elif hist > 0:
        indicators.append({'name': 'MACD', 'value': f'+{macd:.3f}', 'signal': 'BUY', 'color': 'green'})
    else:
        indicators.append({'name': 'MACD', 'value': f'{macd:.3f}', 'signal': 'SELL', 'color': 'red'})

    # RSI
    rsi = row.get('rsi14', 50)
    s, c = sig(rsi, rsi < 45, rsi > 75)
    indicators.append({'name': 'RSI-14', 'value': f'{rsi:.1f}', 'signal': s, 'color': c})

    # KDJ
    k = row.get('kdj_k', 50)
    s, c = sig(k, k < 30, k > 80)
    indicators.append({'name': 'KDJ-K', 'value': f'{k:.1f}', 'signal': s, 'color': c})

    # BOLL
    boll_pct = row.get('boll_pct', 0.5)
    if boll_pct > 0.5:
        indicators.append({'name': 'BOLL', 'value': '中轨+', 'signal': 'BUY', 'color': 'green'})
    elif boll_pct < 0.2:
        indicators.append({'name': 'BOLL', 'value': '下轨支撑', 'signal': 'BUY', 'color': 'green'})
    else:
        indicators.append({'name': 'BOLL', 'value': '中轨-', 'signal': 'HOLD', 'color': 'gold'})

    # 量比
    vr = row.get('vol_ratio', 1)
    s = '放量' if vr > 1.5 else ('缩量' if vr < 0.7 else 'HOLD')
    c = 'green' if vr > 1.5 else ('red' if vr < 0.5 else 'gold')
    indicators.append({'name': '量比', 'value': f'{vr:.2f}', 'signal': s, 'color': c})

    # OBV
    obv = row.get('obv', 0)
    obv_ma = row.get('obv_ma5', obv)
    s, c = ('↑趋势', 'green') if obv > obv_ma else ('↓趋势', 'red')
    indicators.append({'name': 'OBV', 'value': s, 'signal': 'BUY' if obv > obv_ma else 'SELL', 'color': c})

    # 振幅
    amp = row.get('amplitude', 0)
    indicators.append({'name': '振幅', 'value': f'{amp:.1f}%', 'signal': '正常' if amp < 3 else '波动', 'color': 'gold'})

    # 换手率
    to = row.get('turnover', 0)
    indicators.append({'name': '换手率', 'value': f'{to:.2f}%', 'signal': 'HOLD', 'color': 'gold'})

    return indicators
