# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**量策 AI · 次日红盘预测系统** — A PyQt5 desktop app that predicts next-day stock performance using an XGBoost + LightGBM ensemble, technical indicators, and Chinese news sentiment analysis.

## Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python main.py
# or
./run.sh

# No test suite exists — manual testing only
python main.py 2>&1 | tee debug.log
```

## Architecture

### Data Flow
```
User selects stock
→ PredictionWorker (QThread)
→ PredictionEngine.run_prediction()
  1. Fetch historical OHLCV (DataManager: AKShare → Tushare → demo_data)
  2. Fetch real-time quote (same fallback chain)
  3. Compute 25+ technical indicators (technical_indicators.py)
  4. Sentiment analysis via SnowNLP (sentiment_analyzer.py)
  5. Ensemble ML prediction (ensemble_model.py)
  6. Compute 5 risk factors
→ result_ready signal → MainWindow updates all UI components
```

### Key Design Patterns

**Singleton accessors** — used throughout: `PredictionEngine.instance()`, `get_data_manager()`, `get_cache()`, `get_config()`, `get_sentiment_analyzer()`

**Fallback chain** — all data fetches degrade gracefully:
- Data: AKShare (free) → Tushare (paid, requires token) → demo_data (synthetic, always works)
- Stock info: API name → demo_data name → stock code
- Predictions: real history → generated demo history

**Threading** — `PredictionWorker(QThread)` emits `result_ready`, `error_occurred`, `progress` signals; all UI updates happen on main thread via Qt signal/slot.

### Model Persistence
- Models auto-train on first prediction (~30s); subsequent calls load from disk (<1s)
- Saved per stock in `saved_models/xgboost_{code}.pkl`, `lightgbm_{code}.pkl`, `ensemble_meta_{code}.json`
- Pre-trained models included for: 000001, 000333, 000425, 000858, 002130, 300750, 600036, 600519, 601318

### Caching
- `cache/cache.db` — SQLite KV store (JSON values, TTL-based expiration)
- `cache/*.pkl` — Pickle files for DataFrames
- `cache/cache.db` also stores prediction history table (tracks accuracy over time)
- Default TTL: 6hr for daily data, 1min for real-time quotes

### UI Layout
```
MainWindow
├── TopBar (60px) — search, market indices, settings
├── IconRail (64px) — page navigation
├── Sidebar (220px) — watchlist + sector performance
└── QStackedWidget (pages 0-4)
    ├── DashboardPage — main prediction view
    └── WatchlistPage — manage tracked stocks
    (pages 2-4 are placeholders)
```

DashboardPage stacks: `StockHeader → PredictionHero → KPITiles → ChartPanel → TechIndicatorPanel → SentimentPanel → RiskFactorsPanel → PredictionHistoryPanel`

### Configuration
`config/settings.json` — key fields:
- `data_source`: `"akshare"` (default) or `"tushare"`
- `tushare_token`: required if using Tushare
- `enable_sentiment`: toggles SnowNLP analysis (off by default)
- `red_threshold`: label threshold for "up day" (default 0.5)
- `history_years`: lookback window for training data (default 2)
- `watchlist`: list of stock codes to track

### Extensibility Points
- **New data source**: create provider in `src/data/`, add to `DataManager` fallback chain
- **New ML model**: create class in `src/models/` following XGBoost/LightGBM pattern
- **New UI page**: create `QWidget` in `src/ui/pages/`, register in `MainWindow` and `IconRail`
- **New indicator**: add function to `src/features/technical_indicators.py` and include in feature list

### Theme
Dark Material Design in `src/ui/styles/theme.py`: background `#080913`, primary `#6C7DFF`, success (up) `#35D07F`, danger (down) `#FF6B6B`.
