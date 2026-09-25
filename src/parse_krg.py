"""Quarterly air-pollution series for Karaganda, parsed from the Kazhydromet PDF bulletins.

Input : data/raw/kazhydromet/bulletins/*.txt, produced by `pdftotext -layout`.
Output: krg_series.csv with columns period, granularity, pollutant, mean_mgm3, ratio_pdk_ss,
        max_mgm3, ratio_pdk_mr, np_pct, n_over_pdk.

Concentrations are in mg/m3; ratio_pdk_ss and ratio_pdk_mr are multiples of the Kazakh 24-hour
and single-measurement limits; np_pct is the share of samples above the limit.
"""
import re, csv, glob, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BUL = ROOT / 'data' / 'raw' / 'kazhydromet' / 'bulletins'
OUT = ROOT / 'data' / 'raw' / 'kazhydromet'

NUM = r'-?\d+(?:[.,]\d+)?'
CITY_HDR = re.compile(r'^\s*(?:г\.|гор\.)\s*([А-ЯЁ][а-яё-]+)')
FRAC = re.compile(r'[РP]М[-\s]?(2[.,]5|10)')   # Cyrillic РМ-2,5 / РМ-10 -> PM25 / PM10

def num(s):
    return float(s.replace(',', '.'))

def parse(path):
    """Rows of table 1 for Karaganda, as (substance, [numbers]).

    The bulletin layout changed: until 2023 the substance name and its numbers sit on one line,
    from 2024 the name is split around the numeric line ("Взвешенные частицы" / numbers /
    "РМ-2,5"), so the parser has to carry a name fragment across lines.
    """
    STOP = ('Таблица 2', 'эпизодич', 'Адрес поста', 'ЭКОСЕРВИС',
            'Приложение', 'Населенный', 'Примесь', 'концентрац')
    out, inside, carry = [], False, ''
    for ln in open(path, encoding='utf-8', errors='replace'):
        ln = ln.rstrip()
        m = CITY_HDR.match(ln)
        if m:
            inside = m.group(1).startswith('Караганд')
            carry = ''
            continue
        if not inside:
            continue
        if any(k in ln for k in STOP):
            inside = False
            continue
        raw = FRAC.sub(lambda t: 'PMFINE' if t.group(1)[0] == '2' else 'PMCOARSE', ln)
        nums = re.findall(NUM, raw)
        name = re.sub(NUM, '', raw).strip(' .|')
        name = name.replace('PMFINE', 'PM2.5').replace('PMCOARSE', 'PM10')
        if len(nums) == 1 and not name and out and out[-1][0].rstrip().endswith('-'):
            out[-1][0] = out[-1][0].rstrip() + ln.strip()   # rejoin a name split as "РМ-" + "2,5"
            continue
        if len(nums) >= 2 and name:
            out.append([(carry + ' ' + name).strip(), [num(x) for x in nums]])
            carry = ''
        elif len(nums) >= 2 and carry:          # numbers on a line with no name of their own
            out.append([carry, [num(x) for x in nums]])
            carry = ''
        elif name and not nums and len(name) < 40:
            # the tail of a name that the numeric line split in two
            if out and (name.startswith(('PM2.5', 'PM10', '(')) ) and not carry:
                out[-1][0] = (out[-1][0] + ' ' + name).strip()
            else:
                carry = (carry + ' ' + name).strip()
    return [(n, v) for n, v in out]

CANON = [
    ('PM2.5', 'PM2.5'), ('РМ-2,5', 'PM2.5'), ('PM10', 'PM10'), ('РМ-10', 'PM10'), ('пыль', 'Взвешенные частицы (пыль)'),
    ('иоксид серы', 'Диоксид серы'), ('ксид углерода', 'Оксид углерода'),
    ('иоксид азота', 'Диоксид азота'), ('ксид азота', 'Оксид азота'),
    ('зон', 'Озон'), ('ероводород', 'Сероводород'), ('ммиак', 'Аммиак'),
    ('енол', 'Фенол'), ('ормальдегид', 'Формальдегид'), ('амма', 'Гамма-фон'),
    ('ышьяк', 'Мышьяк'), ('туть', 'Ртуть'), ('адмий', 'Кадмий'),
    ('винец', 'Свинец'), ('ром', 'Хром'), ('едь', 'Медь'),
]

def canon(name):
    """Map the spelling variants used across bulletins onto one canonical substance name."""
    for key, out in CANON:
        if key in name:
            return out
    return None


def period(fn):
    """2021_kvartal_3 -> ('2021Q3','quarter'); polugodie -> H1; year -> Y."""
    b = os.path.basename(fn)[:-4]
    y, kind = b.split('_', 1)
    if kind.startswith('kvartal'):
        return f"{y}Q{kind[-1]}", 'quarter'
    if kind.startswith('polugodie'):
        return f"{y}H1", 'half'
    if kind == 'year':
        return f"{y}Y", 'year'
    return None, None

rows, seen = [], set()
for f in sorted(glob.glob(str(BUL / '*.txt'))):
    p, gran = period(f)
    if not p:
        continue
    got = parse(f)
    if not got:
        print("empty parse:", f)
    for name, v in got:
        name = canon(name)
        if name is None or (p, name) in seen:   # table 1 comes first, so keep the first hit
            continue
        seen.add((p, name))
        rows.append({
            "period": p, "granularity": gran, "pollutant": name,
            "mean_mgm3": v[0] if len(v) > 0 else "",
            "ratio_pdk_ss": v[1] if len(v) > 1 else "",
            "max_mgm3": v[2] if len(v) > 2 else "",
            "ratio_pdk_mr": v[3] if len(v) > 3 else "",
            "np_pct": v[4] if len(v) > 4 else "",
            "n_over_pdk": v[5] if len(v) > 5 else "",
        })

rows.sort(key=lambda r: (r["period"], r["pollutant"]))
with open(OUT / 'krg_series.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

def demo():
    assert period('2021_kvartal_1.txt') == ('2021Q1', 'quarter')
    assert period('2021_year.txt') == ('2021Y', 'year')
    assert period('2025_polugodie_1.txt') == ('2025H1', 'half')
    pm = [r for r in rows if r["pollutant"] == 'PM2.5']
    assert len(pm) == len({r["period"] for r in pm}), "duplicate PM2.5 rows within one period"
    assert canon('Взвешенные частицы PM2.5') == 'PM2.5'
    assert canon('Озон (приземный)') == 'Озон'
    assert canon('Взвешенные частицы РМ-2,5') == 'PM2.5'
    assert canon('Взвешенные частицы РМ-10') == 'PM10'
    q = {r["period"]: r["mean_mgm3"] for r in pm}
    assert q['2022Q2'] > 0.05, f"2022Q2 is still mis-parsed: {q['2022Q2']}"
    assert q['2026Q1'] == 0.43
    assert q['2023Y'] == 0.27 and q['2024Y'] > 0
    assert canon('Средняя разовая') is None
    assert pm, "PM2.5 was not found in any period"
    assert all(isinstance(r["mean_mgm3"], float) for r in pm)
    print("self-check ok")

if __name__ == '__main__':
    demo()
    per = sorted({r["period"] for r in rows})
    print(f"periods: {len(per)} -> {', '.join(per)}")
    print(f"rows: {len(rows)}, substances: {len({r['pollutant'] for r in rows})}")
    print("\nPM2.5 by period (mean mg/m3, multiple of the 24-hour limit, % of samples above):")
    for r in rows:
        if r["pollutant"] == 'PM2.5':
            print(f"  {r['period']}  {r['mean_mgm3']:>7}  x{r['ratio_pdk_ss']:<7} above={r['np_pct']}%")
