# Predicting daily PM2.5 in Karaganda, Kazakhstan

Course project for **Artificial Intelligence and Machine Learning**, Astana IT University, 2025-2026.
It combines both assignments into one study, since both are about the same city and the same data.

| Assignment | What it asks for | Where it is |
|---|---|---|
| Research article (`docs/assignment_briefs/assignment_ml_algorithms.pdf`) | 11 algorithms, k-fold with k = 10, Table 1, IMRAD article of 3500 words, 10-15 references | [docs/article.md](docs/article.md), [docs/article.docx](docs/article.docx) |
| Case Study Task 1 (`docs/assignment_briefs/case_study_task_1.docx`) | Air pollution analysis, report of 8-15 pages, deck of 10-15 slides, notebook | [docs/report.md](docs/report.md), [docs/slides.pptx](docs/slides.pptx), [notebooks/analysis.ipynb](notebooks/analysis.ipynb) |

**City:** Karaganda. **Target:** daily mean PM2.5. **Task:** regression from meteorology and calendar terms.

## Headline results

Meteorology and season explain **58.7 % of the daily variance** of PM2.5 over Karaganda.
**CatBoost** is the best of eleven algorithms at an RMSE of **3.591 ug/m3** against 5.735 for a mean baseline, a 37.4 % error reduction.
The tree ensembles beat the regularised linear models by 0.26 in R2, which is the quantitative statement that the relationship is non-linear.

The most consequential finding is methodological.
Re-running the identical benchmark under a **blocked chronological split** instead of a shuffled one drops the best R2 from 0.587 to 0.184, and the error reduction against the matching baseline from 37.4 % to 21.3 %.
About two fifths of the apparent skill under the prescribed shuffled protocol is an artefact of placing days from the same weather episode on both sides of the split.
The report and the article state the shuffled number as an upper bound and the blocked number as the honest estimate.

The learned importance ranking is led by the **ventilation index** (wind speed x mixing depth), which outranks both of its own constituents.
That ranking is corroborated by an independent, measurement-based source: on the 169 high-pollution days Kazhydromet recorded between 2021 and 2025, the median wind speed halves from 16.4 to 8.3 km/h and the median minimum mixing depth falls from 135 to 30 m.

## Table 1

Ten-fold cross-validated performance, experiment A. Mean baseline: RMSE 5.735, R2 -0.010.

| Algorithm | Number of features | Number of targets | k-fold validation | RMSE (ug/m3) | R2 |
|---|---|---|---|---|---|
| Ridge | 21 | 1 | 10-fold | 4.644 +- 0.646 | 0.324 +- 0.120 |
| Lasso | 21 | 1 | 10-fold | 4.664 +- 0.676 | 0.321 +- 0.106 |
| Elastic Net | 21 | 1 | 10-fold | 4.664 +- 0.678 | 0.322 +- 0.104 |
| KNN Regression | 21 | 1 | 10-fold | 4.394 +- 0.628 | 0.398 +- 0.082 |
| Extra Trees Regression | 21 | 1 | 10-fold | 3.717 +- 0.452 | 0.553 +- 0.140 |
| Adaptive Boosting (AdaBoost) | 21 | 1 | 10-fold | 4.885 +- 0.272 | 0.221 +- 0.225 |
| Gradient Boosting Regression | 21 | 1 | 10-fold | 3.790 +- 0.507 | 0.528 +- 0.185 |
| XGBoost | 21 | 1 | 10-fold | 3.655 +- 0.537 | 0.559 +- 0.192 |
| LightGBM | 21 | 1 | 10-fold | 3.728 +- 0.517 | 0.543 +- 0.181 |
| CatBoost | 21 | 1 | 10-fold | **3.591 +- 0.477** | **0.587 +- 0.109** |
| HistGradientBoosting | 21 | 1 | 10-fold | 3.749 +- 0.510 | 0.537 +- 0.185 |

Mean absolute error, per-fold scores and the three robustness experiments are in `results/`.

## Dataset

The dataset is assembled from four public sources and is regenerated end to end by the scripts in `src/`.
No source requires registration or an API key.

| Source | Link | What it provides |
|---|---|---|
| CAMS global reanalysis, via Open-Meteo | https://open-meteo.com/en/docs/air-quality-api | Daily PM2.5, PM10, NO2, SO2, CO, O3 for 49.80 N, 73.11 E. 1503 days from 2022-08-04 |
| ERA5 reanalysis, via Open-Meteo | https://open-meteo.com/en/docs/historical-weather-api | Daily temperature, wind, pressure, humidity, precipitation and boundary layer height. 2083 days from 2021-01-01 |
| Kazhydromet regional bulletins | https://www.kazhydromet.kz/ru/ecology/ezhemesyachnyy-informacionnyy-byulleten-o-sostoyanii-okruzhayuschey-sredy | 24 bulletins for the Karaganda region, 2021-2026. 15 substances, 169 high-pollution days, 105 emitting enterprises |
| Kazhydromet national bulletins | https://www.kazhydromet.kz/ru/ecology/ezhemesyachnyy-informacionnyy-byulleten-o-sostoyanii-okruzhayuschey-sredy | Composite pollution ranking of 70 settlements |

The ready-to-model table is `data/processed/karaganda_modelling.csv`: 1503 rows, 21 predictors, one target.
The bulletin PDFs and their text conversions are kept in `data/raw/kazhydromet/bulletins/` so the parse is auditable.

## Reproducing everything

```bash
uv sync                               # or: pip install -e .
brew install libomp                   # macOS only, needed by XGBoost and LightGBM
```

```bash
python src/fetch_open_meteo.py   # refresh ERA5 + CAMS from Open-Meteo        needs network, ~60 s
python src/build_features.py     # -> data/processed/karaganda_modelling.csv              0.2 s
python src/run_models.py         # -> results/table1_experiment_{A,B,C,D}.csv + diagnostics 350 s
python src/figures.py            # -> results/figures/*.png, 12 figures                   1.3 s
python src/make_documents.py     # -> docs/article.docx, report.docx, slides.pptx         0.3 s
python src/make_notebook.py      # -> notebooks/analysis.ipynb                            0.1 s
python src/verify.py             # cross-check every number in the write-ups vs results/  0.2 s
```

Only step 1 needs the network; everything else runs offline on what is already in `data/raw/`.
Timings are wall clock on an M-series Mac. `make_notebook.py --check` additionally executes all
14 notebook cells, which repeats the benchmark and therefore takes about as long as step 3.

The bulletin parsers only need re-running when new bulletins are added:

```bash
python src/parse_krg.py && python src/parse_vz.py && python src/parse_sources.py
```

Every script ends in assertion-based self-checks and fails loudly rather than emitting wrong numbers silently.
The checks cover the parse (period count, known values verified by hand against the PDFs), the feature build (row count, no target leakage, no gap in the daily index), the benchmark (every model beats the mean baseline; blocked validation never beats shuffled) and the documents (word count, slide count).

## Layout

```
data/raw/          bulletins as PDF and text, parsed CSVs, reanalysis CSVs
data/processed/    karaganda_modelling.csv - the single table used for modelling
src/               the whole pipeline, one script per stage
results/           Table 1 and the three robustness experiments, diagnostics, 12 figures
docs/              article and report in Markdown and Word, slides in Markdown and PowerPoint
notebooks/         analysis.ipynb, a thin narrative over the same functions
KNOWN_ISSUES.md    one data defect found and left documented rather than silently patched
```

## How the study is designed

The target is the CAMS daily mean PM2.5 and the predictors are meteorological and calendar terms only, with no pollutant on the predictor side, so R2 reads directly as the share of daily variance explained by weather and season.
This is the meteorological normalisation framing of Grange and Carslaw rather than pure forecasting.

Twenty-one predictors are used.
Eleven are raw ERA5 fields; three are derived with a physical motivation (diurnal temperature range for inversion strength, heating degree days for heating demand, ventilation index for dispersion capacity); four are sine and cosine encodings of the two circular variables, wind direction and day of year; three are calendar terms.

Four experiments run on the same eleven-algorithm roster:

| | Design | Purpose |
|---|---|---|
| **A** | Same-day meteorology, shuffled 10-fold | Table 1, as the assignment specifies |
| **B** | Same-day meteorology, blocked 10-fold | Leakage control for A |
| **C** | Next-day forecast with lagged pollutants, blocked 10-fold | The operationally useful task |
| **D** | As A but fitted on log(PM2.5), back-transformed | Control for the skewed target |

Preprocessing and hyperparameter selection both sit inside the cross-validation pipeline, so neither sees a held-out fold.
Regularisation strength and neighbourhood size are chosen by an inner cross-validation on the training fold; boosting hyperparameters are fixed a priori and identical across experiments.

## Honest limitations

The target is a reanalysis product, not an instrument reading.
Over the ten overlapping quarters the reanalysis reports 6.9 to 11.3 ug/m3 where the Kazhydromet posts report 119 to 430, a ratio of 15 to 38.
Both have known biases in opposite directions: a 40 km grid cell averages the city with open steppe, while the ground posts sit next to coal-burning housing and show a PM2.5/PM10 ratio of 0.90 to 1.00 against a normal urban 0.5 to 0.7.
Normalised to their own means the two series correlate at r = 0.69, so the timing is trustworthy and the absolute level is not; every statement about level in the write-ups is given as a range.

Because CAMS assimilates meteorology, some circularity exists between predictors and target.
The 41 % of variance that remains unexplained bounds it, and the independent analysis of the 169 measured high-pollution days provides the external check that an internal cross-validation score cannot.

The best model systematically underpredicts above roughly 20 ug/m3, which is the expected behaviour of a squared-error objective on a heavy-tailed target and the wrong bias for an early-warning system.
A deployment should refit on a quantile objective.
