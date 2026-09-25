# Known issues

Problems found in this project that are **not** caused by the current task, recorded once so they are not rediscovered.

## 1. `np_pct` column is mis-parsed for hydrogen sulfide in `krg_series.csv`

**Where:** `data/raw/kazhydromet/krg_series.csv`, rows with `pollutant == 'Сероводород'`, produced by `src/parse_krg.py`.

**Symptom:** `np_pct` is the share of samples above the permissible limit and must lie in 0-100. For hydrogen sulfide it reaches 8553 (2024 annual), 2185 (2024Q3) and 2000 (2023 annual). All 13 out-of-range rows in the file are hydrogen sulfide; every other substance is in range. The companion `max_mgm3` for the same rows is around 6 mg/m3, which is several orders of magnitude above a plausible urban hydrogen sulfide reading, so the column offset most likely starts one field earlier.

**Cause:** the hydrogen sulfide row in the Kazhydromet bulletin tables appears to use a different column layout from the other substances, and the fixed-offset parser in `parse_krg.py` picks up the neighbouring field.

**Impact on this project:** none. Hydrogen sulfide is not used in any analysis, table or figure. PM2.5, PM10, nitrogen dioxide and sulphur dioxide were spot-checked against the source bulletins and are correct.

**Fix if needed:** re-derive the hydrogen sulfide columns by matching on the header text of each bulletin table instead of a fixed offset, and add `assert 0 <= np_pct <= 100` to the self-check at the end of `parse_krg.py`.
