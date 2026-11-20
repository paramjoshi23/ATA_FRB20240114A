# ATA FRB 20240114A Analysis

This repository contains the analysis and publication-plotting code for bursts from **FRB 20240114A** observed with the Allen Telescope Array (ATA). It includes burst-property calculations, cumulative-distribution plots, frequency-versus-time/MJD plots, violin plots, drift-rate analysis, waterfall plots, and utilities for combining figures.

The accompanying paper is **“High Frequency Wideband Study of FRB 20240114A with the Allen Telescope Array”** by Joshi et al. (2026), [arXiv:2606.31897](https://arxiv.org/abs/2606.31897).

## Scientific scope

The scripts in this repository support calculations and figures involving:

- peak flux density and fluence;
- isotropic burst energy;
- minimum detectable fluence and minimum detectable energy;
- combined SNR for sub-bursts;
- cumulative fluence, energy, and spectral-energy-density distributions;
- burst bandwidth, duration, energy, fractional bandwidth, and drift-rate distributions;
- frequency-versus-MJD coverage and burst occurrence;
- normalized drift rate versus duration;
- ATA frequency coverage and on-sky observing time;
- publication-ready frequency/time waterfall plots for individual bursts.

## Repository layout

### Burst-property data

| File | Purpose |
| --- | --- |
| `FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv` | Primary burst-property table included in the repository. It contains burst IDs, 3-sigma durations and bandwidths, drift slopes and errors, center frequencies, isotropic energies, and fluences. |
| `effelsberg_bursts.csv` | Effelsberg burst catalog used by the frequency-versus-MJD scripts. |
| `parkes_bursts.csv` | Murriyang/Parkes burst catalog used by the frequency-versus-MJD scripts. |
| `Filterbank_FRB_Main_JSON_database.json` | ATA filterbank stream metadata: start times, sample counts, sample intervals, channel counts, channel frequencies, and burst names. |
| `NEW_FINAL_FRB_properties_JSON.json` | ATA burst-property JSON used to match burst names to MJD and center frequency. |

The repository is designed to generate additional data and image files such as `*_plot_paper_final.png`, cumulative-distribution PNGs, violin PNGs, and text arrays from the four calculation scripts described below. Those generated products are not all currently included.

> **NPZ and intermediate-text inputs:** `plot_FRB_npz_paper_FINAL3.py` requires an external `.npz` burst waterfall file (https://doi.org/10.5281/zenodo.19429570 contains all the NPZ files for the 97 bursts), and the flux/fluence/energy calculation scripts require plain-text arrays that are not included in this repository. See the script table and pipeline below.

## Script reference

### Calculations

| Script | Input | Output | Description |
| --- | --- | --- | --- |
| `calc_flux.py` | `sefd.txt`, `snr.txt`, `3sigma_durations_new.txt`, `3sigma_bandwidths_new.txt` | `flux_output_new.txt` | Calculates peak flux density from SEFD, SNR, 3-sigma burst duration, bandwidth, and two polarizations using the radiometer equation. |
| `calc_fluence.py` | `flux_output_new.txt`, `3sigma_durations_new.txt` | `fluence_output_new.txt` | Multiplies peak flux density by burst duration to calculate fluence in Jy-ms. |
| `calc_burst_energy.py` | `fluence_output_new.txt`, `3sigma_bandwidths_new.txt` | `FRB_burst_energy_new.txt` | Converts fluence and bandwidth into isotropic burst energy in erg using the luminosity distance of 630.72 Mpc. |
| `calc_combined_SNR.py` | `subbursts_SNR.txt`, containing SNR and width columns | Terminal result | Computes a weighted combined SNR for sub-bursts. |
| `calc_min_detectable_fluence.py` | `SEFD_Jy` command-line argument | Terminal result | Calculates minimum detectable flux density and 1-ms fluence using SNR 10, duration 1 ms, bandwidth 1344 MHz, and two polarizations. |
| `calc_min_burst_energy_manual_fluence.py` | One or more fluence values in Jy-ms passed as arguments or entered interactively | Terminal result | Calculates minimum burst energy for manually supplied fluence values using 1344 MHz bandwidth and the same luminosity-distance formula as `calc_burst_energy.py`. |

Examples:

```bash
python calc_min_detectable_fluence.py 40
python calc_min_burst_energy_manual_fluence.py 0.5 1.2 3.0
```

The four array-based calculation scripts use fixed filenames and must be run sequentially from this directory:

```text
sefd.txt + snr.txt + durations + bandwidths
                    |
                    v
calc_flux.py -> flux_output_new.txt
                    |
                    v
calc_fluence.py -> fluence_output_new.txt
                    |
                    v
calc_burst_energy.py -> FRB_burst_energy_new.txt
```

### Distribution plots

| Script | Primary input | Default output | Figure |
| --- | --- | --- | --- |
| `plot_cummulative_fluence_dist.py` | Burst-property CSV, using `Fluence (Jy-ms)` | `cumulative_fluence_distribution.png` | Cumulative fluence distribution, divided into combined bursts and sub-bursts. |
| `plot_cummulative_energy_dist_powerlaw_fit.py` | Burst-property CSV, using `Isotropic Burst Energy (ergs)` | `cumulative_energy_distribution_powerlaw_fit.png` | Cumulative energy distribution with a log-space power-law fit. |
| `plot_cummulative_spectral_energy_density_dist_powerlaw_fit.py` | Burst-property CSV, using energy and 3-sigma bandwidth | `cumulative_spectral_energy_density_dist_powerlaw_fit_ata_FINAL.png` | Cumulative spectral-energy-density distribution with a log-space power-law fit. |

Run a distribution script with an explicit input/output where needed:

```bash
python plot_cummulative_fluence_dist.py --input FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv --output cumulative_fluence_distribution.png
python plot_cummulative_energy_dist_powerlaw_fit.py --input FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv --output cumulative_energy_distribution_powerlaw_fit.png
python plot_cummulative_spectral_energy_density_dist_powerlaw_fit.py --input FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv
```

The cumulative scripts treat the first 98 rows as combined bursts and remaining rows as sub-bursts; this split can be changed with `--split-index` in `plot_cummulative_fluence_dist.py`.

### Violin and frequency-bin plots

| Script | Primary input | Default output | Figure |
| --- | --- | --- | --- |
| `violin_plot_bandwidth_paper.py` | Burst-property CSV, `3-sigma Bandwidth (MHz)` and `center_f` | `violin_plot_bandwidth_FINAL.png` | Bandwidth distribution in 500-MHz center-frequency bins. |
| `violin_plot_duration_paper.py` | Burst-property CSV, `3-sigma Duration (ms)` and `center_f` | `violin_plot_duration_FINAL.png` | Duration distribution in frequency bins. |
| `violin_plot_energy_paper.py` | Burst-property CSV, isotropic energy and `center_f` | `violin_plot_energy_FINAL.png` | Isotropic-energy distribution in frequency bins. |
| `violin_plot_fractional_bandwidth_paper.py` | Burst-property CSV, bandwidth and `center_f` | `violin_plot_fractional_bandwidth_FINAL.png` | Fractional-bandwidth distribution in frequency bins. |
| `violin_plot_drift_rate_paper.py` | `_new.csv`, `slope (mhz/ms)` and `center_f` | `violin_plot_drift_rate_FINAL.png` | Magnitude of negative drift rates in frequency bins. |

Example:

```bash
python violin_plot_drift_rate_paper.py --input FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv --output violin_plot_drift_rate_FINAL.png --bins 4
python violin_plot_duration_paper.py --input FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv --output violin_plot_duration_FINAL.png
```

The violin scripts default to 1000–4500 MHz in 500-MHz steps and generally support `--input`, `--output`, `--bins`, and `--title`; use `python <script> --help` for the exact options.

### Frequency, drift, and waterfall plots

| Script | Input | Output | Figure |
| --- | --- | --- | --- |
| `plot_frequency_vs_mjd_with_histogram.py` | `Filterbank_FRB_Main_JSON_database.json`, `NEW_FINAL_FRB_properties_JSON.json`, Effelsberg/Parkes CSV catalogs | `frb20240114a_frequency_vs_mjd_with_histogram.png` and `.pdf` | Bursts versus MJD overlaid with ATA observing bands, plus a sideways on-sky-time histogram. |
| `plot_frequency_common.py` | Shared JSON/CSV data helpers imported by the frequency plots | No standalone figure | Resolves burst names, loads telescope catalogs, applies publication styling, and draws ATA observing bands. |
| `plot_OnSky_time_frequency_histogram.py` | Observation center frequencies and on-sky hours embedded in the script | `frequency_histogram_bold.png` | On-sky observing time distributed across observed frequency bands. |
| `plot_normalised_drift_rate_vs_duration.py` | Burst-property CSV passed with `--csv` | `normalised_drift_rate_vs_duration_paper_FINAL.png` | Normalized drift rate (center frequency divided by absolute drift slope) versus duration for multi-component bursts, with an optional orthogonal-distance-regression fit. |
| `plot_FRB_npz_paper_FINAL3.py` | A burst `.npz` waterfall archive supplied as a positional argument | `<burst-name>_plot_paper_final.png` | Individual-burst waterfall and integrated intensity profile. |
| `create_png_collage.py` | Any list of PNG files or a directory supplied by `--dir` | User-selected output PNG | Combines publication figures into a labeled or unlabeled grid collage. |

Frequency-versus-MJD plot:

```bash
python plot_frequency_vs_mjd_with_histogram.py
```

Normalized drift-rate plot:

```bash
python plot_normalised_drift_rate_vs_duration.py --csv FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv --out normalised_drift_rate_vs_duration_paper_FINAL.png
```

Waterfall plot:

```bash
python plot_FRB_npz_paper_FINAL3.py BURST.npz -fdown 1 -tdown 1 -time 20
```

The NPZ archive is expected to contain a `wfall` array plus metadata such as `bandwidth`, `duration`, and `dfs`. The script uses `--subburst_offsets` and `--onpulse_widths` to annotate sub-burst regions.

Collage example:

```bash
python create_png_collage.py publication_collage.png --dir . --layout 2 3 --img-size 600
```

## Shell workflow

`run_FRB_plots_all.bash` is a Bash launcher for regenerating the plot set. Review its contents before running it because generated-file paths and input filenames may be environment- or machine-specific.

```bash
bash run_FRB_plots_all.bash
```

## Installation

Python 3.9 or newer is recommended.

Create an isolated environment and install all dependencies:

```bash
python -m venv .venv
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the requirements:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Dependency summary

| Package | Used for |
| --- | --- |
| `numpy` | Array arithmetic, text-array loading/saving, NPZ waterfalls, and statistical calculations. |
| `matplotlib` | All plotting and image output. |
| `pandas` | Loading and cleaning burst-property CSV tables. |
| `scipy` | Power-law curve fitting and orthogonal-distance-regression drift fitting. |
| `seaborn` | Violin-plot styling. |
| `Pillow` | Reading, resizing, and combining PNG figures in the collage utility. |

## Running from the repository root

Run plotting scripts from the repository root unless passing absolute or relative input/output paths. Several scripts use repository-root-relative defaults and save their PNG/PDF outputs to the current directory.

```bash
python plot_frequency_vs_mjd_with_histogram.py
python plot_cummulative_fluence_dist.py --input FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv
python violin_plot_duration_paper.py --input FRB_burst_properties_paper_all_with_subbursts_with_errors_rounded2_new.csv
```

Use `python <script-name> --help` to inspect the command-line options supported by each script.

## License

See [LICENSE](LICENSE).
