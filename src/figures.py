"""Every figure used in the report, the article and the slide deck.

Colours come from a validated categorical palette (blue / orange / aqua, light surface);
correlations use a diverging blue-grey-orange ramp with a neutral midpoint, magnitudes a
single-hue ramp. No figure uses two y-scales: where two series differ in magnitude they are
drawn as stacked panels or on a log axis.

Run after build_features.py and run_models.py. Writes PNG at 200 dpi into results/figures/.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / 'results'
FIG = RES / 'figures'
PROC = ROOT / 'data' / 'processed' / 'karaganda_modelling.csv'
KAZ = ROOT / 'data' / 'raw' / 'kazhydromet'

BLUE, ORANGE, AQUA, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, INK2, MUTED = '#0b0b0b', '#52514e', '#8a8984'
SURFACE, GRID = '#fcfcfb', '#e3e2de'
DIVERGING = LinearSegmentedColormap.from_list('bgo', ['#2a78d6', '#e8e8e6', '#eb6834'])
SEQUENTIAL = LinearSegmentedColormap.from_list('blues', ['#eef4fc', '#2a78d6', '#173e6e'])

SMOOTH_DAYS = 31           # window of the circular smoother on the day-of-year climatology
WHO_ANNUAL_PM25 = 5.0      # WHO 2021 air quality guideline, annual mean, ug/m3
WHO_DAILY_PM25 = 15.0      # WHO 2021 air quality guideline, 24-hour mean, ug/m3
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
CITY_EN = {'Караганда': 'Karaganda', 'Петропавловск': 'Petropavlovsk', 'Шубарши': 'Shubarshi',
           'Атырау': 'Atyrau', 'Темиртау': 'Temirtau', 'Балхаш': 'Balkhash', 'Алматы': 'Almaty',
           'Астана': 'Astana', 'Усть-Каменогорск': 'Ust-Kamenogorsk', 'Шымкент': 'Shymkent',
           'Актобе': 'Aktobe', 'Павлодар': 'Pavlodar', 'Жезказган': 'Zhezkazgan',
           'Риддер': 'Ridder', 'Семей': 'Semey', 'Костанай': 'Kostanay', 'Тараз': 'Taraz',
           'Актау': 'Aktau', 'Уральск': 'Uralsk', 'Кызылорда': 'Kyzylorda', 'Экибастуз': 'Ekibastuz',
           'Сарань': 'Saran', 'Абай': 'Abay', 'Туркестан': 'Turkestan', 'Кокшетау': 'Kokshetau', 'Сатпаев': 'Satpayev', 'Талгар': 'Talgar',
           'Аксу': 'Aksu', 'Жанаозен': 'Zhanaozen', 'Степногорск': 'Stepnogorsk'}


def style(ax, title='', xlabel='', ylabel=''):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    if title:
        ax.set_title(title, color=INK, fontsize=11.5, loc='left', pad=10, fontweight='bold')
    ax.set_xlabel(xlabel, color=INK2, fontsize=9.5)
    ax.set_ylabel(ylabel, color=INK2, fontsize=9.5)
    return ax


def top_legend(ax, handles, ncol=3):
    """Legend on its own line above the axes, so it never overlaps the left-aligned title."""
    ax.set_title(ax.get_title(loc='left'), color=INK, fontsize=11.5, loc='left', pad=34, fontweight='bold')
    return ax.legend(handles=handles, frameon=False, fontsize=9.5, labelcolor=INK2, ncol=ncol,
                     loc='lower right', bbox_to_anchor=(1.0, 1.0))


def save(fig, name):
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(FIG / name, dpi=200, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)
    print('  ', name)


# --------------------------------------------------------------------------- data
def load():
    d = pd.read_csv(PROC, parse_dates=['date'])
    series = pd.read_csv(KAZ / 'krg_series.csv')
    vz = pd.read_csv(KAZ / 'krg_vz_days.csv', parse_dates=['date'])
    rank = pd.read_csv(KAZ / 'national' / 'kz_city_ranking.csv')
    return d, series, vz, rank


# --------------------------------------------------------------------------- figures
def fig01_timeseries(d):
    fig, ax = plt.subplots(figsize=(11, 4))
    style(ax, 'Daily mean PM2.5 in Karaganda, CAMS reanalysis',
          ylabel='PM2.5, ug/m3')
    for year in range(d.date.dt.year.min(), d.date.dt.year.max() + 2):
        ax.axvspan(pd.Timestamp(year - 1, 10, 1), pd.Timestamp(year, 4, 1),
                   color='#f0eeea', zorder=0)
    ax.plot(d.date, d.pm2_5, color=MUTED, linewidth=0.6, alpha=0.75, zorder=2)
    ax.plot(d.date, d.pm2_5.rolling(30, center=True).mean(), color=BLUE, linewidth=2, zorder=3)
    ax.axhline(WHO_DAILY_PM25, color=ORANGE, linewidth=1.5, linestyle='--', zorder=4)
    ax.text(d.date.iloc[15], WHO_DAILY_PM25 + 2.6, 'WHO 24-hour guideline, 15 ug/m3',
            color=ORANGE, fontsize=9)
    ax.set_xlim(d.date.min(), d.date.max())
    ax.legend(handles=[Line2D([], [], color=MUTED, lw=1, label='Daily mean'),
                       Line2D([], [], color=BLUE, lw=2, label='30-day centred mean'),
                       Patch(facecolor='#f0eeea', label='Heating season (Oct-Mar)')],
              frameon=False, fontsize=9, labelcolor=INK2, loc='upper right', ncol=3)
    save(fig, 'fig01_pm25_timeseries.png')


def fig02_monthly(d):
    g = [d.loc[d.date.dt.month == m, 'pm2_5'].values for m in range(1, 13)]
    fig, ax = plt.subplots(figsize=(9, 4))
    style(ax, 'Monthly distribution of daily PM2.5, Karaganda 2022-2026',
          ylabel='PM2.5, ug/m3')
    bp = ax.boxplot(g, patch_artist=True, widths=0.6, showfliers=True,
                    flierprops=dict(marker='o', markersize=2.5, markerfacecolor=MUTED,
                                    markeredgecolor='none', alpha=0.5),
                    medianprops=dict(color=SURFACE, linewidth=1.8),
                    whiskerprops=dict(color=MUTED, linewidth=1),
                    capprops=dict(color=MUTED, linewidth=1))
    heating = {1, 2, 3, 10, 11, 12}
    for i, box in enumerate(bp['boxes'], 1):
        box.set(facecolor=BLUE if i in heating else AQUA, edgecolor=SURFACE, linewidth=1.5)
    ax.set_xticklabels(MONTHS)
    ax.axhline(WHO_DAILY_PM25, color=ORANGE, linewidth=1.5, linestyle='--')
    ax.text(0.6, WHO_DAILY_PM25 + 1, 'WHO 24-hour guideline', color=ORANGE, fontsize=9)
    ax.legend(handles=[Patch(facecolor=BLUE, label='Heating season'),
                       Patch(facecolor=AQUA, label='Warm season')],
              frameon=False, fontsize=9, labelcolor=INK2, loc='upper right')
    save(fig, 'fig02_monthly_climatology.png')


def fig03_seasonal(d):
    """Split daily PM2.5 into a smooth annual cycle, a slow trend and a synoptic residual.

    STL with period=365 is the obvious tool and is wrong here: with only four years the seasonal
    sub-series holds four points per day of year, so the smoother cannot separate the annual cycle
    from synoptic noise and reports most of the weather as "seasonal". The day-of-year climatology
    below does the separation the claim actually needs.
    """
    s = d.set_index('date').pm2_5.asfreq('D').interpolate()
    doy = s.index.dayofyear
    clim = s.groupby(doy).mean().reindex(range(1, 367)).interpolate()
    wrapped = pd.concat([clim.iloc[-SMOOTH_DAYS:], clim, clim.iloc[:SMOOTH_DAYS]])
    clim_s = wrapped.rolling(SMOOTH_DAYS, center=True, min_periods=1).mean().iloc[SMOOTH_DAYS:-SMOOTH_DAYS]
    seasonal = pd.Series(doy.map(clim_s).values, index=s.index)
    trend = (s - seasonal).rolling(365, center=True, min_periods=120).mean()
    resid = s - seasonal - trend
    comp = pd.DataFrame({'seasonal': seasonal - seasonal.mean(),
                         'trend': trend - trend.mean(), 'residual': resid}).dropna()
    share = comp.var() / s.loc[comp.index].var() * 100

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7))
    style(a1, f'Annual cycle of daily PM2.5: the {SMOOTH_DAYS}-day smoothed day-of-year mean over 2022-2026',
          ylabel='PM2.5, ug/m3')
    a1.plot(clim_s.index, clim_s.values, color=BLUE, linewidth=2.4)
    a1.fill_between(clim_s.index, s.mean(), clim_s.values, where=clim_s.values >= s.mean(),
                    color=BLUE, alpha=0.12)
    a1.axhline(s.mean(), color=MUTED, linestyle=':', linewidth=1.2)
    a1.text(8, s.mean() + 0.12, f'record mean {s.mean():.1f}', color=INK2, fontsize=9)
    a1.annotate(f'peak {clim_s.max():.1f}', (clim_s.idxmax(), clim_s.max()), xytext=(12, 6),
                textcoords='offset points', color=ORANGE, fontsize=9.5, fontweight='bold')
    a1.annotate(f'trough {clim_s.min():.1f}', (clim_s.idxmin(), clim_s.min()), xytext=(12, -14),
                textcoords='offset points', color=ORANGE, fontsize=9.5, fontweight='bold')
    a1.plot([clim_s.idxmax(), clim_s.idxmin()], [clim_s.max(), clim_s.min()], 'o',
            color=ORANGE, markersize=9)
    starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    a1.set_xticks(starts, MONTHS)
    a1.set_xlim(1, 366)

    style(a2, 'What is left after removing that cycle and the slow trend: synoptic variability',
          ylabel='Residual, ug/m3')
    a2.axhline(0, color=MUTED, linewidth=1)
    a2.plot(resid.index, resid.values, color=AQUA, linewidth=0.7)
    a2.set_xlim(s.index.min(), s.index.max())
    a2.text(0.006, 0.95,
            f'variance share of the daily series:  annual cycle {share["seasonal"]:.1f} %   '
            f'trend {share["trend"]:.1f} %   synoptic residual {share["residual"]:.1f} %',
            transform=a2.transAxes, color=INK, fontsize=10, va='top', fontweight='bold')
    fig.tight_layout()
    save(fig, 'fig03_seasonal_decomposition.png')
    share.round(2).to_csv(RES / 'seasonal_variance_share.csv', header=['percent_of_variance'])
    clim_s.round(2).to_csv(RES / 'doy_climatology.csv', header=['pm2_5_ugm3'], index_label='day_of_year')


def fig04_cams_vs_ground(d, series):
    kh = series[(series.pollutant == 'PM2.5') & (series.granularity == 'quarter')].copy()
    kh['ug'] = kh.mean_mgm3 * 1000
    q = d.set_index('date').pm2_5.resample('QE').mean()
    q.index = [f'{t.year}Q{t.quarter}' for t in q.index]
    common = [p for p in kh.period if p in q.index]
    kh = kh.set_index('period').loc[common]
    cams = q.loc[common]
    x = np.arange(len(common))

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7))
    style(a1, 'Quarterly mean PM2.5: ground network and CAMS reanalysis (log scale)',
          ylabel='PM2.5, ug/m3 (log)')
    a1.set_yscale('log')
    a1.plot(x, kh.ug.values, 'o-', color=ORANGE, linewidth=2, markersize=8)
    a1.plot(x, cams.values, 'o-', color=BLUE, linewidth=2, markersize=8)
    a1.text(x[-1] + 0.22, kh.ug.values[-1], 'Kazhydromet\nposts 6 and 8',
            color=ORANGE, fontsize=9.5, fontweight='bold', va='center')
    a1.text(x[-1] + 0.22, cams.values[-1], 'CAMS\n40 km grid cell',
            color=BLUE, fontsize=9.5, fontweight='bold', va='center')
    a1.axhline(WHO_ANNUAL_PM25, color=MUTED, linewidth=1.2, linestyle=':')
    a1.text(0.05, WHO_ANNUAL_PM25 * 1.07, 'WHO annual guideline, 5 ug/m3', color=INK2, fontsize=8.5)
    for xi, (k, c) in enumerate(zip(kh.ug.values, cams.values)):
        a1.annotate(f'x{k / c:.0f}', (xi, np.sqrt(k * c)), ha='center', va='center',
                    fontsize=8, color=INK2,
                    bbox=dict(boxstyle='round,pad=0.2', fc=SURFACE, ec='none'))
    a1.set_xticks(x); a1.set_xticklabels(common, rotation=45, ha='right')
    a1.set_ylim(3.2, kh.ug.max() * 1.9)
    a1.set_xlim(-0.5, len(common) + 1.9)

    style(a2, 'The same two series normalised to their own period mean: the seasonal shape agrees',
          ylabel='Ratio to series mean')
    a2.plot(x, kh.ug.values / kh.ug.mean(), 'o-', color=ORANGE, linewidth=2, markersize=8)
    a2.plot(x, cams.values / cams.mean(), 'o-', color=BLUE, linewidth=2, markersize=8)
    a2.axhline(1, color=MUTED, linewidth=1, linestyle=':')
    r = np.corrcoef(kh.ug.values, cams.values)[0, 1]
    a2.text(0.01, 0.94, f'Pearson r = {r:.2f} over {len(common)} quarters',
            transform=a2.transAxes, color=INK, fontsize=9.5, va='top')
    a2.set_xticks(x); a2.set_xticklabels(common, rotation=45, ha='right')
    a2.set_xlim(-0.5, len(common) + 1.9)
    a2.text(x[-1] + 0.22, kh.ug.values[-1] / kh.ug.mean(), 'Kazhydromet',
            color=ORANGE, fontsize=9.5, fontweight='bold', va='center')
    a2.text(x[-1] + 0.22, cams.values[-1] / cams.mean(), 'CAMS',
            color=BLUE, fontsize=9.5, fontweight='bold', va='center')
    fig.tight_layout()
    save(fig, 'fig04_cams_vs_kazhydromet.png')
    pd.DataFrame({'period': common, 'kazhydromet_ugm3': kh.ug.values,
                  'cams_ugm3': cams.values, 'ratio': kh.ug.values / cams.values}
                 ).round(2).to_csv(RES / 'cams_vs_kazhydromet.csv', index=False)


def fig05_vz_by_month(vz):
    counts = vz.date.dt.month.value_counts().reindex(range(1, 13), fill_value=0)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    style(ax, f'High-pollution days recorded by Kazhydromet in Karaganda, 2021-2025 (n={len(vz)})',
          ylabel='Number of days')
    heating = {1, 2, 3, 10, 11, 12}
    bars = ax.bar(MONTHS, counts.values, width=0.68,
                  color=[BLUE if m in heating else AQUA for m in range(1, 13)], zorder=3)
    for b, v in zip(bars, counts.values):
        if v:
            ax.text(b.get_x() + b.get_width() / 2, v + 0.7, str(v), ha='center',
                    color=INK2, fontsize=9)
    ax.legend(handles=[Patch(facecolor=BLUE, label='Heating season'),
                       Patch(facecolor=AQUA, label='Warm season')],
              frameon=False, fontsize=9, labelcolor=INK2)
    save(fig, 'fig05_vz_days_by_month.png')
    counts.to_csv(RES / 'vz_days_by_month.csv', header=['days'])


def fig06_vz_meteorology():
    raw = pd.read_csv(ROOT / 'data' / 'raw' / 'open_meteo' / 'karaganda_daily.csv', parse_dates=['date'])
    raw = raw[(raw.date.dt.year <= 2025) & raw.date.dt.month.isin([1, 2, 3, 10, 11, 12])]
    panels = [('temperature_2m_mean', 'Mean temperature, C'),
              ('wind_speed_10m_mean', 'Mean wind speed, km/h'),
              ('blh_min_m', 'Minimum mixing depth, m'),
              ('surface_pressure_mean', 'Surface pressure, hPa')]
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.8))
    for ax, (col, label) in zip(axes, panels):
        style(ax, ylabel=label)
        groups = [raw.loc[raw.vz_day == 0, col].dropna(), raw.loc[raw.vz_day == 1, col].dropna()]
        bp = ax.boxplot(groups, patch_artist=True, widths=0.55, showfliers=False,
                        medianprops=dict(color=SURFACE, linewidth=1.8),
                        whiskerprops=dict(color=MUTED, linewidth=1),
                        capprops=dict(color=MUTED, linewidth=1))
        for box, c in zip(bp['boxes'], [AQUA, ORANGE]):
            box.set(facecolor=c, edgecolor=SURFACE, linewidth=1.5)
        ax.set_xticklabels(['Ordinary', 'High-\npollution'], fontsize=9)
    fig.suptitle('Heating-season meteorology on high-pollution days versus ordinary days, 2021-2025',
                 color=INK, fontsize=11.5, x=0.005, ha='left', y=1.02, fontweight='bold')
    fig.tight_layout()
    save(fig, 'fig06_vz_meteorology.png')
    rows = []
    for col, label in panels:
        rows.append({'variable': label,
                     'ordinary_median': raw.loc[raw.vz_day == 0, col].median(),
                     'high_pollution_median': raw.loc[raw.vz_day == 1, col].median()})
    pd.DataFrame(rows).round(1).to_csv(RES / 'vz_meteorology.csv', index=False)


def fig07_correlations(d):
    met = ['temperature_2m_mean', 'diurnal_range', 'wind_speed_10m_mean', 'wind_speed_10m_max',
           'blh_min_m', 'blh_mean_m', 'ventilation_index', 'surface_pressure_mean',
           'relative_humidity_2m_mean', 'precipitation_sum', 'snowfall_sum', 'heating_degree_days']
    pol = ['pm2_5', 'ctx_pm10', 'ctx_nitrogen_dioxide', 'ctx_sulphur_dioxide',
           'ctx_carbon_monoxide', 'ctx_ozone']
    labels_p = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    labels_m = ['Temperature', 'Diurnal range', 'Wind speed mean', 'Wind speed max',
                'Mixing depth min', 'Mixing depth mean', 'Ventilation index', 'Pressure',
                'Humidity', 'Precipitation', 'Snowfall', 'Heating degree days']
    c = d[met + pol].corr().loc[met, pol]
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    im = ax.imshow(c.values, cmap=DIVERGING, vmin=-0.7, vmax=0.7, aspect='auto')
    ax.set_xticks(range(len(pol)), labels_p, color=INK2, fontsize=9.5)
    ax.set_yticks(range(len(met)), labels_m, color=INK2, fontsize=9.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(len(met)):
        for j in range(len(pol)):
            v = c.values[i, j]
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=8.5,
                    color=SURFACE if abs(v) > 0.42 else INK)
    ax.set_title('Pearson correlation, daily meteorology against CAMS pollutants',
                 color=INK, fontsize=11.5, loc='left', pad=10, fontweight='bold')
    cb = fig.colorbar(im, ax=ax, shrink=0.72, pad=0.03)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK2, labelsize=8.5, length=0)
    save(fig, 'fig07_correlation_heatmap.png')
    c.round(3).to_csv(RES / 'correlation_matrix.csv')


def fig08_model_comparison():
    t = pd.read_csv(RES / 'table1_experiment_A.csv')
    t = t[t.Algorithm != 'Baseline (mean)'].sort_values('RMSE', ascending=False)
    base = pd.read_csv(RES / 'table1_experiment_A.csv').query("Algorithm == 'Baseline (mean)'").RMSE.iloc[0]
    fig, ax = plt.subplots(figsize=(9, 5))
    style(ax, 'Ten-fold cross-validated RMSE by algorithm (experiment A)',
          xlabel='RMSE, ug/m3 (lower is better)')
    y = np.arange(len(t))
    best = t.RMSE.min()
    colours = [ORANGE if r == best else BLUE for r in t.RMSE]
    ax.barh(y, t.RMSE, xerr=t.RMSE_sd, height=0.66, color=colours, zorder=3,
            error_kw=dict(ecolor=MUTED, elinewidth=1.2, capsize=3))
    ax.set_yticks(y, t.Algorithm, color=INK2, fontsize=9.5)
    for yi, (r, sd, r2) in enumerate(zip(t.RMSE, t.RMSE_sd, t.R2)):
        ax.text(r + sd + 0.16, yi, f'{r:.2f}    R2 {r2:.2f}', va='center', fontsize=9, color=INK2)
    ax.axvline(base, color=MUTED, linestyle='--', linewidth=1.3, zorder=4)
    ax.set_xlim(0, t.RMSE.max() + 2.6)
    top_legend(ax, [Patch(facecolor=ORANGE, label='Best model'),
                    Patch(facecolor=BLUE, label='Other algorithms'),
                    Line2D([], [], color=MUTED, ls='--', label=f'Mean baseline, {base:.2f}')])
    save(fig, 'fig08_model_comparison.png')


def fig09_observed_predicted():
    p = pd.read_csv(RES / 'predictions_best.csv', parse_dates=['date'])
    model = pd.read_csv(RES / 'permutation_importance.csv').model.iloc[0]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
    style(a1, f'Out-of-fold predictions, {model} (experiment A)',
          xlabel='Observed PM2.5, ug/m3', ylabel='Predicted PM2.5, ug/m3')
    lim = [0, max(p.observed.max(), p.predicted.max()) * 1.03]
    hb = a1.hexbin(p.observed, p.predicted, gridsize=38, cmap=SEQUENTIAL, mincnt=1, linewidths=0)
    a1.plot(lim, lim, color=ORANGE, linewidth=1.6, linestyle='--', zorder=5)
    a1.text(lim[1] * 0.52, lim[1] * 0.93, '1:1 line', color=ORANGE, fontsize=9)
    a1.set_xlim(lim); a1.set_ylim(lim)
    cb = fig.colorbar(hb, ax=a1, shrink=0.85, pad=0.02, label='days')
    cb.outline.set_visible(False); cb.ax.tick_params(colors=INK2, labelsize=8.5, length=0)
    cb.set_label('Days', color=INK2, fontsize=9)

    style(a2, 'Residuals against observed concentration',
          xlabel='Observed PM2.5, ug/m3', ylabel='Residual (observed - predicted), ug/m3')
    a2.scatter(p.observed, p.residual, s=9, color=BLUE, alpha=0.35, linewidths=0)
    a2.axhline(0, color=ORANGE, linewidth=1.6, linestyle='--')
    fig.tight_layout()
    save(fig, 'fig09_observed_vs_predicted.png')


def fig10_importance():
    imp = pd.read_csv(RES / 'permutation_importance.csv').head(14).iloc[::-1]
    nice = {'ventilation_index': 'Ventilation index', 'wind_speed_10m_mean': 'Wind speed, mean',
            'wind_speed_10m_max': 'Wind speed, max', 'blh_mean_m': 'Mixing depth, mean',
            'blh_min_m': 'Mixing depth, min', 'temperature_2m_mean': 'Temperature, mean',
            'temperature_2m_min': 'Temperature, min', 'temperature_2m_max': 'Temperature, max',
            'diurnal_range': 'Diurnal temperature range', 'heating_degree_days': 'Heating degree days',
            'relative_humidity_2m_mean': 'Relative humidity', 'surface_pressure_mean': 'Surface pressure',
            'precipitation_sum': 'Precipitation', 'snowfall_sum': 'Snowfall',
            'wind_dir_sin': 'Wind direction (sin)', 'wind_dir_cos': 'Wind direction (cos)',
            'doy_sin': 'Day of year (sin)', 'doy_cos': 'Day of year (cos)',
            'is_heating_season': 'Heating season flag', 'is_weekend': 'Weekend flag',
            'trend_days': 'Linear time trend'}
    fig, ax = plt.subplots(figsize=(8.5, 5))
    model = imp.model.iloc[0]
    style(ax, f'Permutation importance, {model} (increase in RMSE when a predictor is shuffled)',
          xlabel='Increase in RMSE, ug/m3')
    y = np.arange(len(imp))
    ax.barh(y, imp.importance, xerr=imp.sd, height=0.66, color=BLUE, zorder=3,
            error_kw=dict(ecolor=MUTED, elinewidth=1.1, capsize=2.5))
    ax.set_yticks(y, [nice.get(f, f) for f in imp.feature], color=INK2, fontsize=9.5)
    save(fig, 'fig10_permutation_importance.png')


def fig11_experiments():
    frames = [pd.read_csv(RES / f'table1_experiment_{k}.csv') for k in 'ABCD']
    t = pd.concat(frames)
    t = t[t.Algorithm != 'Baseline (mean)']
    order = pd.read_csv(RES / 'table1_experiment_A.csv').sort_values('RMSE').Algorithm.tolist()
    order = [a for a in order if a != 'Baseline (mean)']
    titles = {'A': 'A: shuffled 10-fold', 'B': 'B: blocked 10-fold',
              'C': 'C: next-day forecast', 'D': 'D: log target'}
    fig, ax = plt.subplots(figsize=(11, 4.6))
    style(ax, 'Cross-validated R2 under four validation designs', ylabel='R2')
    x = np.arange(len(order))
    w = 0.2
    for i, (key, colour) in enumerate(zip('ABCD', [BLUE, ORANGE, AQUA, YELLOW])):
        vals = t[t.Experiment == key].set_index('Algorithm').reindex(order).R2
        ax.bar(x + (i - 1.5) * w, vals, width=w * 0.92, color=colour, zorder=3)
    ax.axhline(0, color=INK2, linewidth=1)
    ax.set_xticks(x, [a.replace(' Regression', '').replace('Adaptive Boosting (AdaBoost)', 'AdaBoost')
                      for a in order], rotation=28, ha='right', fontsize=9)
    top_legend(ax, [Patch(facecolor=c, label=titles[k])
                    for k, c in zip('ABCD', [BLUE, ORANGE, AQUA, YELLOW])], ncol=4)
    save(fig, 'fig11_experiment_comparison.png')


def fig12_city_ranking(rank):
    t = rank.head(15).iloc[::-1].copy()
    t['name'] = t.city.map(lambda c: CITY_EN.get(c, c))
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    style(ax, 'Kazhydromet composite pollution score, 15 worst settlements of Kazakhstan (H1 2026)',
          xlabel='Composite score')
    y = np.arange(len(t))
    colours = [ORANGE if c == 'Караганда' else BLUE for c in t.city]
    ax.barh(y, t.score, height=0.66, color=colours, zorder=3)
    ax.set_yticks(y, t.name, color=INK2, fontsize=9.5)
    for yi, (sc, v) in enumerate(zip(t.score, t.vz_cases_H1_2026)):
        tail = f'    {v} high-pollution cases' if v else ''
        ax.text(sc + 0.15, yi, f'{sc:.1f}{tail}', va='center', fontsize=8.5, color=INK2)
    ax.set_xlim(0, t.score.max() + 7)
    top_legend(ax, [Patch(facecolor=ORANGE, label='Karaganda, the study city'),
                    Patch(facecolor=BLUE, label='Other settlements')], ncol=2)
    save(fig, 'fig12_city_ranking.png')


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    d, series, vz, rank = load()
    print('figures ->', FIG.relative_to(ROOT))
    fig01_timeseries(d)
    fig02_monthly(d)
    fig03_seasonal(d)
    fig04_cams_vs_ground(d, series)
    fig05_vz_by_month(vz)
    fig06_vz_meteorology()
    fig07_correlations(d)
    fig08_model_comparison()
    fig09_observed_predicted()
    fig10_importance()
    fig11_experiments()
    fig12_city_ranking(rank)

    produced = sorted(p.name for p in FIG.glob('*.png'))
    assert len(produced) == 12, produced
    assert all(p.stat().st_size > 20_000 for p in FIG.glob('*.png')), 'a figure came out empty'
    print(f'self-check ok: {len(produced)} figures')


if __name__ == '__main__':
    main()
