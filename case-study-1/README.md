# Case Study Task 1: air pollution in Karaganda

The light version of the project, scoped strictly to the case study brief.
Descriptive analysis only, no machine-learning benchmark.
The full study with eleven algorithms and four validation designs is one level up.

## Deliverables

| Brief asks for | File | Size |
|---|---|---|
| A. Written report, 8-15 pages | `report.docx` (source: `report.md`) | 3262 words, 8 figures, 4 tables, ~12 pages |
| B. Presentation, 10-15 slides | `slides.pptx` (source: `slides.md`) | 14 slides plus title |
| C. Python notebook / code (optional) | `analysis.ipynb`, `build.py` | 20 cells, 9 of them code |

## Rebuilding

```bash
python case-study-1/build.py
```

One script does everything: draws three figures, copies five from the main study, writes
`report.docx`, `slides.pptx` and `analysis.ipynb`, then checks that eight figures exist, none is
empty, and the deck is inside the 10-15 slide range.

Data comes from `../data/raw/`, which is already in the repository. Nothing here needs the network.

## How the report maps onto the brief

| Brief | Where |
|---|---|
| 5.1 Data collection and cleaning | Report section 3 and 4; parsers in `../src/parse_*.py` |
| 5.2 Time-series analysis | Report 5.3, figures 4 and 5 |
| 5.2 Seasonal patterns | Report 5.3, figure 6 |
| 5.2 Correlation with weather | Report 5.4, figure 7, table 3 |
| 5.3 Line charts of pollutants over months | Figures 4 and 5 |
| 5.3 Heatmap comparing cities | Figure 2 |
| 5.3 Bar charts ranking sources | Figures 3 and 8 |
| 5.4 Comparison with WHO standards | Report 5.6 |
| 5.4 High-risk periods and exceedance days | Report 5.3, 169 episodes by month |
| 5.5 Recommendations | Report section 7, short / medium / long term |
| Research questions 1-5 | Report section 6, answered one by one |

## Main findings

- Karaganda is **first among 70 monitored settlements** and accounts for 244 of the country's 337
  high-pollution episodes in H1 2026.
- **PM2.5 is the problem:** 5.6 times the Kazakh 24-hour limit on average, 100 % of samples above
  the limit since 2022, and 6 to 30 times the WHO guideline. The tall-stack gases stay under their
  limits, which points at low-level sources.
- **All 169 episodes of 2021-2025 fall between September and April**, none between May and August.
- On episode days the median wind speed halves and the mixing layer drops from 135 to 30 m.
  Karaganda has an emissions problem that turns dangerous through a dispersion bottleneck.
- The episodes are recorded at two posts in a residential district and involve particles rather
  than stack gases, so **domestic coal burning drives the peaks** while permitted industry sets the
  background.

## Honest limitations

The ground posts report quarterly PM2.5 of 119-430 ug/m3 where the reanalysis reports 6.9-11.3.
Both are biased, in opposite directions: a 40 km grid cell averages the city with empty steppe,
while the posts sit next to coal-burning housing and show a PM2.5/PM10 ratio of 0.90-1.00 against
a normal urban 0.5-0.7. Normalised to their own means the two agree at r = 0.69, so timing is
reliable and absolute level is not. Every level in the report is given as a range.

A per-city concentration series is not included: the bulletin tables for cities other than
Karaganda use a different column layout, and the parser does not read them reliably. The city
comparison therefore uses the national ranking, which is verified.
