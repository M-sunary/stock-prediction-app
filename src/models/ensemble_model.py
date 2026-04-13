"""
集成预测模型
XGBoost + LightGBM 集成，支持 LSTM 可选
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

from ..features.technical_indicators import build_labeled_dataset, build_features


_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'saved_models'
)
os.makedirs(_MODELS_DIR, exist_ok=True)


class BaseModel:
    def __init__(self, name: str):
        self.name = name
        self._model = None
        self._scaler = StandardScaler()
        self._trained = False

    def train(self, X: pd.DataFrame, y: pd.Series) -> float:
        raise NotImplementedError

    def predict_proba(self, X: pd.DataFrame) -> float:
        raise NotImplementedError

    def save(self, code: str):
        path = os.path.join(_MODELS_DIR, f"{self.name}_{code}.pkl")
        with open(path, 'wb') as f:
            pickle.dump({'model': self._model, 'scaler': self._scaler, 'trained': self._trained}, f)

    def load(self, code: str) -> bool:
        path = os.path.join(_MODELS_DIR, f"{self.name}_{code}.pkl")
        if not os.path.exists(path):
            return False
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self._model = data['model']
        self._scaler = data['scaler']
        self._trained = data['trained']
        return True


class XGBoostModel(BaseModel):
    def __init__(self):
        super().__init__('xgboost')

    def train(self, X: pd.DataFrame, y: pd.Series) -> float:
        try:
            import xgboost as xgb
        except ImportError:
            return 0.0

        X_scaled = self._scaler.fit_transform(X.fillna(0).to_numpy())
        tscv = TimeSeriesSplit(n_splits=3)
        aucs = []
        for tr_idx, val_idx in tscv.split(X_scaled):
            xtr, xval = X_scaled[tr_idx], X_scaled[val_idx]
            ytr, yval = y.iloc[tr_idx], y.iloc[val_idx]
            m = xgb.XGBClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                eval_metric='logloss',
                random_state=42, n_jobs=-1
            )
            m.fit(xtr, ytr)
            proba = m.predict_proba(xval)[:, 1]
            if len(np.unique(yval)) > 1:
                aucs.append(roc_auc_score(yval, proba))

        # 最终用全量训练
        self._model = xgb.XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            eval_metric='logloss',
            random_state=42, n_jobs=-1
        )
        self._model.fit(X_scaled, y)
        self._trained = True
        return float(np.mean(aucs)) if aucs else 0.0

    def predict_proba(self, X: pd.DataFrame) -> float:
        if not self._trained or self._model is None:
            return 0.5
        X_scaled = self._scaler.transform(X.fillna(0).to_numpy())
        return float(self._model.predict_proba(X_scaled)[0, 1])

    def get_feature_importance(self, feature_names: list) -> dict:
        if not self._trained or self._model is None:
            return {}
        scores = self._model.feature_importances_
        return {name: float(score) for name, score in zip(feature_names, scores)}


class LightGBMModel(BaseModel):
    def __init__(self):
        super().__init__('lightgbm')

    def train(self, X: pd.DataFrame, y: pd.Series) -> float:
        try:
            import lightgbm as lgb
        except ImportError:
            return 0.0

        X_scaled = self._scaler.fit_transform(X.fillna(0).to_numpy())
        tscv = TimeSeriesSplit(n_splits=3)
        aucs = []
        for tr_idx, val_idx in tscv.split(X_scaled):
            xtr, xval = X_scaled[tr_idx], X_scaled[val_idx]
            ytr, yval = y.iloc[tr_idx], y.iloc[val_idx]
            m = lgb.LGBMClassifier(
                n_estimators=200, num_leaves=31, learning_rate=0.05,
                feature_fraction=0.8, bagging_fraction=0.8,
                random_state=42, verbose=-1, n_jobs=-1
            )
            m.fit(xtr, ytr, eval_set=[(xval, yval)],
                  callbacks=[lgb.early_stopping(20, verbose=False)])
            proba = m.predict_proba(xval)[:, 1]
            if len(np.unique(yval)) > 1:
                aucs.append(roc_auc_score(yval, proba))

        self._model = lgb.LGBMClassifier(
            n_estimators=300, num_leaves=31, learning_rate=0.05,
            feature_fraction=0.8, bagging_fraction=0.8,
            random_state=42, verbose=-1, n_jobs=-1
        )
        self._model.fit(X_scaled, y)
        self._trained = True
        return float(np.mean(aucs)) if aucs else 0.0

    def predict_proba(self, X: pd.DataFrame) -> float:
        if not self._trained or self._model is None:
            return 0.5
        X_scaled = self._scaler.transform(X.fillna(0).to_numpy())
        return float(self._model.predict_proba(X_scaled)[0, 1])

    def get_feature_importance(self, feature_names: list) -> dict:
        if not self._trained or self._model is None:
            return {}
        scores = self._model.feature_importances_
        total = sum(scores) or 1
        return {name: float(score / total) for name, score in zip(feature_names, scores)}


class LogisticRegressionModel(BaseModel):
    def __init__(self):
        super().__init__('logreg')

    def train(self, X: pd.DataFrame, y: pd.Series) -> float:
        from sklearn.linear_model import LogisticRegression
        X_scaled = self._scaler.fit_transform(X.fillna(0).to_numpy())
        tscv = TimeSeriesSplit(n_splits=3)
        aucs = []
        for tr_idx, val_idx in tscv.split(X_scaled):
            xtr, xval = X_scaled[tr_idx], X_scaled[val_idx]
            ytr, yval = y.iloc[tr_idx], y.iloc[val_idx]
            m = LogisticRegression(C=1.0, max_iter=500, solver='lbfgs',
                                   class_weight='balanced', random_state=42)
            m.fit(xtr, ytr)
            proba = m.predict_proba(xval)[:, 1]
            if len(np.unique(yval)) > 1:
                aucs.append(roc_auc_score(yval, proba))
        from sklearn.linear_model import LogisticRegression as LR
        self._model = LR(C=1.0, max_iter=500, solver='lbfgs',
                         class_weight='balanced', random_state=42)
        self._model.fit(X_scaled, y)
        self._trained = True
        return float(np.mean(aucs)) if aucs else 0.0

    def predict_proba(self, X: pd.DataFrame) -> float:
        if not self._trained or self._model is None:
            return 0.5
        X_scaled = self._scaler.transform(X.fillna(0).to_numpy())
        return float(self._model.predict_proba(X_scaled)[0, 1])

    def get_feature_importance(self, feature_names: list) -> dict:
        if not self._trained or self._model is None:
            return {}
        coefs = np.abs(self._model.coef_[0])
        total = coefs.sum() or 1
        return {name: float(c / total) for name, c in zip(feature_names, coefs)}


class EnsemblePredictor:
    """XGBoost + LightGBM + LogReg 集成预测器"""

    def __init__(self):
        self.xgb_model = XGBoostModel()
        self.lgb_model = LightGBMModel()
        self.logreg_model = LogisticRegressionModel()
        self._weights = {'xgboost': 0.45, 'lightgbm': 0.45, 'logreg': 0.10}
        self._feature_names = []
        self._is_trained = False

    def train(self, df: pd.DataFrame, threshold_pct: float = 0.0) -> dict:
        """训练集成模型，返回各模型 AUC"""
        labeled = build_labeled_dataset(df, threshold_pct)
        if len(labeled) < 60:
            return {'error': 'insufficient_data'}

        feature_cols = [c for c in labeled.columns if c != 'label']
        X = labeled[feature_cols]
        y = labeled['label']
        self._feature_names = feature_cols

        xgb_auc = self.xgb_model.train(X, y)
        lgb_auc = self.lgb_model.train(X, y)
        logreg_auc = self.logreg_model.train(X, y)

        # LogReg 固定 10%，其余按 AUC 比例分配剩余 90%
        denom = xgb_auc + lgb_auc or 1
        self._weights = {
            'xgboost': round(xgb_auc / denom * 0.90, 3),
            'lightgbm': round(lgb_auc / denom * 0.90, 3),
            'logreg': 0.10,
        }
        self._is_trained = True
        return {'xgboost_auc': xgb_auc, 'lightgbm_auc': lgb_auc, 'logreg_auc': logreg_auc}

    def predict(self, df: pd.DataFrame) -> dict:
        """对 df 最后一行数据进行预测"""
        features = build_features(df)
        if features.empty:
            return self._fallback_result()

        X = features.tail(1)
        if self._feature_names:
            for col in self._feature_names:
                if col not in X.columns:
                    X[col] = 0
            X = X[[c for c in self._feature_names if c in X.columns]]

        xgb_prob = self.xgb_model.predict_proba(X) if self._is_trained else 0.5
        lgb_prob = self.lgb_model.predict_proba(X) if self._is_trained else 0.5
        logreg_prob = self.logreg_model.predict_proba(X) if self._is_trained else 0.5
        ensemble = (
            self._weights.get('xgboost', 0.45) * xgb_prob +
            self._weights.get('lightgbm', 0.45) * lgb_prob +
            self._weights.get('logreg', 0.10) * logreg_prob
        )
        direction = '看多' if ensemble >= 0.5 else '看空'
        return {
            'probability': round(ensemble * 100, 1),
            'xgboost': round(xgb_prob * 100, 1),
            'lightgbm': round(lgb_prob * 100, 1),
            'logreg': round(logreg_prob * 100, 1),
            'direction': direction,
        }

    def get_feature_importance(self) -> list:
        """返回特征重要性 Top 15（三模型平均）"""
        xgb_imp = self.xgb_model.get_feature_importance(self._feature_names)
        lgb_imp = self.lgb_model.get_feature_importance(self._feature_names)
        logreg_imp = self.logreg_model.get_feature_importance(self._feature_names)

        all_keys = set(list(xgb_imp.keys()) + list(lgb_imp.keys()) + list(logreg_imp.keys()))
        merged = {}
        for k in all_keys:
            cnt = sum(1 for d in [xgb_imp, lgb_imp, logreg_imp] if k in d)
            merged[k] = sum(d.get(k, 0) for d in [xgb_imp, lgb_imp, logreg_imp]) / (cnt or 1)

        total = sum(merged.values()) or 1
        sorted_items = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:15]
        return [
            {'feature': k, 'importance': round(v / total * 100, 1)}
            for k, v in sorted_items
        ]

    def _fallback_result(self) -> dict:
        return {
            'probability': 50.0,
            'xgboost': 50.0,
            'lightgbm': 50.0,
            'logreg': 50.0,
            'direction': '中性',
        }

    def save(self, code: str):
        self.xgb_model.save(code)
        self.lgb_model.save(code)
        self.logreg_model.save(code)
        meta = {
            'weights': self._weights,
            'feature_names': self._feature_names,
            'is_trained': self._is_trained
        }
        with open(os.path.join(_MODELS_DIR, f"ensemble_meta_{code}.json"), 'w') as f:
            json.dump(meta, f)

    def load(self, code: str) -> bool:
        path = os.path.join(_MODELS_DIR, f"ensemble_meta_{code}.json")
        if not os.path.exists(path):
            return False
        with open(path) as f:
            meta = json.load(f)
        self._weights = meta['weights']
        self._feature_names = meta['feature_names']
        self._is_trained = meta['is_trained']
        xgb_ok = self.xgb_model.load(code)
        lgb_ok = self.lgb_model.load(code)
        logreg_ok = self.logreg_model.load(code)
        if not (xgb_ok and lgb_ok and logreg_ok):
            self._is_trained = False
        return xgb_ok and lgb_ok and logreg_ok

