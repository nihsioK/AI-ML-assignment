"""Weather (ERA5) and modelled composition (CAMS) for Karaganda via Open-Meteo. No API key.

Output in data/raw/open_meteo/:
  karaganda_weather_daily.csv - ERA5 daily fields from 2021-01-01, plus boundary layer height
                                aggregated from the hourly series
  karaganda_cams_daily.csv    - CAMS global (~40 km cell), daily means from the hourly series
  karaganda_daily.csv         - the two joined, plus the high-pollution-day flag from
                                krg_vz_days.csv
"""
import csv, json, datetime, statistics, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'raw' / 'open_meteo'
LAT, LON, TZ = 49.8047, 73.1094, 'Asia/Almaty'      # Karaganda
START = datetime.date(2021, 1, 1)
CAMS_START = datetime.date(2022, 8, 1)               # the API returns nothing before this
END = datetime.date.today() - datetime.timedelta(days=7)   # the reanalysis lags by a few days
ARCHIVE = 'https://archive-api.open-meteo.com/v1/archive'
AQ = 'https://air-quality-api.open-meteo.com/v1/air-quality'
WEATHER = ['temperature_2m_mean', 'temperature_2m_min', 'temperature_2m_max',
           'wind_speed_10m_mean', 'wind_speed_10m_max', 'wind_direction_10m_dominant',
           'precipitation_sum', 'snowfall_sum', 'relative_humidity_2m_mean', 'surface_pressure_mean']
POLLUTANTS = ['pm2_5', 'pm10', 'nitrogen_dioxide', 'sulphur_dioxide', 'carbon_monoxide', 'ozone']

def get(url, **params):
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=180) as r:
        j = json.load(r)
    if 'error' in j:
        raise RuntimeError(j.get('reason'))
    return j

def by_year(start, end):
    while start <= end:
        stop = min(datetime.date(start.year, 12, 31), end)
        yield start.isoformat(), stop.isoformat()
        start = stop + datetime.timedelta(days=1)

def daily_mean(hourly, names):
    """Hourly series -> {date: {name: mean over the non-null hours}}."""
    days = {}
    for i, t in enumerate(hourly['time']):
        d = days.setdefault(t[:10], {n: [] for n in names})
        for n in names:
            if hourly[n][i] is not None:
                d[n].append(hourly[n][i])
    return {day: {n: round(statistics.fmean(v), 2) if v else None for n, v in vals.items()}
            for day, vals in days.items()}

def weather():
    rows = {}
    for a, b in by_year(START, END):
        d = get(ARCHIVE, latitude=LAT, longitude=LON, start_date=a, end_date=b,
                daily=','.join(WEATHER), timezone=TZ)['daily']
        h = get(ARCHIVE, latitude=LAT, longitude=LON, start_date=a, end_date=b,
                hourly='boundary_layer_height', timezone=TZ)['hourly']
        blh = {}
        for t, v in zip(h['time'], h['boundary_layer_height']):
            if v is not None:
                blh.setdefault(t[:10], []).append(v)
        for i, day in enumerate(d['time']):
            if d['temperature_2m_mean'][i] is None:
                continue
            rows[day] = {n: d[n][i] for n in WEATHER}
            rows[day]['blh_min_m'] = min(blh[day]) if day in blh else None
            rows[day]['blh_mean_m'] = round(statistics.fmean(blh[day])) if day in blh else None
    return rows

def cams():
    rows = {}
    for a, b in by_year(CAMS_START, END):
        h = get(AQ, latitude=LAT, longitude=LON, start_date=a, end_date=b,
                hourly=','.join(POLLUTANTS), timezone=TZ)['hourly']
        for day, vals in daily_mean(h, POLLUTANTS).items():
            if vals['pm2_5'] is not None:
                rows[day] = vals
    return rows

def write(path, rows, first_col='date'):
    days = sorted(rows)
    cols = [first_col] + list(rows[days[0]])
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for d in days:
            w.writerow({first_col: d, **rows[d]})

if __name__ == '__main__':
    w, c = weather(), cams()
    write(OUT / 'karaganda_weather_daily.csv', w)
    write(OUT / 'karaganda_cams_daily.csv', c)
    vz = {r['date'] for r in csv.DictReader(open(ROOT / 'data/raw/kazhydromet/krg_vz_days.csv', encoding='utf-8'))}
    merged = {d: {**w[d], **{f'cams_{k}': v for k, v in c.get(d, {}).items()}, 'vz_day': int(d in vz)} for d in w}
    for d in merged:                      # no CAMS before August 2022, so those columns stay empty
        for k in POLLUTANTS:
            merged[d].setdefault(f'cams_{k}', None)
    write(OUT / 'karaganda_daily.csv', merged)

    # self-check
    assert len(w) > 2000 and all(r['temperature_2m_mean'] is not None for r in w.values())
    assert min(c) <= '2022-12-01' and len(c) > 1300, (min(c), len(c))
    pm = [r['pm2_5'] for r in c.values()]
    assert 1 < statistics.fmean(pm) < 200, statistics.fmean(pm)
    assert sum(r['vz_day'] for r in merged.values()) == len(vz), "a high-pollution day fell outside the range"
    print("self-check ok")
    print(f"weather: {min(w)}..{max(w)}, {len(w)} days | CAMS: {min(c)}..{max(c)}, {len(c)} days "
          f"| mean CAMS PM2.5 {statistics.fmean(pm):.1f} ug/m3")
