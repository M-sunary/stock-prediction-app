"""
预测引擎 - 统一调度数据获取、特征工程、模型预测
网络不可用时自动降级为演示数据模式
"""
from PyQt5.QtCore import pyqtSignal, QThread
from typing import Optional
import traceback

from ..data.data_manager import get_data_manager
from ..data.demo_data import (
    generate_daily_data, generate_realtime_quote,
    generate_market_index, generate_prediction_history, get_stock_params
)
from ..features.technical_indicators import (
    add_technical_features, get_latest_signals, get_indicator_summary
)
from ..features.sentiment_analyzer import get_sentiment_analyzer
from ..models.ensemble_model import EnsemblePredictor
from ..core.config_manager import get_config


class PredictionWorker(QThread):
    """后台预测线程，避免 UI 卡顿"""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, code: str, name: str = ''):
        super().__init__()
        self.code = code
        self.name = name

    def run(self):
        try:
            engine = PredictionEngine.instance()
            self.progress.emit('正在获取行情数据...')
            result = engine.run_prediction(self.code, self.name, self.progress)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
            traceback.print_exc()


class PredictionEngine:
    """预测引擎单例"""
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._data = get_data_manager()
        self._sentiment = get_sentiment_analyzer()
        self._config = get_config()
        self._predictors: dict = {}

    def _get_predictor(self, code: str) -> EnsemblePredictor:
        if code not in self._predictors:
            p = EnsemblePredictor()
            p.load(code)
            self._predictors[code] = p
        return self._predictors[code]

    def run_prediction(self, code: str, name: str = '',
                       progress_cb=None) -> dict:
        def emit(msg):
            if progress_cb:
                progress_cb.emit(msg)

        # 1. 获取股票基础信息
        params = get_stock_params(code)
        if not name:
            name = params.get('name', code)

        # 2. 获取历史数据（AKShare → Tushare → demo）
        emit('获取K线数据...')
        years = self._config.get('history_years', 3)
        df = self._data.get_stock_daily(code, years=years)
        is_demo = False
        if df is None or len(df) < 60:
            emit('使用演示数据（网络不可用）...')
            df = generate_daily_data(code, years)
            is_demo = True

        # 3. 获取实时行情（同样走 AKShare → Tushare → demo 链路）
        emit('获取实时行情...')
        quote = self._data.get_realtime_quote(code) if not is_demo else None
        if not quote:
            quote = generate_realtime_quote(code)

        # 从行情/股票信息更新 name（Tushare 可以返回真实名称）
        if not name or name == code:
            info = self._data.get_stock_info(code)
            real_name = info.get('name', '')
            if real_name and real_name != code:
                name = real_name
        if not name or name == code:
            name = quote.get('name', '') or params.get('name', code)

        # 4. 计算技术指标
        emit('计算技术指标...')
        df_ta = add_technical_features(df)
        signals = get_latest_signals(df_ta)
        indicators = get_indicator_summary(df_ta)

        # 5. 情感分析
        sentiment_score = 0.0
        news_list = []
        if self._config.get('enable_sentiment', True):
            emit('分析新闻情感...')
            sentiment_score = self._sentiment.get_sentiment_score(code, name)
            news_list = self._sentiment.get_news_with_sentiment(code, name)

        # 6. ML 预测
        emit('运行预测模型...')
        predictor = self._get_predictor(code)
        threshold = self._config.get('red_threshold', 0.0)

        if not predictor._is_trained:
            emit('训练模型（首次约需 30 秒）...')
            predictor.train(df_ta, threshold)
            predictor.save(code)

        prediction = predictor.predict(df_ta)
        feature_importance = predictor.get_feature_importance()

        # 保存本次预测到历史记录，供自选股页面展示
        import datetime as _dt
        today = df['date'].iloc[-1].strftime('%Y-%m-%d') if 'date' in df.columns else \
            _dt.date.today().isoformat()
        self._data.save_prediction(
            code, today,
            prediction.get('probability', 50.0),
            prediction.get('direction', '--')
        )

        # 持久化特征重要性到缓存，供因子分析页面使用
        self._data._cache.set(
            f"feature_importance_{code}",
            {'items': feature_importance, 'updated': today}
        )

        # 缓存股票名称，供自选股/侧边栏显示
        if name and name != code:
            self._data._cache.set(f"info_{code}", {'code': code, 'name': name})

        # 7. 风险因子
        risk_factors = self._compute_risk_factors(df_ta)

        # 8. 52周统计
        close = df['close']
        high52 = float(close.tail(252).max())
        low52 = float(close.tail(252).min())
        current = float(close.iloc[-1])
        pct_52 = (current - low52) / (high52 - low52) * 100 if high52 != low52 else 50

        # 9. 预测历史（真实记录 + demo 兜底）
        history = self._data.get_prediction_history(code)
        if not history:
            history = generate_prediction_history(code)

        accuracy = self._data.get_accuracy_stats(code)
        if not accuracy.get('wins') and not accuracy.get('losses'):
            # 计算 demo history 准确率
            wins = sum(1 for h in history if h.get('correct'))
            losses = len(history) - wins
            accuracy = {'wins': wins, 'losses': losses,
                        'accuracy': wins / len(history) if history else 0}

        return {
            'code': code,
            'name': name,
            'quote': quote,
            'df': df,
            'df_ta': df_ta,
            'prediction': prediction,
            'signals': signals,
            'indicators': indicators,
            'sentiment_score': sentiment_score,
            'news': news_list,
            'risk_factors': risk_factors,
            'feature_importance': feature_importance,
            'stats': {
                'high_52w': high52,
                'low_52w': low52,
                'pct_52w': round(pct_52, 1),
                'pe': quote.get('pe', params.get('pe', 0)),
                'amount': quote.get('amount', 0),
            },
            'history': history,
            'accuracy': accuracy,
            'is_demo': is_demo,
            'error': None,
        }

    def get_cached_feature_importance(self, code: str) -> list:
        """返回缓存的特征重要性，供因子分析页面调用（无需重跑预测）"""
        cached = self._data._cache.get(f"feature_importance_{code}", max_age_hours=24 * 7)
        if cached:
            return cached.get('items', [])
        predictor = self._get_predictor(code)
        if predictor._is_trained:
            return predictor.get_feature_importance()
        return []

    def _compute_risk_factors(self, df_ta) -> list:
        if df_ta.empty:
            return []
        row = df_ta.iloc[-1]
        vol = row.get('vol_10d', 0.2) * 100
        sys_risk = min(int(vol * 10), 80)
        factors = [
            {'name': '大盘系统风险', 'value': sys_risk, 'label': _risk_label(sys_risk)},
            {'name': '行业集中度', 'value': 42, 'label': _risk_label(42)},
            {'name': '地产敞口风险', 'value': 35, 'label': _risk_label(35)},
            {'name': '利率变动风险', 'value': 31, 'label': _risk_label(31)},
        ]
        to = row.get('turnover', 0.5)
        liq = max(5, min(80, int(100 - to * 40)))
        factors.append({'name': '流动性风险', 'value': liq, 'label': _risk_label(liq)})
        avg = int(sum(f['value'] for f in factors) / len(factors))
        factors.append({'name': '综合风险评分', 'value': avg, 'label': _risk_label(avg)})
        return factors


def _risk_label(v: int) -> str:
    if v <= 30:
        return '低'
    elif v <= 50:
        return '中'
    elif v <= 70:
        return '中高'
    return '高'
