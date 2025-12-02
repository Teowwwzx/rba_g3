# Datasets Directory

This folder contains all the data files used by the RBA Robo-Advisor.

## Core Datasets (Used by Website)
These files are the primary source of truth for the dashboard.
- **`dataset_ace_companies.csv`**: Raw list of ACE Market companies.
- **`dataset_main_companies.csv`**: Raw list of Main Market companies.
- **`dataset_ace_prices_wide.csv`**: Historical daily prices for ACE Market stocks (wide format).
- **`dataset_main_prices_wide.csv`**: Historical daily prices for Main Market stocks (wide format).
- **`dataset_bond_yield.csv`**: Historical Malaysia 10-Year Bond Yields.
- **`dataset_klci.csv`**: Historical KLCI index data.
- **`dataset_ace_cleaned_companies.csv`**: List of "Qualified" ACE Market companies (filtered by 5Y duration & >0.25% avg return).
- **`dataset_main_cleaned_companies.csv`**: List of "Qualified" Main Market companies.

## Subfolders
- **`intermediate/`**: Contains temporary or intermediate files generated during the data processing pipeline (e.g., cleaned price matrices used for generating final Excel/CSV exports). These are not directly used by the live website.

## Data Pipeline Scripts
1. `generate_datasets.py`: Downloads raw data -> Outputs Core Datasets.
2. `filter_datasets.py`: Filters for qualified stocks -> Outputs `_cleaned_companies.csv` (Core) and `_cleaned_prices.csv` (Intermediate).
3. `combine_datasets.py`: Merges data -> Outputs final user-friendly files to `../final_datasets/`.
