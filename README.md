# 量策 AI · 次日红盘预测系统

一个 PyQt5 桌面应用，使用 XGBoost + LightGBM 集成学习预测 A 股次日涨跌。

## 功能

- 个股选择和预测分析
- 25+ 技术指标计算
- 中文财经新闻情感分析 (SnowNLP)
- 风险因子评估
- 预测历史记录

## 运行

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# 或
./run.sh
```

## 依赖

- PyQt5
- XGBoost, LightGBM
- akshare / tushare (数据源)
- snownlp (情感分析)

## 技术栈

- XGBoost + LightGBM 集成模型
- 技术指标：MA, MACD, RSI,布林带等
- 雪球 NLP 中文情感分析

## 项目结构

```
src/
  core/           # 预测引擎
  data/          # 数据获取
  features/      # 特征工程
  models/        # ML 模型
  ui/            # 界面组件
```