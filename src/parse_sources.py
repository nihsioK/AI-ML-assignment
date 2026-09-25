"""Emitting enterprises by city and district of the Karaganda region.

Parses the "main sources of pollution" section of the most recent Kazhydromet bulletin.
Output: data/raw/kazhydromet/krg_sources.csv with columns city, source.
"""
import re, csv, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BUL = ROOT / 'data' / 'raw' / 'kazhydromet' / 'bulletins'
OUT = ROOT / 'data' / 'raw' / 'kazhydromet' / 'krg_sources.csv'
SPLIT = re.compile(r',\s*(?=ТОО|АО|РГП|шахта|Агломерац|СТС|Разрез|ГУ|ИП|ПК)|;')

def sources(text):
    i = text.index('и следующие')
    j = text.index('Мониторинг качества', i)
    block = re.sub(r'\s+', ' ', text[i:j]).split('предприятия:', 1)[1]
    # cities ("г. Каражал :") are followed by districts ("Абайский район :"); both are keys
    parts = re.split(r'(?:г\.\s?([А-ЯЁ][а-яё-]+)|([А-ЯЁ][А-ЯЁа-яё-]+\s+район))\s*:?\s', block)
    for k in range(1, len(parts), 3):
        area = parts[k] or parts[k + 1]
        for e in SPLIT.split(parts[k + 2]):
            e = e.strip(' ;.,')
            if 3 < len(e) <= 80:            # longer than 80 means the split captured stray text
                yield area, e

latest = sorted(BUL.glob('*.txt'))[-1]
rows = [{"city": c, "source": s} for c, s in sources(latest.read_text(encoding='utf-8', errors='replace'))]
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=["city", "source"]); w.writeheader(); w.writerows(rows)

def demo():
    krg = [r["source"] for r in rows if r["city"] == 'Караганда']
    assert 10 <= len(krg) <= 25, len(krg)
    assert any('Tau-Ken' in s for s in krg)
    kzh = [r["source"] for r in rows if r["city"] == 'Каражал']
    assert len(kzh) == 3, kzh
    print("self-check ok")

if __name__ == '__main__':
    demo()
    import collections
    print(latest.name, "->", dict(collections.Counter(r["city"] for r in rows)))
