## Air Pollution in Karaganda, Kazakhstan

Case Study Task 1

**Data:** Kazhydromet bulletins 2021-2026, ERA5 and CAMS reanalysis 2021-2026

**Question:** why is Karaganda the most polluted city in Kazakhstan, and what can be done about it?

## Problem statement

- Karaganda is **first among 70 monitored settlements** of Kazakhstan by the official Kazhydromet score
- It recorded **244 of the country's 337 high-pollution episodes** in the first half of 2026, that is 72 %
- Coal mining, coal chemistry, ferroalloys, and half a million people heating their homes with coal
- Two competing explanations, with very different price tags:
- **Too much is emitted** - fix with fuel substitution and industrial regulation, over a decade
- **It does not disperse** - fix with episode forecasting and heating-day restrictions, within a season
- This study separates the two using five years of official data

## Karaganda leads the national ranking

![Composite pollution score, Kazhydromet, first half of 2026. Almaty, which gets most of the public attention, is only seventh.](figures/fig3_city_ranking.png)

## It is worst on every indicator at once

![Fifteen worst settlements across five indicators. Several cities match Karaganda on one; none matches it on all five.](figures/fig4_city_heatmap.png)

## Data used

| Source | What it gives | Coverage |
|---|---|---|
| Kazhydromet regional bulletins | 15 substances, 169 episode days, 105 emitters | 24 periods, 2021-2026 |
| Kazhydromet national bulletins | Ranking of 70 settlements | H1 2026 |
| ERA5 reanalysis | Temperature, wind, pressure, mixing depth | 2083 days |
| CAMS reanalysis | PM2.5, PM10, NO2, SO2, CO, O3 | 1503 days |

All four are public and free. Bulletins were parsed from PDF; the reanalysis came from the Open-Meteo API.

**Caveat stated up front:** ground posts report 119-430 ug/m3 where the reanalysis reports 6.9-11.3. Normalised, the two agree at r = 0.69. **Timing is reliable, absolute level is not** - so every level in this report is given as a range.

## Key finding 1: it is a particulate problem

![Average exceedance of the Kazakh 24-hour limit, 16 quarters. PM2.5 is 5.6 times over; the tall-stack gases are under.](figures/fig7_pollutant_ranking.png)

## Key finding 1, in numbers

- **PM2.5 averages 5.6x** the Kazakh 24-hour limit, one measurement hit **40.9x** the short-term limit
- **100 % of samples** have been above the limit since 2022
- PM10 follows at 3.4x; phenol is the only gas with a constant exceedance, pointing at coal chemistry
- **SO2, NO2 and CO stay below their limits** - that is the signature of low-level sources, not tall stacks
- Against the WHO guideline of 5 ug/m3 a year, Karaganda runs at **6 to 30 times** over, depending on which of the two badly reconciled sources you trust

## Key finding 2: all the risk is in the cold season

![169 measured high-pollution days by month, 2021-2025. Sixty per cent fall in December to February; none at all between May and August.](figures/fig5_episodes_by_month.png)

## Key finding 3: the weather decides the day

![Weather on episode days against ordinary heating-season days.](figures/fig6_episode_weather.png)

## Key finding 3, in numbers

| Heating-season median | Ordinary day | Episode day |
|---|---|---|
| Temperature | -4.5 C | -11.1 C |
| Wind speed | 16.4 km/h | 8.3 km/h |
| Minimum mixing depth | 135 m | 30 m |
| Surface pressure | 956.8 hPa | 961.8 hPa |

High pressure, hard frost, calm air, a mixing layer tens of metres deep: a textbook temperature inversion.

Flat steppe traps pollution just as effectively as the mountain basin usually blamed for Almaty's smog.

## Key finding 4: the episodes are domestic, not industrial

![Permitted emitting enterprises by city and district of the Karaganda region.](figures/fig8_emission_sources.png)

## Why we conclude that

- The region has **105 permitted emitters** and 585 thousand tonnes a year from stationary sources - that is the background
- But **all 169 episodes** were recorded at posts 6 and 8, both in Prishakhtinsk, a district of low-rise housing with individual coal stoves, not an industrial zone
- The substance that exceeds limits is **particles, not stack gases** - a low-level release signature
- The episodes **require calm air**, and calm concentrates near-ground emissions specifically
- Caveat: wind on episode days comes from the south-east twice as often as usual, and the CHP plant lies in that direction, so an industrial share of the peaks is not ruled out

## Proposed solutions: now

- **Episode warning service.** The trigger is readable from an ordinary weather forecast: wind under 8 km/h plus a shallow mixing layer in the heating season. Free data, free tools, could run within one heating season
- **Act on the warnings:** free public transport on those days, ban open-air burning, postpone industrial maintenance releases, restrict school outdoor activity
- **Twenty low-cost sensors.** Karaganda has 2, Almaty has 153. This costs a fraction of one reference station and settles whether Prishakhtinsk represents the city or one neighbourhood
- **Fix the reference instruments.** The PM2.5/PM10 ratio sits at 0.90-1.00 against a normal 0.5-0.7 - the size separation is not working, which undermines the numbers the national ranking rests on

## Proposed solutions: 3-10 years

- **Target household coal in Prishakhtinsk first** - connection to district heating, subsidised low-emission stoves, processed fuel with controlled ash. Pilot it in the catchment of post 8 and measure before and after
- **Regulate the ash content of coal sold to households** - administrative measure, no capital cost, immediate effect
- **Continuous stack monitoring** at the largest emitters, publicly disclosed
- **Decarbonise the heat supply** - gas conversion of the CHP plants, solar-assisted district heating, building retrofit. Nothing else brings the annual mean near the WHO guideline
- **Preserve ventilation corridors** in city planning, revegetate the spoil heaps
- **Converge national limits towards the WHO guidelines** on a published schedule

## Conclusions

- Karaganda has an **emissions problem that becomes dangerous through a dispersion bottleneck** - emissions run all year, the winter anticyclone turns them into episodes
- **PM2.5 is the problem**, 5.6x the national limit and 6-30x the WHO guideline
- **Seasonality is absolute:** 169 episodes in five years, none between May and August
- **Domestic coal burning drives the peaks**, permitted industry sets the background
- **Cheapest effective action:** an episode warning service on free weather data, running within one season
- **Biggest obstacle:** two instruments in one district decide the ranking of a city of half a million, and they show a size-separation fault

**Thank you. Questions?**
