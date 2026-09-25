"""Build the Case Study Task 1 deliverables: figures, report and slide deck.

This is the light version of the project, scoped strictly to the case study brief:
descriptive analysis of air pollution in Karaganda, no machine-learning benchmark.
The full study with the eleven-algorithm benchmark lives one level up.

Three figures are drawn here; five are reused from the main study and copied in so that
case-study-1/ can be handed in on its own.

Run:  python case-study-1/build.py
"""
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG = HERE / 'figures'
KAZ = ROOT / 'data' / 'raw' / 'kazhydromet'
sys.path.insert(0, str(ROOT / 'src'))

BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, INK2, MUTED, SURFACE, GRID = '#0b0b0b', '#52514e', '#8a8984', '#fcfcfb', '#e3e2de'
SEQUENTIAL = LinearSegmentedColormap.from_list('blues', ['#f3f7fd', '#9dc2ec', '#2a78d6', '#173e6e'])

# figures taken unchanged from the main study, with the name they get here
REUSED = {
    'fig01_pm25_timeseries.png': 'fig1_daily_pm25.png',
    'fig02_monthly_climatology.png': 'fig2_monthly_pm25.png',
    'fig05_vz_days_by_month.png': 'fig5_episodes_by_month.png',
    'fig06_vz_meteorology.png': 'fig6_episode_weather.png',
    'fig12_city_ranking.png': 'fig3_city_ranking.png',
}

CITY_EN = {'Караганда': 'Karaganda', 'Петропавловск': 'Petropavlovsk', 'Шубарши': 'Shubarshi',
           'Атырау': 'Atyrau', 'Астана': 'Astana', 'Актобе': 'Aktobe', 'Алматы': 'Almaty',
           'Темиртау': 'Temirtau', 'Абай': 'Abay', 'Жезказган': 'Zhezkazgan', 'Сатпаев': 'Satpayev',
           'Павлодар': 'Pavlodar', 'Туркестан': 'Turkestan', 'Талгар': 'Talgar',
           'Усть-Каменогорск': 'Ust-Kamenogorsk'}

POLLUTANT_EN = {'PM2.5': 'PM2.5', 'PM10': 'PM10', 'Фенол': 'Phenol',
                'Взвешенные частицы (пыль)': 'Suspended dust', 'Формальдегид': 'Formaldehyde',
                'Озон': 'Ozone', 'Диоксид азота': 'Nitrogen dioxide',
                'Диоксид серы': 'Sulphur dioxide', 'Оксид углерода': 'Carbon monoxide',
                'Оксид азота': 'Nitrogen oxide'}

AREA_EN = {'Караганда': 'Karaganda', 'Бухар-Жырауский район': 'Bukhar-Zhyrau district',
           'Сарань': 'Saran', 'Темиртау': 'Temirtau', 'Шахтинск': 'Shakhtinsk',
           'Шетский район': 'Shet district', 'Жанааркинский район': 'Zhanaarka district',
           'Балхаш': 'Balkhash', 'Абайский район': 'Abay district',
           'Улытауский район': 'Ulytau district', 'Актогайский район': 'Aktogay district',
           'Каркаралинсий район': 'Karkaraly district', 'Жезказган': 'Zhezkazgan',
           'Каражал': 'Karazhal', 'Нуринский район': 'Nura district',
           'Осакаровский район': 'Osakarovka district'}


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


def save(fig, name):
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(FIG / name, dpi=200, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)
    print('  ', name)


def fig4_city_heatmap():
    """City comparison heatmap, the 'heatmaps comparing cities' item of the brief.

    Built from the Kazhydromet national ranking, which is verified data. A per-city
    concentration series is not available: the bulletin tables for cities other than Karaganda
    use a different column layout that the parser does not read reliably.
    """
    r = pd.read_csv(KAZ / 'national' / 'kz_city_ranking.csv').head(15).copy()
    r['name'] = r.city.map(lambda c: CITY_EN.get(c, c))
    cols = {'level_H1_2026': 'Pollution level\nH1 2026',
            'level_Q3_2025': 'Pollution level\nQ3 2025',
            'chronic_2021_2025': 'Chronically\npolluted',
            'vz_cases_H1_2026': 'High-pollution\nepisodes',
            'score': 'Composite\nscore'}
    m = r[list(cols)].copy()
    norm = m.copy()
    for c in m:                                    # each indicator on its own 0-1 scale
        v = m[c].astype(float)
        if c == 'vz_cases_H1_2026':                # Karaganda's 244 would flatten everything else
            v = np.log1p(v)
        norm[c] = 0.0 if v.max() == v.min() else (v - v.min()) / (v.max() - v.min())

    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    ax.imshow(norm.values, cmap=SEQUENTIAL, vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(len(cols)), list(cols.values()), color=INK2, fontsize=9)
    ax.set_yticks(range(len(r)), r.name, color=INK2, fontsize=9.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(len(r)):
        for j, c in enumerate(cols):
            raw = m.iloc[i, j]
            txt = f'{raw:.1f}' if c == 'score' else ('yes' if c == 'chronic_2021_2025' and raw
                                                     else ('no' if c == 'chronic_2021_2025' else f'{int(raw)}'))
            ax.text(j, i, txt, ha='center', va='center', fontsize=9,
                    color=SURFACE if norm.iloc[i, j] > 0.55 else INK)
    ax.set_title('Air pollution across Kazakhstan: the 15 worst-ranked settlements, Kazhydromet H1 2026',
                 color=INK, fontsize=11.5, loc='left', pad=12, fontweight='bold')
    ax.text(0, -0.155, 'Colour scales each column to its own range, darker is worse; the episode '
                       'column is log-scaled so that Karaganda does not flatten the rest. '
                       'Pollution level runs 1 (low) to 4 (very high).',
            transform=ax.transAxes, color=MUTED, fontsize=8.5)
    save(fig, 'fig4_city_heatmap.png')
    r[['rank', 'name'] + list(cols)].to_csv(HERE / 'city_comparison.csv', index=False)


def fig7_pollutant_ranking():
    """Which pollutants exceed the Kazakh limit, and by how much."""
    s = pd.read_csv(KAZ / 'krg_series.csv')
    q = s[s.granularity == 'quarter']
    agg = (q.groupby('pollutant')
             .agg(mean_ratio=('ratio_pdk_ss', 'mean'), share_above=('np_pct', 'mean'))
             .loc[lambda d: d.index.isin(POLLUTANT_EN)]
             .sort_values('mean_ratio'))
    agg.index = [POLLUTANT_EN[i] for i in agg.index]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    style(ax, 'Karaganda: average exceedance of the Kazakh 24-hour limit, 16 quarters 2021-2026',
          xlabel='Multiple of the permissible limit (1.0 = at the limit)')
    y = np.arange(len(agg))
    colours = [ORANGE if v >= 1 else BLUE for v in agg.mean_ratio]
    ax.barh(y, agg.mean_ratio, height=0.66, color=colours, zorder=3)
    ax.set_yticks(y, agg.index, color=INK2, fontsize=9.5)
    ax.axvline(1.0, color=MUTED, linestyle='--', linewidth=1.4, zorder=4)
    ax.text(1.06, -0.75, 'permissible limit', color=INK2, fontsize=9)
    for yi, v in enumerate(agg.mean_ratio):
        ax.text(v + 0.08, yi, f'{v:.2f}x', va='center', fontsize=9, color=INK2)
    ax.set_xlim(0, agg.mean_ratio.max() + 0.8)
    save(fig, 'fig7_pollutant_ranking.png')
    agg.round(2).to_csv(HERE / 'pollutant_ranking.csv')


def fig8_sources():
    """Where the permitted emitters of the region sit."""
    src = pd.read_csv(KAZ / 'krg_sources.csv')
    counts = src.city.value_counts().head(12).iloc[::-1]
    names = [AREA_EN.get(c, c) for c in counts.index]

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    style(ax, 'Permitted emitting enterprises by city and district, Karaganda region',
          xlabel='Number of enterprises named in the Kazhydromet bulletin')
    y = np.arange(len(counts))
    colours = [ORANGE if n == 'Karaganda' else BLUE for n in names]
    ax.barh(y, counts.values, height=0.66, color=colours, zorder=3)
    ax.set_yticks(y, names, color=INK2, fontsize=9.5)
    for yi, v in enumerate(counts.values):
        ax.text(v + 0.15, yi, str(v), va='center', fontsize=9, color=INK2)
    ax.set_xlim(0, counts.max() + 2.5)
    save(fig, 'fig8_emission_sources.png')


NOTEBOOK = [
    ('md', """# Air pollution in Karaganda: exploratory analysis

Case Study Task 1. Descriptive analysis only, no machine learning: this notebook reproduces the
numbers and figures in `report.md`.

Run it from the `case-study-1` folder."""),

    ('code', """from pathlib import Path
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == 'case-study-1' else Path.cwd()
KAZ = ROOT / 'data' / 'raw' / 'kazhydromet'
pd.set_option('display.width', 140)
print('project root:', ROOT)"""),

    ('md', """## 1. How bad is Karaganda compared with other cities?"""),

    ('code', """rank = pd.read_csv(KAZ / 'national' / 'kz_city_ranking.csv')
print(f'{len(rank)} settlements ranked by Kazhydromet, H1 2026')
print(f'Karaganda: rank {rank["rank"].iloc[0]}, '
      f'score {rank.score.iloc[0]}, {rank.vz_cases_H1_2026.iloc[0]} episodes '
      f'out of {rank.vz_cases_H1_2026.sum()} nationwide '
      f'({100 * rank.vz_cases_H1_2026.iloc[0] / rank.vz_cases_H1_2026.sum():.0f}%)')
rank.head(10)[['rank', 'city', 'score', 'vz_cases_H1_2026', 'airkaz_sensors']]"""),

    ('md', """## 2. Which pollutants exceed the limits?

`ratio_pdk_ss` is the measured concentration divided by the Kazakh 24-hour permissible limit, so
a value above 1.0 means the limit was exceeded on average over the quarter."""),

    ('code', """series = pd.read_csv(KAZ / 'krg_series.csv')
quarters = series[series.granularity == 'quarter']

ranking = (quarters.groupby('pollutant')
           .agg(mean_ratio=('ratio_pdk_ss', 'mean'),
                worst_single=('ratio_pdk_mr', 'max'),
                share_above=('np_pct', 'mean'))
           .sort_values('mean_ratio', ascending=False))
ranking.round(2).head(10)"""),

    ('md', """PM2.5 is 5.6 times the limit on average and nothing else is close. Note that sulphur dioxide,
nitrogen dioxide and carbon monoxide stay below their limits: the problem is particles from
low-level sources, not gases from tall stacks."""),

    ('md', """## 3. Seasonality: the quarterly measurements"""),

    ('code', """pm = quarters[quarters.pollutant == 'PM2.5'].copy()
pm['quarter'] = pm.period.str[-1]
pm['ug_m3'] = pm.mean_mgm3 * 1000                       # the bulletins report mg/m3
print(pm.groupby('quarter').ug_m3.mean().round(0).rename('mean PM2.5, ug/m3').to_string())
print()
pm[['period', 'ug_m3', 'ratio_pdk_ss', 'np_pct']].round(2).to_string(index=False)"""),

    ('md', """Quarters 1 and 4, the heating season, run 1.5 to 2 times higher than quarters 2 and 3.

## 4. Seasonality: the measured episode record

These are the days on which Kazhydromet actually registered high pollution."""),

    ('code', """episodes = pd.read_csv(KAZ / 'krg_vz_days.csv', parse_dates=['date'])
by_month = episodes.date.dt.month.value_counts().reindex(range(1, 13), fill_value=0)
by_month.index = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
print(f'{len(episodes)} episode days, 2021-2025')
print(by_month.rename('days').to_string())
print()
print('by year: ', episodes.date.dt.year.value_counts().sort_index().to_dict())
print('by post: ', episodes.posts.value_counts().to_dict())"""),

    ('md', """Every episode falls between September and April, and all of them come from posts 6 and 8 in the
Prishakhtinsk district. Since 2024 only post 8 appears.

## 5. What weather produces an episode?

Restricted to heating-season days, so the comparison reflects the weather and not the calendar."""),

    ('code', """daily = pd.read_csv(ROOT / 'data/raw/open_meteo/karaganda_daily.csv', parse_dates=['date'])
heating = daily[(daily.date.dt.year <= 2025) & daily.date.dt.month.isin([1, 2, 3, 10, 11, 12])]

cols = ['temperature_2m_mean', 'wind_speed_10m_mean', 'blh_min_m', 'surface_pressure_mean']
table = heating.groupby('vz_day')[cols].median().T
table.columns = ['ordinary day', 'episode day']
print(f'{int(heating.vz_day.sum())} episode days vs {int((heating.vz_day == 0).sum())} ordinary days')
table.round(1)"""),

    ('md', """Wind speed halves and the mixing layer collapses from 135 to 30 metres. Frost, calm and high
pressure: a classic temperature inversion."""),

    ('code', """# correlation of PM2.5 with weather, whole record and split by season
cams = daily[daily.cams_pm2_5.notna()].copy()
cams['heating'] = cams.date.dt.month.isin([1, 2, 3, 10, 11, 12])

for label, sub in [('all year', cams), ('heating', cams[cams.heating]), ('warm', cams[~cams.heating])]:
    r = sub[['wind_speed_10m_mean', 'blh_min_m', 'temperature_2m_mean']].corrwith(sub.cams_pm2_5)
    print(f'{label:9s} (n={len(sub):4d})  ' + '  '.join(f'{k.split("_")[0]} {v:+.2f}' for k, v in r.items()))"""),

    ('md', """Both dispersion variables roughly double in strength during the heating season.

## 6. Comparison with the WHO guidelines

WHO 2021: 5 ug/m3 as an annual mean, 15 ug/m3 as a 24-hour mean."""),

    ('code', """WHO_ANNUAL, WHO_DAILY = 5.0, 15.0

print('--- reanalysis, the conservative estimate ---')
annual = cams.groupby(cams.date.dt.year).cams_pm2_5.mean()
for year, v in annual.items():
    print(f'  {year}: {v:5.2f} ug/m3   {v / WHO_ANNUAL:.1f}x the WHO annual guideline')
print(f'  days above the 24-hour guideline: {(cams.cams_pm2_5 > WHO_DAILY).sum()} of {len(cams)} '
      f'({100 * (cams.cams_pm2_5 > WHO_DAILY).mean():.1f}%)')

print()
print('--- ground measurements, the high estimate ---')
for _, row in pm.iterrows():
    print(f'  {row.period}: {row.ug_m3:5.0f} ug/m3   {row.ug_m3 / WHO_ANNUAL:.0f}x the WHO annual guideline')"""),

    ('md', """The two sources disagree by a factor of about 20. The 40 km reanalysis cell averages the city
with empty steppe and must underestimate; the ground posts sit next to coal-burning housing and
may overstate a city-wide mean. The honest reading is a range: **6 to 30 times the WHO guideline**.

## 7. Where the emissions come from"""),

    ('code', """sources = pd.read_csv(KAZ / 'krg_sources.csv')
print(f'{len(sources)} permitted enterprises across {sources.city.nunique()} cities and districts')
print()
print('Karaganda city:')
for name in sources[sources.city == 'Караганда'].source:
    print('  -', name)"""),

    ('md', """Coal extraction, coal chemistry, ferroalloys and waste handling. But the episodes all occur at
posts in a residential district and involve particles rather than stack gases, which points at
domestic coal burning as the driver of the peaks and at permitted industry as the background.

## 8. Figures

All eight figures in the report are produced by `build.py`:

```bash
python build.py
```"""),
]


def write_notebook():
    import json
    cells = [{'cell_type': 'markdown' if k == 'md' else 'code', 'metadata': {},
              'source': src.splitlines(keepends=True),
              **({'outputs': [], 'execution_count': None} if k == 'code' else {})}
             for k, src in NOTEBOOK]
    for i, c in enumerate([c for c in cells if c['cell_type'] == 'code'], 1):
        compile(''.join(c['source']), f'<cell {i}>', 'exec')      # fail now, not in Jupyter
    nb = {'cells': cells, 'nbformat': 4, 'nbformat_minor': 5,
          'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python',
                                      'name': 'python3'},
                       'language_info': {'name': 'python', 'version': '3.11'}}}
    (HERE / 'analysis.ipynb').write_text(json.dumps(nb, indent=1, ensure_ascii=False) + '\n',
                                         encoding='utf-8')
    return sum(c['cell_type'] == 'code' for c in cells), len(cells)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    print('figures ->', FIG.relative_to(ROOT))
    for src, dst in REUSED.items():
        shutil.copy(ROOT / 'results' / 'figures' / src, FIG / dst)
        print('  ', dst, '(reused)')
    fig4_city_heatmap()
    fig7_pollutant_ranking()
    fig8_sources()

    produced = sorted(p.name for p in FIG.glob('*.png'))
    assert len(produced) == 8, produced
    assert all(p.stat().st_size > 20_000 for p in FIG.glob('*.png')), 'a figure came out empty'

    from make_documents import to_docx, to_pptx
    if (HERE / 'report.md').exists():
        print(to_docx(HERE / 'report.md', HERE / 'report.docx').name)
    if (HERE / 'slides.md').exists():
        _, n = to_pptx(HERE / 'slides.md', HERE / 'slides.pptx')
        print(f'slides.pptx: {n} slides, {n - 1} excluding the title slide')
        assert 10 <= n - 1 <= 15, f'{n - 1} content slides, the brief asks for 10-15'
    code_cells, total_cells = write_notebook()
    print(f'analysis.ipynb: {total_cells} cells ({code_cells} code)')
    print(f'self-check ok: {len(produced)} figures')


if __name__ == '__main__':
    main()
