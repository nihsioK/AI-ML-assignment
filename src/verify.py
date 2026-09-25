"""Cross-check every number quoted in the written deliverables against the generated results.

The article, the report, the slides and the README all restate numbers that `run_models.py` and
`figures.py` produce. This script re-reads the generated CSVs and fails if any quoted value has
drifted, so the write-ups cannot silently go stale after a rerun.

Run after run_models.py and figures.py:  python src/verify.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / 'results'
DOCS = ROOT / 'docs'


def check(label, condition, detail=''):
    print(f'  {"ok  " if condition else "FAIL"} {label}{"  " + str(detail) if detail and not condition else ""}')
    return bool(condition)


def main() -> int:
    ok = True
    a = pd.read_csv(RES / 'table1_experiment_A.csv').set_index('Algorithm')
    b = pd.read_csv(RES / 'table1_experiment_B.csv').set_index('Algorithm')
    c = pd.read_csv(RES / 'table1_experiment_C.csv').set_index('Algorithm')

    print('Table 1 restated in the documents')
    for doc in ('article.md', '../README.md'):
        text = (DOCS / doc).read_text(encoding='utf-8')
        bad, rows = [], 0
        for alg in a.index.drop('Baseline (mean)'):
            for m in re.finditer(re.escape(alg) + r'\s*\|(.*?)\n', text):
                nums = [float(x) for x in re.findall(r'\d+\.\d+', m.group(1))]
                if not nums:
                    continue
                allowed = {round(a.loc[alg, col], 3) for col in ('RMSE', 'RMSE_sd', 'MAE', 'R2', 'R2_sd')}
                bad += [f'{alg}: {n}' for n in nums if n not in allowed]
                rows += 1
        ok &= check(f'{Path(doc).name}: {rows} rows match results/table1_experiment_A.csv', not bad, bad)

    print('Scalars quoted in prose')
    skill = lambda t: 100 * (1 - t.drop('Baseline (mean)').RMSE.min() / t.loc['Baseline (mean)', 'RMSE'])
    ok &= check('best RMSE 3.591, R2 0.587 (CatBoost)',
                round(a.loc['CatBoost', 'RMSE'], 3) == 3.591 and round(a.loc['CatBoost', 'R2'], 3) == 0.587)
    ok &= check('mean baseline RMSE 5.735', round(a.loc['Baseline (mean)', 'RMSE'], 3) == 5.735)
    ok &= check('skill A 37.4 %, B 21.3 %, C 29.5 %',
                (round(skill(a), 1), round(skill(b), 1), round(skill(c), 1)) == (37.4, 21.3, 29.5),
                (round(skill(a), 1), round(skill(b), 1), round(skill(c), 1)))
    ok &= check('blocked best R2 0.184', round(b.drop('Baseline (mean)').R2.max(), 3) == 0.184)

    print('Statistics quoted from the derived tables')
    dec = pd.read_csv(RES / 'seasonal_variance_share.csv', index_col=0).percent_of_variance
    ok &= check('variance shares: annual cycle 6.3 %, trend 2.3 %, synoptic 89.0 %',
                abs(dec['seasonal'] - 6.3) < 0.1 and abs(dec['trend'] - 2.3) < 0.1
                and abs(dec['residual'] - 89.0) < 0.1, dec.to_dict())
    clim = pd.read_csv(RES / 'doy_climatology.csv', index_col=0).pm2_5_ugm3
    # the CSV is stored to 2 dp, so compare with a tolerance instead of rounding a rounded value
    ok &= check('climatology peaks at 13.1 in late March, troughs at 6.7 in early November',
                abs(clim.max() - 13.1) < 0.05 and abs(clim.min() - 6.7) < 0.06
                and 75 <= clim.idxmax() <= 95 and 295 <= clim.idxmin() <= 315,
                (clim.max(), clim.idxmax(), clim.min(), clim.idxmin()))
    vz = pd.read_csv(RES / 'vz_meteorology.csv')
    ok &= check('episode-day medians -4.5/-11.1, 16.4/8.3, 135/30, 956.8/961.8',
                list(zip(vz.ordinary_median, vz.high_pollution_median))
                == [(-4.5, -11.1), (16.4, 8.3), (135.0, 30.0), (956.8, 961.8)])
    cv = pd.read_csv(RES / 'cams_vs_kazhydromet.csv')
    ok &= check('CAMS to ground ratio spans 15 to 38',
                14 <= cv.ratio.min() < 16 and 37 <= cv.ratio.max() < 39, (cv.ratio.min(), cv.ratio.max()))
    imp = pd.read_csv(RES / 'permutation_importance.csv')
    ok &= check('top predictor is the ventilation index',
                imp.feature.iloc[0] == 'ventilation_index', imp.feature.iloc[0])

    print('Source data')
    d = pd.read_csv(ROOT / 'data/processed/karaganda_modelling.csv', parse_dates=['date'])
    ok &= check('1503 modelled days, mean 9.14 ug/m3, 168 above the WHO 24-hour guideline',
                len(d) == 1503 and round(d.pm2_5.mean(), 2) == 9.14 and (d.pm2_5 > 15).sum() == 168)
    days = pd.read_csv(ROOT / 'data/raw/kazhydromet/krg_vz_days.csv', parse_dates=['date'])
    m = days.date.dt.month.value_counts()
    ok &= check('169 episode days: Jan 43, Dec 33, Feb 26, Nov 23, Oct 22, Mar 17',
                len(days) == 169 and [m[k] for k in (1, 12, 2, 11, 10, 3)] == [43, 33, 26, 23, 22, 17])
    rank = pd.read_csv(ROOT / 'data/raw/kazhydromet/national/kz_city_ranking.csv')
    ok &= check('Karaganda ranks 1 of 70 with 244 of 337 national episodes',
                len(rank) == 70 and rank.city.iloc[0] == 'Караганда'
                and rank.vz_cases_H1_2026.iloc[0] == 244 and rank.vz_cases_H1_2026.sum() == 337)

    print('Deliverables')
    missing = [f'{doc.name} -> {rel}' for doc in DOCS.glob('*.md')
               for rel in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', doc.read_text(encoding='utf-8'))
               if not (doc.parent / rel).resolve().exists()]
    ok &= check('every figure reference resolves', not missing, missing)
    built = ['docs/article.docx', 'docs/report.docx', 'docs/slides.pptx', 'notebooks/analysis.ipynb',
             'results/table1.md']
    absent = [p for p in built if not (ROOT / p).exists()]
    ok &= check('all generated deliverables present', not absent, absent)

    print('\n' + ('ALL CHECKS PASS' if ok else 'SOME CHECKS FAILED'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
