"""High-pollution days in Karaganda, extracted from the Kazhydromet bulletins.

The section on extreme and high pollution lists the dates as a run, for example
"17, 18, 19 января, 1, 13 февраля 2023 года по данным поста №8 ...", with the year and the
monitoring posts given once at the end of each run.
Output: krg_vz_days.csv with columns date, posts, source_file.
"""
import re, csv, glob, os, datetime, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BUL = ROOT / 'data' / 'raw' / 'kazhydromet' / 'bulletins'
OUT = ROOT / 'data' / 'raw' / 'kazhydromet'

MONTHS = {m: i + 1 for i, m in enumerate(
    "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split())}
RUN = re.compile(r'(\d{1,2}(?:\s*,\s*\d{1,2})*)\s+(' + '|'.join(MONTHS) + r')')
YEAR = re.compile(r'(20\d\d)\s*г')
POST = re.compile(r'№\s*(\d+)')
PAR = re.compile(r'Случаи экстремально высокого и высокого загрязнения[^:]*:(.{0,3000}?)'
                 r'(?:Фактические значения|таблице 2|Таблица 2|$)')
CITY = re.compile(r'Караганд|Темиртау|Балхаш|Жезказган|Сарань|Абай|Шахтинск|Сатпаев|Каражал|Приозерск')

def paragraphs(text):
    """Yield the high-pollution paragraphs that belong to Karaganda.

    The bulletins do not repeat the city name in every paragraph, so it is taken from the
    nearest preceding mention.
    """
    text = re.sub(r'\s+', ' ', text)
    cities = [(m.start(), m.group(0)) for m in CITY.finditer(text)]
    for m in PAR.finditer(text):
        before = [c for pos, c in cities if pos < m.start()]
        if before and before[-1].startswith('Караганд'):
            yield m.group(1)

def episodes(par):
    """Return [(date, posts)]. The year and the posts are taken from the tail of each run."""
    out, pending = [], []
    tokens = sorted([(m.start(), 'run', m) for m in RUN.finditer(par)] +
                    [(m.start(), 'year', m) for m in YEAR.finditer(par)])
    for i, (_, kind, m) in enumerate(tokens):
        if kind == 'run':
            days = [int(d) for d in re.findall(r'\d{1,2}', m.group(1))]
            pending += [(day, MONTHS[m.group(2)]) for day in days]
        else:
            nxt = tokens[i + 1][0] if i + 1 < len(tokens) else len(par)
            posts = ','.join(dict.fromkeys(POST.findall(par[m.end():nxt])))
            year = int(m.group(1))
            for day, mon in pending:
                try:
                    out.append((datetime.date(year, mon, day), posts))
                except ValueError:
                    pass                      # e.g. "31 февраля": a typo in the bulletin
            pending = []
    return out

rows, seen = [], set()
for f in sorted(glob.glob(str(BUL / '*.txt'))):
    text = open(f, encoding='utf-8', errors='replace').read()
    if 'Караганд' not in text:
        continue
    for par in paragraphs(text):
        for d, posts in episodes(par):
            if d in seen:
                continue
            seen.add(d)
            rows.append({"date": d.isoformat(), "posts": posts,
                         "source_file": os.path.basename(f)[:-4]})
rows.sort(key=lambda r: r["date"])
with open(OUT / 'krg_vz_days.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=["date", "posts", "source_file"])
    w.writeheader(); w.writerows(rows)

def demo():
    par = ("17, 18 января, 27, 28 марта, 2023 года по данным постов № 6 (ул. А) и №8 (ул. Б), "
           "6, 7 ноября 2023 года по данным поста №8 (улица Зелинского 23 (Пришахтинск)) "
           "зафиксировано 293 случая")
    got = episodes(par)
    assert [d.isoformat() for d, _ in got] == ['2023-01-17', '2023-01-18', '2023-03-27',
                                               '2023-03-28', '2023-11-06', '2023-11-07'], got
    assert got[0][1] == '6,8' and got[-1][1] == '8', got
    assert not any(d.day == 23 for d, _ in got), "the 23 from the street address leaked into the dates"
    by_year = collections.Counter(r["date"][:4] for r in rows)
    assert by_year['2023'] == 19 and by_year['2024'] == 39, dict(by_year)   # checked by hand against the annual bulletins
    print("self-check ok")

if __name__ == '__main__':
    demo()
    by_year = collections.Counter(r["date"][:4] for r in rows)
    print("high-pollution days:", len(rows), "by year:", dict(sorted(by_year.items())))
    by_month = collections.Counter(int(r["date"][5:7]) for r in rows)
    print("by month:", dict(sorted(by_month.items())))
    print("posts:", dict(collections.Counter(r["posts"] for r in rows)))
