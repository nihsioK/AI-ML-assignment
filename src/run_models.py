"""Benchmark eleven regression algorithms on daily PM2.5 in Karaganda under 10-fold validation.

Four experiments are run on the same algorithm roster:

  A  same-day meteorology -> PM2.5, shuffled KFold(k=10)        <- Table 1 of the assignment
  B  same-day meteorology -> PM2.5, blocked TimeSeriesSplit(10) <- leakage control for A
  C  next-day forecast with pollutant lags, TimeSeriesSplit(10) <- operational forecasting task
  D  as A but fitted on log(PM2.5), metrics back-transformed    <- skewness control for A

Experiment A is the one the assignment specifies. B exists because a shuffled split on an
autocorrelated daily series lets a model memorise neighbouring days, so A alone would overstate
generalisation; the A-minus-B gap is reported rather than hidden. C answers the practically
useful question ("what will tomorrow look like?"), which A does not. D checks that the ranking
in A is not an artefact of the right-skewed target penalising the linear models.

Alpha for Ridge/Lasso/ElasticNet and k for KNN are selected by an inner cross-validation on the
training fold only, so no test-fold information reaches model selection. Boosting and bagging
hyper-parameters are fixed a priori (see MODELS) and identical across experiments.

Outputs, all under results/:
  table1_experiment_A.csv ... table1_experiment_D.csv   per-experiment metric tables
  table1.md                                             the assignment table, experiment A
  cv_folds_long.csv                                     every fold of every model, for the paper
  predictions_best.csv                                  out-of-fold predictions of the best model
  permutation_importance.csv                            predictor importance of the best model
"""
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (AdaBoostRegressor, ExtraTreesRegressor, GradientBoostingRegressor,
                              HistGradientBoostingRegressor)
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import ElasticNetCV, LassoCV, RidgeCV
from sklearn.model_selection import GridSearchCV, KFold, TimeSeriesSplit, cross_validate, cross_val_predict
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from build_features import feature_columns, TARGET

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'processed' / 'karaganda_modelling.csv'
OUT = ROOT / 'results'
SEED = 42
K = 10
ALPHAS = np.logspace(-3, 3, 25)
L1_RATIOS = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99]


def _pipe(estimator, scale: bool):
    """Median imputation for every model, standardisation only where the algorithm needs it.

    Both steps live inside the pipeline so they are refitted on each training fold and never
    see the held-out fold.
    """
    steps = [('impute', SimpleImputer(strategy='median'))]
    if scale:
        steps.append(('scale', StandardScaler()))
    steps.append(('model', estimator))
    return Pipeline(steps)


def models() -> dict[str, Pipeline]:
    knn = GridSearchCV(KNeighborsRegressor(weights='distance'),
                       {'n_neighbors': [3, 5, 10, 15, 20, 30]}, cv=5, scoring='neg_root_mean_squared_error')
    from catboost import CatBoostRegressor
    from lightgbm import LGBMRegressor
    from xgboost import XGBRegressor
    return {
        'Baseline (mean)': _pipe(DummyRegressor(strategy='mean'), False),
        'Ridge': _pipe(RidgeCV(alphas=ALPHAS), True),
        'Lasso': _pipe(LassoCV(alphas=ALPHAS, max_iter=20000, random_state=SEED), True),
        'Elastic Net': _pipe(ElasticNetCV(alphas=ALPHAS, l1_ratio=L1_RATIOS, max_iter=20000,
                                          random_state=SEED), True),
        'KNN Regression': _pipe(knn, True),
        'Extra Trees Regression': _pipe(ExtraTreesRegressor(
            n_estimators=500, random_state=SEED, n_jobs=-1), False),
        'Adaptive Boosting (AdaBoost)': _pipe(AdaBoostRegressor(
            n_estimators=300, learning_rate=0.5, random_state=SEED), False),
        'Gradient Boosting Regression': _pipe(GradientBoostingRegressor(
            n_estimators=500, learning_rate=0.05, max_depth=3, subsample=0.8, random_state=SEED), False),
        'XGBoost': _pipe(XGBRegressor(
            n_estimators=600, learning_rate=0.05, max_depth=5, subsample=0.8, colsample_bytree=0.8,
            reg_lambda=1.0, random_state=SEED, n_jobs=-1, tree_method='hist'), False),
        'LightGBM': _pipe(LGBMRegressor(
            n_estimators=600, learning_rate=0.05, num_leaves=31, subsample=0.8, colsample_bytree=0.8,
            random_state=SEED, n_jobs=-1, verbose=-1), False),
        'CatBoost': _pipe(CatBoostRegressor(
            iterations=600, learning_rate=0.05, depth=6, random_seed=SEED, verbose=0,
            allow_writing_files=False), False),
        'HistGradientBoosting': _pipe(HistGradientBoostingRegressor(
            max_iter=600, learning_rate=0.05, random_state=SEED), False),
    }


SCORING = {'rmse': 'neg_root_mean_squared_error', 'mae': 'neg_mean_absolute_error', 'r2': 'r2'}


def evaluate(X: pd.DataFrame, y: pd.Series, cv, log_target: bool = False):
    """Run every model under one cross-validation design. Returns (summary, per-fold long table)."""
    rows, folds = [], []
    for name, pipe in models().items():
        est = TransformedTargetRegressor(pipe, func=np.log, inverse_func=np.exp) if log_target else pipe
        t0 = time.perf_counter()
        cvres = cross_validate(est, X, y, cv=cv, scoring=SCORING, n_jobs=1, error_score='raise')
        elapsed = time.perf_counter() - t0
        rmse, mae, r2 = (-cvres['test_rmse'], -cvres['test_mae'], cvres['test_r2'])
        rows.append({
            'Algorithm': name, 'Number of features': X.shape[1], 'Number of targets': 1,
            'k-fold validation': f'{cv.get_n_splits()}-fold',
            'RMSE': rmse.mean(), 'RMSE_sd': rmse.std(),
            'MAE': mae.mean(), 'MAE_sd': mae.std(),
            'R2': r2.mean(), 'R2_sd': r2.std(),
            'Fit time, s': elapsed / cv.get_n_splits(),
        })
        for i, (a, b, c) in enumerate(zip(rmse, mae, r2), 1):
            folds.append({'Algorithm': name, 'fold': i, 'RMSE': a, 'MAE': b, 'R2': c})
        print(f'  {name:<30} RMSE {rmse.mean():6.3f}  MAE {mae.mean():6.3f}  '
              f'R2 {r2.mean():6.3f} +-{r2.std():.3f}  ({elapsed:5.1f} s)')
    return pd.DataFrame(rows), pd.DataFrame(folds)


def lagged_frame(df: pd.DataFrame, feats: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Experiment C: predict PM2.5 at t+1 from meteorology at t+1 plus pollution history up to t.

    Meteorology for the target day is treated as known, which is what an operational forecast has
    from a numerical weather prediction model. Only the pollutant terms are lagged.
    """
    g = df.copy()
    for lag in (1, 2, 3):
        g[f'pm2_5_lag{lag}'] = g[TARGET].shift(lag)
    g['pm2_5_roll3'] = g[TARGET].shift(1).rolling(3).mean()
    g['pm2_5_roll7'] = g[TARGET].shift(1).rolling(7).mean()
    g['pm10_lag1'] = g['ctx_pm10'].shift(1)
    g['no2_lag1'] = g['ctx_nitrogen_dioxide'].shift(1)
    lag_cols = [c for c in g.columns if 'lag' in c or 'roll' in c]
    g = g.dropna(subset=lag_cols).reset_index(drop=True)
    return g[feats + lag_cols], g[TARGET]


def main():
    df = pd.read_csv(DATA, parse_dates=['date'])
    feats = feature_columns(df)
    X, y = df[feats], df[TARGET]
    OUT.mkdir(parents=True, exist_ok=True)

    kfold = KFold(n_splits=K, shuffle=True, random_state=SEED)
    blocked = TimeSeriesSplit(n_splits=K)
    experiments = {
        'A': ('Same-day meteorology, shuffled 10-fold', X, y, kfold, False),
        'B': ('Same-day meteorology, blocked 10-fold', X, y, blocked, False),
        'C': ('Next-day forecast with lags, blocked 10-fold', *lagged_frame(df, feats), blocked, False),
        'D': ('Same-day meteorology, log target, shuffled 10-fold', X, y, kfold, True),
    }

    summaries, all_folds = {}, []
    for key, (title, Xe, ye, cv, logt) in experiments.items():
        print(f'\nExperiment {key}: {title}  (n={len(ye)}, p={Xe.shape[1]})')
        summary, folds = evaluate(Xe, ye, cv, log_target=logt)
        summary.insert(0, 'Experiment', key)
        summary.to_csv(OUT / f'table1_experiment_{key}.csv', index=False)
        summaries[key] = summary
        folds.insert(0, 'Experiment', key)
        all_folds.append(folds)

    pd.concat(all_folds).to_csv(OUT / 'cv_folds_long.csv', index=False)
    write_table1(summaries['A'])

    # --- diagnostics for the best model of experiment A -----------------------
    ranked = summaries['A'][summaries['A'].Algorithm != 'Baseline (mean)'].sort_values('RMSE')
    best = ranked.iloc[0]['Algorithm']
    print(f'\nBest model in experiment A: {best}')
    pipe = models()[best]
    pred = cross_val_predict(pipe, X, y, cv=kfold, n_jobs=1)
    pd.DataFrame({'date': df['date'], 'observed': y, 'predicted': pred,
                  'residual': y - pred, 'vz_day': df['ctx_vz_day']}
                 ).to_csv(OUT / 'predictions_best.csv', index=False)

    pipe.fit(X, y)
    imp = permutation_importance(pipe, X, y, n_repeats=20, random_state=SEED,
                                 scoring='neg_root_mean_squared_error', n_jobs=-1)
    (pd.DataFrame({'feature': feats, 'importance': imp.importances_mean, 'sd': imp.importances_std})
       .sort_values('importance', ascending=False)
       .assign(model=best)
       .to_csv(OUT / 'permutation_importance.csv', index=False))

    # self-check: the benchmark is meaningless if the models cannot beat the mean
    a = summaries['A'].set_index('Algorithm')
    assert a.loc['Baseline (mean)', 'R2'] < 0.02, a.loc['Baseline (mean)', 'R2']
    assert a.loc[best, 'R2'] > a.loc['Baseline (mean)', 'R2'] + 0.2, 'no model beats the mean'
    assert (a['RMSE'] > 0).all() and a['RMSE'].max() < 3 * y.std()
    assert summaries['B'].set_index('Algorithm').loc[best, 'R2'] <= a.loc[best, 'R2'] + 1e-9, \
        'blocked CV should not beat shuffled CV on an autocorrelated series'
    print('self-check ok ->', OUT.relative_to(ROOT))


def write_table1(summary: pd.DataFrame):
    """Table 1 in the layout the assignment prescribes."""
    t = summary[summary.Algorithm != 'Baseline (mean)'].copy()
    lines = ['| Algorithm | Number of features | Number of targets | k-fold validation | '
             'RMSE (ug/m3) | R2 |', '|---|---|---|---|---|---|']
    for _, r in t.iterrows():
        lines.append(f"| {r['Algorithm']} | {r['Number of features']} | {r['Number of targets']} | "
                     f"{r['k-fold validation']} | {r['RMSE']:.3f} +- {r['RMSE_sd']:.3f} | "
                     f"{r['R2']:.3f} +- {r['R2_sd']:.3f} |")
    (OUT / 'table1.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
