# Supermarket refrigeration data quick guide

Commercial CO₂ test rig with a freezer (LT), a chilled case (MT), and a shared gas cooler. The 11 CSVs contain five baseline runs and six fault runs. [Study and instrumentation](https://doi.org/10.1038/s41597-021-00927-6) · [Raw data and authors’ analysis script](https://doi.org/10.6084/m9.figshare.13232627)

## Runs

| Run | Scenario | Baseline | Rows | Nominal (s) | Common positive step (s) |
| --- | --- | --- | --- | --- | --- |
| BaselineTestA | Baseline | — | 81204 | 1 | 1.0 |
| BaselineTestB | Baseline | — | 81341 | 1 | 1.0 |
| BaselineTestC | Baseline | — | 81274 | 1 | 1.0 |
| BaselineTestD | Baseline | — | 81363 | 1 | 1.0 |
| BaselineTestE | Baseline | — | 81249 | 1 | 1.0 |
| Fault1_DisplayCaseDoorOpen | Freezer door open | A | 81234 | 1 | 1.0 |
| Fault2_IceAccumulation | Ice accumulation on freezer evaporator | B | 26395 | 3 | 60.0 |
| Fault3_EvapValveFailure | Freezer expansion valve failure | C | 81280 | 1 | 60.0 |
| Fault4_MTEvapFanFailure | Chilled-case evaporator fan motor failure | D | 81238 | 1 | 1.0 |
| Fault5_CondAPBlock | Gas cooler airflow blockage | E | 81094 | 1 | 1.0 |
| Fault6_MTEvapAPBlock | Chilled-case evaporator airflow blockage | A | 81237 | 1 | 1.0 |

**Reading the clock.** Timestamp is the recorded clock with unspecified timezone. Ice accumulation and expansion valve failure use minute-resolution timestamps with many rows per minute. Preserve row order. Fault files identify the scenario for the run. Confirm onset and defrost intervals before labeling rows.

## Channel dictionary and basic statistics

**838,909 rows across 185 distinct non-timestamp fields.** Min and max use all finite values. Typical is the median of run medians. Missing percentages use rows in files containing the channel. Constant runs have a single finite value across their observed readings. Duplicate headers retain their column position. Names describe likely locations inferred from headers where source mappings are unavailable. A dash in Unit means the raw CSV unit is unverified. Extreme values may include invalid readings.

| Channel | Meaning | Unit | Min | Typical | Max | Missing % | Constant runs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| W_MT-COMP1 | Power at chilled circuit / compressor 1 | — | 1.6 | 4.77 | 8.45 | 0.0 | 0/11 |
| W_MT-COMP2 | Power at chilled circuit / compressor 2 | — | -1.27 | 0.03 | 15.66 | 0.0 | 0/11 |
| W_MT-COMP3 | Power at chilled circuit / compressor 3 | — | -0.76 | 0.01 | 19.09 | 0.0 | 0/11 |
| W_LT-COMP1 | Power at freezer circuit / compressor 1 | — | 0.0 | 0.02 | 1.61 | 0.0 | 0/11 |
| W_LT-COMP2 | Power at freezer circuit / compressor 2 | — | -0.02 | 0.0 | 1.9 | 0.0 | 0/11 |
| W-CONDENSOR | Power at condenser | — | -0.09 | 0.04 | 1.6 | 0.0 | 0/11 |
| M-MTcooler | Mass flow at chilled cooler | — | -1.28 | 0.98 | 10.34 | 0.0 | 0/11 |
| M-LTcooler | Mass flow at freezer cooler | — | -1.31 | -1.25 | -0.89 | 0.0 | 0/11 |
| M-CompRack | Mass flow at compressor rack | — | -0.12 | 0.0 | 10.34 | 0.0 | 0/11 |
| W-LT-BPHX | Power at freezer circuit / brazed-plate heat exchanger | — | -31.28 | 0.97 | 64.49 | 0.0 | 0/11 |
| W-MT-BPHX | Power at chilled circuit / brazed-plate heat exchanger | — | -1732.34 | -0.06 | 12751.3 | 0.0 | 0/11 |
| P-LT-BPHX | Pressure at freezer circuit / brazed-plate heat exchanger | — | -5.65 | 12.31 | 16.48 | 0.0 | 0/11 |
| P-MT-BPHX | Pressure at chilled circuit / brazed-plate heat exchanger | — | -32.76 | 12.02 | 54.86 | 0.0 | 0/11 |
| P-MTcase-SUC-inside | Pressure at chilled case / suction / inside | — | 304.46 | 381.45 | 463.89 | 0.0 | 0/11 |
| P-MTcase-SUC | Pressure at chilled case / suction | — | 304.75 | 381.25 | 463.6 | 0.0 | 0/11 |
| P-MTcase-LIQ | Pressure at chilled case / liquid line | — | 412.66 | 449.12 | 585.55 | 0.0 | 0/11 |
| P-LTcase-SUC-inside | Pressure at freezer case / suction / inside | — | 149.09 | 176.2 | 235.04 | 0.0 | 0/11 |
| P-LTcase-SUC | Pressure at freezer case / suction | — | 149.12 | 175.41 | 234.13 | 0.0 | 0/11 |
| P-LTcase-LIQ | Pressure at freezer case / liquid line | — | 412.4 | 448.96 | 584.31 | 0.0 | 0/11 |
| P-FlashTank | Pressure at flash tank | — | 413.25 | 450.4 | 585.22 | 0.0 | 0/11 |
| P-GC-IN | Pressure at gas cooler / inlet | — | 527.2 | 809.9 | 1176.36 | 0.0 | 0/11 |
| P-MT_Dis-OilSepIn | Pressure at chilled circuit / discharge / oil separator inlet | — | 529.82 | 811.41 | 1295.62 | 0.0 | 0/11 |
| P-LT-SUC | Pressure at freezer circuit / suction | — | 105.08 | 175.61 | 288.93 | 0.0 | 0/11 |
| P-MT_SUC | Pressure at chilled circuit / suction | — | 302.65 | 379.74 | 462.48 | 0.0 | 0/11 |
| T-MT-COMP1-SUC | Temperature at chilled circuit / compressor 1 / suction | — | 16.69 | 22.32 | 41.74 | 0.0 | 0/11 |
| T-MT-COMP1-DIS | Temperature at chilled circuit / compressor 1 / discharge | — | 76.71 | 131.13 | 186.76 | 0.0 | 0/11 |
| T-MT-COMP2-SUC | Temperature at chilled circuit / compressor 2 / suction | — | 17.68 | 67.73 | 78.87 | 0.0 | 0/11 |
| T-MT-COMP2-DIS | Temperature at chilled circuit / compressor 2 / discharge | — | 77.84 | 95.44 | 195.7 | 0.0 | 0/11 |
| T-MT-COMP3-SUC | Temperature at chilled circuit / compressor 3 / suction | — | 19.97 | 79.51 | 83.73 | 0.0 | 0/11 |
| T-MT-COMP3-DIS | Temperature at chilled circuit / compressor 3 / discharge | — | 76.21 | 83.91 | 178.66 | 0.0 | 0/11 |
| T-LT-COMP1-SUC | Temperature at freezer circuit / compressor 1 / suction | — | 38.73 | 45.96 | 87.64 | 0.0 | 0/11 |
| T-LT-COMP1-DIS | Temperature at freezer circuit / compressor 1 / discharge | — | 80.88 | 156.42 | 188.24 | 0.0 | 0/11 |
| T-LT-COMP2-SUC | Temperature at freezer circuit / compressor 2 / suction | — | 69.99 | 80.26 | 87.55 | 0.0 | 0/11 |
| T-LT-COMP2-DIS | Temperature at freezer circuit / compressor 2 / discharge | — | 81.24 | 90.22 | 103.3 | 0.0 | 0/11 |
| T-GC-SUC | Temperature at gas cooler / suction | — | 80.06 | 129.16 | 180.95 | 0.0 | 0/11 |
| T-GC-DIS | Temperature at gas cooler / discharge | — | 41.45 | 68.99 | 96.98 | 0.0 | 0/11 |
| T-BP-EEVout | Temperature at bypass / electronic expansion valve outlet | — | 22.12 | 25.8 | 34.08 | 0.0 | 0/11 |
| T-BP-EEVin | Temperature at bypass / electronic expansion valve inlet | — | -99920.4 | 50.72 | 1027.58 | 0.0 | 0/11 |
| T-BP-srf | Temperature at bypass / surface | — | 36.97 | 51.56 | 64.85 | 0.0 | 0/11 |
| T-MTrack-LIQ | Temperature at chilled compressor rack / liquid line | — | 24.87 | 27.64 | 31.02 | 0.0 | 0/11 |
| T-MTcase-LIQ | Temperature at chilled case / liquid line | — | 25.98 | 30.32 | 63.96 | 0.0 | 0/11 |
| T-spare-13B | Spare temperature input, placement unverified | — | -101156.39 | -99247.72 | -98183.05 | 0.0 | 0/11 |
| T-LTcase-LIQ-srf | Temperature at freezer case / liquid line / surface | — | 23.78 | 28.49 | 58.49 | 0.0 | 0/11 |
| T-LTcase-SUC-srf | Temperature at freezer case / suction / surface | — | -22.46 | 20.64 | 56.69 | 0.0 | 0/11 |
| T-LTcase-EEVout | Temperature at freezer case / electronic expansion valve outlet | — | -99768.69 | -7.58 | 221.14 | 0.0 | 0/11 |
| T-LTcase-Sup | Freezer evaporator supply air | °F | -8.04 | -2.01 | 66.54 | 0.0 | 0/11 |
| T-LTcase-Ret | Freezer evaporator return air | °F | -8.89 | -2.93 | 44.18 | 0.0 | 0/11 |
| T-LTcase-Liq | Temperature at freezer case / liquid line | — | 22.93 | 29.1 | 62.23 | 0.0 | 0/11 |
| T-LTcase-Suc | Temperature at freezer case / suction | — | -22.64 | 16.16 | 56.55 | 0.0 | 0/11 |
| T-spare-16C | Spare temperature input, placement unverified | — | -101200.44 | -99288.08 | -98225.61 | 0.0 | 0/11 |
| T-GC-In | Temperature at gas cooler / inlet | — | 76.63 | 121.65 | 168.38 | 0.0 | 0/11 |
| T-GC-Out | Temperature at gas cooler / outlet | — | -99895.53 | 52.55 | 1027.58 | 0.0 | 0/11 |
| T-GC-Fan2-In | Gas cooler fan 2 inlet air | °F | 27.91 | 63.54 | 97.72 | 0.0 | 0/11 |
| T-GC-Fan1-In | Temperature at gas cooler / fan 1 / inlet | — | -101143.95 | 496.61 | 1027.58 | 0.0 | 0/11 |
| T-GC-Fan2-Out | Gas cooler fan 2 outlet air | °F | 36.46 | 68.69 | 99.24 | 0.0 | 0/11 |
| T-GC-Fan1-Out | Temperature at gas cooler / fan 1 / outlet | — | 36.04 | 68.96 | 99.39 | 0.0 | 0/11 |
| T-MTRack-Suc-srf | Temperature at chilled compressor rack / suction / surface | — | 20.55 | 46.52 | 62.54 | 0.0 | 0/11 |
| T-LT-Ret | Temperature at freezer circuit / return | — | 7.24 | 35.51 | 70.78 | 0.0 | 0/11 |
| T-LT-Suc | Temperature at freezer circuit / suction | — | 35.46 | 40.68 | 72.81 | 0.0 | 0/11 |
| T-LT-Dis | Temperature at freezer circuit / discharge | — | 34.43 | 122.02 | 172.4 | 0.0 | 0/11 |
| T-MT-Suc | Temperature at chilled circuit / suction | — | 17.97 | 22.98 | 38.95 | 0.0 | 0/11 |
| T-MT-Dis | Temperature at chilled circuit / discharge | — | 76.59 | 123.5 | 173.04 | 0.0 | 0/11 |
| T-FalseLoad | Temperature at simulated refrigeration load | — | 28.11 | 62.12 | 80.63 | 0.0 | 0/11 |
| T-Spare-2D | Spare temperature input, placement unverified | — | -101063.92 | -99136.01 | -98072.99 | 0.0 | 0/11 |
| T-spare-3D | Spare temperature input, placement unverified | — | -101063.92 | -99136.01 | -98072.99 | 0.0 | 0/11 |
| T-Spare-4D | Spare temperature input, placement unverified | — | -101063.92 | -99136.01 | -98072.99 | 0.0 | 0/11 |
| T-MTCase-Liq-Srf | Temperature at chilled case / liquid line / surface | — | 21.89 | 27.29 | 48.57 | 0.0 | 0/11 |
| T-MTCase-Suc-Srf | Temperature at chilled case / suction / surface | — | 17.11 | 43.31 | 64.23 | 0.0 | 0/11 |
| T-MTCase-EEVOut | Temperature at chilled case / electronic expansion valve outlet | — | 8.19 | 18.84 | 59.4 | 0.0 | 0/11 |
| T-MTCase-Sup | Chilled-case evaporator supply air | °F | 27.17 | 32.4 | 60.42 | 0.0 | 0/11 |
| T-MTCase-Ret | Chilled-case evaporator return air | °F | 39.11 | 45.38 | 107.59 | 0.0 | 0/11 |
| T-MTCase-Suc | Temperature at chilled case / suction | — | 12.2 | 40.54 | 67.06 | 0.0 | 0/11 |
| T-101 | Numbered temperature probe, placement unverified | — | -2.89 | -0.16 | 53.27 | 0.0 | 0/11 |
| T-102 | Numbered temperature probe, placement unverified | — | -8.43 | -2.44 | 48.02 | 0.0 | 0/11 |
| T-103 | Numbered temperature probe, placement unverified | — | -3.79 | -2.9 | 49.84 | 0.0 | 0/11 |
| T-104 | Numbered temperature probe, placement unverified | — | -7.17 | -3.59 | 48.45 | 0.0 | 0/11 |
| T-105 | Numbered temperature probe, placement unverified | — | -4.32 | -3.57 | 51.41 | 0.0 | 0/11 |
| T-106 | Numbered temperature probe, placement unverified | — | -10.82 | -4.93 | 46.61 | 0.0 | 0/11 |
| T-107 | Numbered temperature probe, placement unverified | — | -5.77 | -1.5 | 51.27 | 0.0 | 0/11 |
| T-108 | Numbered temperature probe, placement unverified | — | -10.05 | -2.99 | 48.48 | 0.0 | 0/11 |
| T-109 | Numbered temperature probe, placement unverified | — | -5.97 | -0.69 | 48.31 | 0.0 | 0/11 |
| T-110 | Numbered temperature probe, placement unverified | — | -9.96 | -2.02 | 46.77 | 0.0 | 0/11 |
| T-111 | Numbered temperature probe, placement unverified | — | -2.2 | -0.39 | 48.16 | 0.0 | 0/11 |
| T-112 | Numbered temperature probe, placement unverified | — | -7.99 | -2.68 | 44.58 | 0.0 | 0/11 |
| T-113 | Numbered temperature probe, placement unverified | — | -3.36 | -1.62 | 47.18 | 0.0 | 0/11 |
| T-114 | Numbered temperature probe, placement unverified | — | -7.98 | -3.78 | 42.72 | 0.0 | 0/11 |
| T-115 | Numbered temperature probe, placement unverified | — | -4.7 | -3.39 | 45.43 | 0.0 | 0/11 |
| T-116 | Numbered temperature probe, placement unverified | — | -12.03 | -5.39 | 42.02 | 0.0 | 0/11 |
| T-201 | Numbered temperature probe, placement unverified | — | -4.9 | -0.93 | 46.82 | 0.0 | 0/11 |
| T-202 | Numbered temperature probe, placement unverified | — | -9.97 | -3.66 | 41.9 | 0.0 | 0/11 |
| T-203 | Numbered temperature probe, placement unverified | — | -4.22 | 0.28 | 45.96 | 0.0 | 0/11 |
| T-204 | Numbered temperature probe, placement unverified | — | -9.18 | -1.82 | 42.27 | 0.0 | 0/11 |
| T-205 | Numbered temperature probe, placement unverified | — | -2.19 | -0.34 | 46.13 | 0.0 | 0/11 |
| T-206 | Numbered temperature probe, placement unverified | — | -7.0 | -1.24 | 43.27 | 0.0 | 0/11 |
| T-207 | Numbered temperature probe, placement unverified | — | -3.13 | -2.26 | 43.76 | 0.0 | 0/11 |
| T-208 | Numbered temperature probe, placement unverified | — | -8.03 | -3.41 | 41.24 | 0.0 | 0/11 |
| T-209 | Numbered temperature probe, placement unverified | — | -6.28 | -3.09 | 43.23 | 0.0 | 0/11 |
| T-210 | Numbered temperature probe, placement unverified | — | -12.68 | -4.48 | 40.43 | 0.0 | 0/11 |
| T-211 | Numbered temperature probe, placement unverified | — | -5.58 | -1.52 | 43.35 | 0.0 | 0/11 |
| T-212 | Numbered temperature probe, placement unverified | — | -11.22 | -3.38 | 41.65 | 0.0 | 0/11 |
| T-213 | Numbered temperature probe, placement unverified | — | -4.32 | -0.07 | 43.65 | 0.0 | 0/11 |
| T-214 | Numbered temperature probe, placement unverified | — | -7.34 | -1.28 | 41.38 | 0.0 | 0/11 |
| T-215 | Numbered temperature probe, placement unverified | — | -2.75 | 3.95 | 46.26 | 0.0 | 0/11 |
| T-216 | Numbered temperature probe, placement unverified | — | -7.09 | -2.64 | 43.3 | 0.0 | 0/11 |
| T-301 | Numbered temperature probe, placement unverified | — | -3.73 | -2.32 | 44.26 | 0.0 | 0/11 |
| T-302 | Numbered temperature probe, placement unverified | — | -10.79 | -4.01 | 40.32 | 0.0 | 0/11 |
| T-303 | Numbered temperature probe, placement unverified | — | -6.13 | -2.78 | 38.77 | 0.0 | 0/11 |
| T-304 | Numbered temperature probe, placement unverified | — | -9.83 | -4.1 | 38.01 | 0.0 | 0/11 |
| T-305 | Numbered temperature probe, placement unverified | — | -6.0 | -1.94 | 42.88 | 0.0 | 0/11 |
| T-306 | Numbered temperature probe, placement unverified | — | -9.12 | -3.97 | 39.6 | 0.0 | 0/11 |
| T-307 | Numbered temperature probe, placement unverified | — | -6.03 | -0.53 | 43.62 | 0.0 | 0/11 |
| T-308 | Numbered temperature probe, placement unverified | — | -8.0 | -2.12 | 43.55 | 0.0 | 0/11 |
| T-309 | Numbered temperature probe, placement unverified | — | 33.94 | 36.48 | 40.58 | 0.0 | 0/11 |
| T-310 | Numbered temperature probe, placement unverified | — | 33.53 | 35.37 | 38.94 | 0.0 | 0/11 |
| T-311 | Numbered temperature probe, placement unverified | — | 33.35 | 35.29 | 43.32 | 0.0 | 0/11 |
| T-312 | Numbered temperature probe, placement unverified | — | 33.85 | 35.93 | 42.2 | 0.0 | 0/11 |
| T-313 | Numbered temperature probe, placement unverified | — | 93.49 | 103.7 | 120.31 | 0.0 | 0/11 |
| T-314 | Numbered temperature probe, placement unverified | — | 34.82 | 36.69 | 39.35 | 0.0 | 0/11 |
| T-315 | Numbered temperature probe, placement unverified | — | 26.57 | 33.35 | 61.92 | 0.0 | 0/11 |
| T-316 | Numbered temperature probe, placement unverified | — | 60.16 | 66.5 | 75.67 | 0.0 | 0/11 |
| T-401 | Numbered temperature probe, placement unverified | — | 36.85 | 41.01 | 51.33 | 0.0 | 0/11 |
| T-402 | Numbered temperature probe, placement unverified | — | 32.1 | 34.94 | 48.41 | 0.0 | 0/11 |
| T-403 | Numbered temperature probe, placement unverified | — | 30.8 | 33.1 | 50.24 | 0.0 | 0/11 |
| T-404 | Numbered temperature probe, placement unverified | — | 36.4 | 39.81 | 53.54 | 0.0 | 0/11 |
| T-405 | Numbered temperature probe, placement unverified | — | 35.82 | 41.36 | 47.64 | 0.0 | 0/11 |
| T-406 | Numbered temperature probe, placement unverified | — | 30.61 | 36.56 | 49.24 | 0.0 | 0/11 |
| T-407 | Numbered temperature probe, placement unverified | — | 35.69 | 38.21 | 50.81 | 0.0 | 0/11 |
| T-408 | Numbered temperature probe, placement unverified | — | 31.41 | 33.8 | 46.6 | 0.0 | 0/11 |
| T-409 | Numbered temperature probe, placement unverified | — | 34.79 | 36.82 | 48.02 | 0.0 | 0/11 |
| T-410 | Numbered temperature probe, placement unverified | — | 29.48 | 32.87 | 48.19 | 0.0 | 0/11 |
| T-411 | Numbered temperature probe, placement unverified | — | 35.01 | 39.07 | 47.53 | 0.0 | 0/11 |
| T-412 | Numbered temperature probe, placement unverified | — | 29.85 | 35.5 | 48.06 | 0.0 | 0/11 |
| T-413 | Numbered temperature probe, placement unverified | — | 35.97 | 38.31 | 53.17 | 0.0 | 0/11 |
| T-414 | Numbered temperature probe, placement unverified | — | 31.0 | 33.14 | 47.72 | 0.0 | 0/11 |
| T-415 | Numbered temperature probe, placement unverified | — | 35.04 | 36.88 | 46.77 | 0.0 | 0/11 |
| T-416 | Numbered temperature probe, placement unverified | — | 29.43 | 32.96 | 46.56 | 0.0 | 0/11 |
| T-501 | Numbered temperature probe, placement unverified | — | 35.84 | 39.09 | 46.98 | 0.0 | 0/11 |
| T-502 | Numbered temperature probe, placement unverified | — | 28.93 | 34.61 | 47.81 | 0.0 | 0/11 |
| T-503 | Numbered temperature probe, placement unverified | — | 36.57 | 39.03 | 48.98 | 0.0 | 0/11 |
| T-504 | Numbered temperature probe, placement unverified | — | 30.46 | 34.0 | 44.61 | 0.0 | 0/11 |
| T-505 | Numbered temperature probe, placement unverified | — | 34.84 | 37.19 | 64.4 | 0.0 | 0/11 |
| T-506 | Numbered temperature probe, placement unverified | — | 31.36 | 33.93 | 45.68 | 0.0 | 0/11 |
| T-507 | Numbered temperature probe, placement unverified | — | 35.55 | 40.2 | 46.76 | 0.0 | 0/11 |
| T-508 | Numbered temperature probe, placement unverified | — | 29.59 | 35.81 | 46.02 | 0.0 | 0/11 |
| T-509 | Numbered temperature probe, placement unverified | — | 38.17 | 41.13 | 54.77 | 0.0 | 0/11 |
| T-510 | Numbered temperature probe, placement unverified | — | 29.58 | 33.0 | 45.34 | 0.0 | 0/11 |
| T-511 | Numbered temperature probe, placement unverified | — | 38.58 | 41.41 | 63.97 | 0.0 | 0/11 |
| T-512 | Numbered temperature probe, placement unverified | — | 34.68 | 37.73 | 47.45 | 0.0 | 0/11 |
| T-513 | Numbered temperature probe, placement unverified | — | 37.4 | 42.07 | 50.76 | 0.0 | 0/11 |
| T-514 | Numbered temperature probe, placement unverified | — | 31.26 | 35.99 | 45.92 | 0.0 | 0/11 |
| T-515 | Numbered temperature probe, placement unverified | — | 33.79 | 35.53 | 46.23 | 0.0 | 0/11 |
| T-516 | Numbered temperature probe, placement unverified | — | 34.2 | 35.97 | 39.25 | 0.0 | 0/11 |
| T-LT_BPHX_H20_INLET | Temperature at freezer circuit / brazed-plate heat exchanger / water / INLET | — | 61.14 | 66.9 | 74.67 | 0.0 | 0/11 |
| T-LT_BPHX_H20_OUTLET | Temperature at freezer circuit / brazed-plate heat exchanger / water / OUTLET | — | 61.33 | 67.19 | 74.81 | 0.0 | 0/11 |
| T-MT_BPHX_H20_INLET | Temperature at chilled circuit / brazed-plate heat exchanger / water / INLET | — | 37.02 | 73.35 | 103.77 | 0.0 | 0/11 |
| T-MT_BPHX_H20_OUTLET | Temperature at chilled circuit / brazed-plate heat exchanger / water / OUTLET | — | 35.65 | 73.14 | 102.24 | 0.0 | 0/11 |
| T-LT_BPHX_C02_EXIT | Temperature at freezer circuit / brazed-plate heat exchanger / CO₂ / EXIT | — | 60.62 | 67.09 | 75.1 | 0.0 | 0/11 |
| T-MT_BPHX_C02_EXIT | Temperature at chilled circuit / brazed-plate heat exchanger / CO₂ / EXIT | — | 14.86 | 71.34 | 95.67 | 0.0 | 0/10 |
| F-LT-BPHX | Flow at freezer circuit / brazed-plate heat exchanger | — | -101203.12 | -99303.4 | -98234.02 | 0.0 | 0/11 |
| F-MT-BPHX | Flow at chilled circuit / brazed-plate heat exchanger | — | -101231.38 | -99328.08 | -98261.5 | 0.0 | 0/11 |
| <blank header at column 162> | Unnamed CSV field, meaning unknown | — | -101231.38 | -99328.08 | -98261.5 | 0.0 | 0/11 |
| SupHCompSuc | Compressor suction superheat | — | 0.0 | 0.0 | 53.9 | 0.0 | 8/11 |
| SupHCompDisc | Compressor discharge superheat | — | 0.0 | 5.55 | 59.44 | 0.0 | 1/11 |
| SupHEvap1 | Evaporator 1 superheat | — | — | — | — | 100.0 | 0/11 |
| SupHEvap2 | Evaporator 2 superheat | — | — | — | — | 100.0 | 0/11 |
| SubClComCond | Condenser subcooling (exact point unverified) | — | — | — | — | 100.0 | 0/11 |
| SubcoolCond1 | Condenser subcooling 1 | — | — | — | — | 100.0 | 0/11 |
| SubcoolCond2 | Condenser subcooling 2 | — | — | — | — | 100.0 | 0/11 |
| SuncoolLiq | Likely liquid-line subcooling | — | — | — | — | 100.0 | 0/11 |
| RefHSct | Likely refrigerant suction enthalpy | — | — | — | — | 100.0 | 0/11 |
| RefHLiq | Likely liquid refrigerant enthalpy | — | — | — | — | 100.0 | 0/11 |
| Tsetpt | Temperature setpoint | — | — | — | — | 100.0 | 0/11 |
| RHsetpt | Relative humidity setpoint | — | — | — | — | 100.0 | 0/11 |
| AirHRet | Return-air enthalpy | — | — | — | — | 100.0 | 0/11 |
| AirHSup | Supply-air enthalpy | — | — | — | — | 100.0 | 0/11 |
| TstatSuc | Likely suction saturation temperature | — | — | — | — | 100.0 | 0/11 |
| TstatCondExit | Likely condenser exit saturation temperature | — | — | — | — | 100.0 | 0/11 |
| TstatDisc | Likely discharge saturation temperature | — | — | — | — | 100.0 | 0/11 |
| TstatSubClExit | Likely subcooler exit saturation temperature | — | — | — | — | 100.0 | 0/11 |
| CapaAirside | Air-side capacity | — | — | — | — | 100.0 | 0/11 |
| CapaRefrside | Refrigerant-side capacity | — | — | — | — | 100.0 | 0/11 |
| EnergyBalance | Energy balance | — | — | — | — | 100.0 | 0/11 |
| EERA | Energy efficiency ratio (A variant) | — | — | — | — | 100.0 | 0/11 |
| EER | Energy efficiency ratio | — | — | — | — | 100.0 | 0/11 |
| T-LT_BPHX_C02_EXIT [duplicate at column 159] | Temperature at freezer circuit / brazed-plate heat exchanger / CO₂ / EXIT | — | 85.36 | 88.32 | 91.64 | 0.0 | 0/1 |

Open [sensor_data.ipynb](../notebooks/sensor_data.ipynb) for per-run profiles, fault comparisons and plots. Run all cells to regenerate this guide.
