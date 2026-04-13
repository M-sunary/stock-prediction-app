"""
情感分析模块 - 使用 SnowNLP 对中文新闻进行情感打分
"""
import re
from typing import List, Dict, Optional


# 模拟新闻数据（实际应从网络抓取）
_MOCK_NEWS = [
    {
        'title': '平安银行发布半年报，净利润同比增长14.2%，超出市场预期',
        'source': '财联社',
        'time': '2h前',
        'sentiment': 0.82,
        'tag': 'bull',
    },
    {
        'title': '央行降准落地，银行板块受益明显，北向资金持续加仓',
        'source': '证券时报',
        'time': '4h前',
        'sentiment': 0.71,
        'tag': 'bull',
    },
    {
        'title': '银保监会就银行业务规范征求意见，整体影响中性',
        'source': '新浪财经',
        'time': '6h前',
        'sentiment': 0.05,
        'tag': 'neut',
    },
    {
        'title': '部分分析师下调目标价，理由为地产敞口风险',
        'source': '东方财富',
        'time': '8h前',
        'sentiment': -0.38,
        'tag': 'bear',
    },
]


class SentimentAnalyzer:
    """中文金融新闻情感分析器"""

    def __init__(self):
        self._snownlp = None
        self._available = False
        self._try_init()

    def _try_init(self):
        try:
            from snownlp import SnowNLP
            self._snownlp = SnowNLP
            self._available = True
        except ImportError:
            print("[Sentiment] SnowNLP not available, using rule-based fallback")

    def analyze_text(self, text: str) -> float:
        """
        分析文本情感，返回 [-1, +1] 区间分数
        >0.3: 正面, <-0.3: 负面, 其他: 中性
        """
        if self._available:
            try:
                s = self._snownlp(text)
                # SnowNLP 返回 [0,1]，转换为 [-1,1]
                raw = s.sentiments
                score = (raw - 0.5) * 2
                # 金融词汇加权
                score = self._adjust_with_keywords(text, score)
                return max(-1.0, min(1.0, score))
            except Exception:
                pass
        return self._rule_based(text)

    def _adjust_with_keywords(self, text: str, score: float) -> float:
        """基于金融关键词调整情感分数"""
        positive_words = ['增长', '上涨', '盈利', '净利润增', '超预期', '加仓', '利好', '降准', '突破']
        negative_words = ['下跌', '亏损', '风险', '下调', '减持', '警告', '违规', '处罚', '敞口']
        adjust = 0.0
        for w in positive_words:
            if w in text:
                adjust += 0.1
        for w in negative_words:
            if w in text:
                adjust -= 0.1
        return score + adjust

    def _rule_based(self, text: str) -> float:
        """规则回退"""
        pos = ['涨', '增', '利好', '突破', '超预期', '加仓', '净流入']
        neg = ['跌', '降', '风险', '亏损', '减持', '下调', '出事']
        p = sum(text.count(w) for w in pos)
        n = sum(text.count(w) for w in neg)
        total = p + n
        if total == 0:
            return 0.0
        return (p - n) / total

    def analyze_batch(self, texts: List[str]) -> List[float]:
        return [self.analyze_text(t) for t in texts]

    def aggregate_score(self, scores: List[float], decay: float = 0.9) -> float:
        """加权聚合（近期权重更高）"""
        if not scores:
            return 0.0
        weights = [decay ** i for i in range(len(scores))]
        total_w = sum(weights)
        return sum(s * w for s, w in zip(scores, weights)) / total_w

    def get_news_with_sentiment(self, code: str, name: str = '') -> list:
        """获取新闻并附带情感分数（当前为模拟数据，可扩展为真实爬虫）"""
        # 实际项目中这里调用新闻 API 或爬虫
        news = []
        for item in _MOCK_NEWS:
            news.append({
                'title': item['title'].replace('平安银行', name or '该公司'),
                'source': item['source'],
                'time': item['time'],
                'sentiment': item['sentiment'],
                'tag': item['tag'],
            })
        return news

    def get_sentiment_score(self, code: str, name: str = '') -> float:
        """获取综合情感分数 [-1, +1]"""
        news = self.get_news_with_sentiment(code, name)
        scores = [n['sentiment'] for n in news]
        return self.aggregate_score(scores)


_instance = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _instance
    if _instance is None:
        _instance = SentimentAnalyzer()
    return _instance
