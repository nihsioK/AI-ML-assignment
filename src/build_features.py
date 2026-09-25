"""Build the modelling table for Karaganda PM2.5 from the raw ERA5 + CAMS daily series.

Input : data/raw/open_meteo/karaganda_daily.csv  (weather, CAMS pollutants, high-pollution-day flag)
Output: data/processed/karaganda_modelling.csv

Design notes
------------
The target is the daily mean PM2.5 concentration (CAMS global reanalysis, ug/m3).
Predictors are meteorological and calendar variables only: the research question is how
much of the day-to-day variance of PM2.5 in a coal-heated continental city is explained by
dispersion conditions, so no pollutant is allowed on the predictor side of the primary task.

Three physically motivated derived features are added on top of the raw ERA5 fields:
  diurnal_range        proxy for radiative cooling and nocturnal inversion strength
  heating_degree_days  proxy for heating demand, the dominant winter emission driver
  ventilation_index    wind speed x mixing depth, the standard dispersion metric

Wind direction and day of year are circular and are encoded as sine/cosine pairs so that
31 December is adjacent to 1 January and 359 degrees is adjacent to 1 degree.
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw' / 'open_meteo' / 'karaganda_daily.csv'
OUT = ROOT / 'data' / 'processed' / 'karaganda_modelling.csv'

TARGET = 'pm2_5'
HEATING_BASE_C = 18.0          # standard degree-day base temperature
HEATING_MONTHS = {10, 11, 12, 1, 2, 3}


def build(raw_path: Path = RAW) -> pd.DataFrame:
    d = pd.read_csv(raw_path, parse_dates=['date']).sort_values('date').reset_index(drop=True)
    d = d[d['cams_pm2_5'].notna()].reset_index(drop=True)

    f = pd.DataFrame({'date': d['date']})

    # --- raw meteorology -------------------------------------------------
    for c in ['temperature_2m_mean', 'temperature_2m_min', 'temperature_2m_max',
              'wind_speed_10m_mean', 'wind_speed_10m_max',
              'precipitation_sum', 'snowfall_sum',
              'relative_humidity_2m_mean', 'surface_pressure_mean',
              'blh_min_m', 'blh_mean_m']:
        f[c] = d[c]

    # --- derived meteorology ---------------------------------------------
    f['diurnal_range'] = d['temperature_2m_max'] - d['temperature_2m_min']
    f['heating_degree_days'] = (HEATING_BASE_C - d['temperature_2m_mean']).clip(lower=0)
    f['ventilation_index'] = d['wind_speed_10m_mean'] * d['blh_mean_m']

    # --- circular encodings ----------------------------------------------
    wd = np.deg2rad(d['wind_direction_10m_dominant'])
    f['wind_dir_sin'], f['wind_dir_cos'] = np.sin(wd), np.cos(wd)
    doy = np.deg2rad(d['date'].dt.dayofyear / 365.25 * 360)
    f['doy_sin'], f['doy_cos'] = np.sin(doy), np.cos(doy)

    # --- calendar ---------------------------------------------------------
    f['is_heating_season'] = d['date'].dt.month.isin(HEATING_MONTHS).astype(int)
    f['is_weekend'] = (d['date'].dt.dayofweek >= 5).astype(int)
    f['trend_days'] = (d['date'] - d['date'].min()).dt.days

    # --- targets and context columns (not predictors) ---------------------
    f[TARGET] = d['cams_pm2_5']
    for c in ['pm10', 'nitrogen_dioxide', 'sulphur_dioxide', 'carbon_monoxide', 'ozone']:
        f[f'ctx_{c}'] = d[f'cams_{c}']
    f['ctx_vz_day'] = d['vz_day']

    return f


def feature_columns(df: pd.DataFrame) -> list[str]:
    """Predictor columns: everything that is not the date, the target or a context column."""
    return [c for c in df.columns if c not in ('date', TARGET) and not c.startswith('ctx_')]


if __name__ == '__main__':
    df = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    feats = feature_columns(df)
    # self-check: the pipeline must not silently change shape, leak the target or lose the season
    assert len(df) > 1400, len(df)
    assert df[TARGET].notna().all() and (df[TARGET] > 0).all()
    assert len(feats) == 21, (len(feats), feats)
    assert not any(c.startswith('ctx_') or c == TARGET for c in feats), 'target leaked into features'
    assert (df['date'].diff().dropna().dt.days == 1).all(), 'gap in the daily index'
    winter = df.loc[df.is_heating_season == 1, TARGET].mean()
    summer = df.loc[df.is_heating_season == 0, TARGET].mean()
    assert winter > summer, (winter, summer)
    assert df['ventilation_index'].isna().sum() == df['blh_mean_m'].isna().sum()

    print(f"self-check ok -> {OUT.relative_to(ROOT)}")
    print(f"rows {len(df)}  {df.date.min().date()}..{df.date.max().date()}  features {len(feats)}  target {TARGET}")
    print(f"PM2.5 mean {df[TARGET].mean():.2f}  sd {df[TARGET].std():.2f}  "
          f"heating season {winter:.2f} vs warm season {summer:.2f} ug/m3")
    print(f"missing values: {dict(df[feats].isna().sum()[lambda s: s > 0])}")
