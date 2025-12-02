import pandas as pd
import os
import numpy as np

DATA_DIR = "datasets"

def filter_market(market_name, companies_file, prices_file, output_prefix):
    print(f"--- Filtering {market_name} ---")
    comp_path = os.path.join(DATA_DIR, companies_file)
    price_path = os.path.join(DATA_DIR, prices_file)
    
    if not os.path.exists(comp_path) or not os.path.exists(price_path):
        print(f"Error: Files missing for {market_name}")
        return

    # Load Data
    df_comp = pd.read_csv(comp_path)
    # Load prices with Date as index
    df_prices = pd.read_csv(price_path, index_col=0, parse_dates=True)
    
    print(f"Initial Companies: {len(df_comp)}")
    print(f"Initial Price Columns: {len(df_prices.columns)}")
    
    valid_tickers = []
    
    for ticker in df_prices.columns:
        series = df_prices[ticker].dropna()
        
        if series.empty:
            continue
            
        # 1. Check Duration (5 Years = 1825 Days)
        start_date = series.index[0]
        end_date = series.index[-1]
        duration_days = (end_date - start_date).days
        
        if duration_days < 1825:
            continue
            
        # 2. Check Avg Daily Return > 0.25%
        daily_returns = series.pct_change().dropna()
        avg_return = daily_returns.mean()
        
        if avg_return <= 0.0025:
            continue
            
        # If passed both
        valid_tickers.append({
            'Ticker': ticker,
            'Avg_Return': avg_return,
            'Duration_Days': duration_days,
            'Start_Date': start_date,
            'End_Date': end_date
        })
        
    print(f"Qualified Tickers: {len(valid_tickers)}")
    
    if not valid_tickers:
        print("No companies met the criteria.")
        return

    # Create Filtered DataFrames
    df_valid_stats = pd.DataFrame(valid_tickers)
    valid_ticker_list = df_valid_stats['Ticker'].tolist()
    
    # Filter Companies Metadata
    # Ensure Ticker column matches type
    df_comp['Ticker'] = df_comp['Ticker'].astype(str)
import pandas as pd
import os
import numpy as np

DATA_DIR = "datasets"

def filter_market(market_name, companies_file, prices_file): # Removed output_prefix
    print(f"--- Filtering {market_name} ---")
    comp_path = os.path.join(DATA_DIR, companies_file)
    price_path = os.path.join(DATA_DIR, prices_file)
    
    if not os.path.exists(comp_path) or not os.path.exists(price_path):
        print(f"Error: Files missing for {market_name}")
        return None, None # Return None for both dataframes

    # Load Data
    df_comp = pd.read_csv(comp_path)
    # Load prices with Date as index
    df_prices = pd.read_csv(price_path, index_col=0, parse_dates=True)
    
    print(f"Initial Companies: {len(df_comp)}")
    print(f"Initial Price Columns: {len(df_prices.columns)}")
    
    valid_tickers = []
    
    for ticker in df_prices.columns:
        series = df_prices[ticker].dropna()
        
        if series.empty:
            continue
            
        # 1. Check Duration (5 Years = 1825 Days)
        start_date = series.index[0]
        end_date = series.index[-1]
        duration_days = (end_date - start_date).days
        
        if duration_days < 1825:
            continue
            
        # 2. Check Avg Daily Return > 0.25%
        daily_returns = series.pct_change().dropna()
        
        # STRICT REQUIREMENT: "past five (5) years"
        # We take the last 1260 trading days (5 * 252) to be fair and consistent
        recent_returns = daily_returns.tail(1260)
        avg_return = recent_returns.mean()
        
        if avg_return <= 0.0025:
            continue
            
        # If passed both
        valid_tickers.append({
            'Ticker': ticker,
            'Avg_Return': avg_return,
            'Duration_Days': duration_days,
            'Start_Date': start_date,
            'End_Date': end_date
        })
        
    print(f"Qualified Tickers: {len(valid_tickers)}")
    
    if not valid_tickers:
        print("No companies met the criteria.")
        return None, None # Return None for both dataframes

    # Create Filtered DataFrames
    df_valid_stats = pd.DataFrame(valid_tickers)
    valid_ticker_list = df_valid_stats['Ticker'].tolist()
    
    # Filter Companies Metadata
    # Ensure Ticker column matches type
    df_comp['Ticker'] = df_comp['Ticker'].astype(str)
    df_cleaned_comp = df_comp[df_comp['Ticker'].isin(valid_ticker_list)].copy()
    
    # Merge stats (Avg Return) into metadata
    df_cleaned_comp = df_cleaned_comp.merge(df_valid_stats[['Ticker', 'Avg_Return', 'Duration_Days']], on='Ticker', how='left')
    
    # Filter Prices
    df_cleaned_prices = df_prices[valid_ticker_list]
    
    # Return the cleaned dataframes instead of saving them
    return df_cleaned_comp, df_cleaned_prices

def main():
    datasets_dir = DATA_DIR # Use DATA_DIR as datasets_dir

    # ACE Market
    ace_cleaned_companies, ace_cleaned_prices = filter_market("ACE Market", "dataset_ace_companies.csv", "dataset_ace_prices_wide.csv")
    
    # Main Market
    main_cleaned_companies, main_cleaned_prices = filter_market("Main Market", "dataset_main_companies.csv", "dataset_main_prices_wide.csv")

    # Save Cleaned Datasets
    print("Saving cleaned datasets...")
    
    # Companies (Metadata) - Keep in main datasets folder as they are small and useful
    if ace_cleaned_companies is not None:
        ace_cleaned_companies.to_csv(os.path.join(datasets_dir, "dataset_ace_cleaned_companies.csv"), index=False)
    if main_cleaned_companies is not None:
        main_cleaned_companies.to_csv(os.path.join(datasets_dir, "dataset_main_cleaned_companies.csv"), index=False)
    
    # Prices (Wide) - Move to intermediate folder to reduce clutter
    intermediate_dir = os.path.join(datasets_dir, "intermediate")
    if not os.path.exists(intermediate_dir):
        os.makedirs(intermediate_dir)
        
    if ace_cleaned_prices is not None:
        ace_cleaned_prices.to_csv(os.path.join(intermediate_dir, "dataset_ace_cleaned_prices.csv"))
    if main_cleaned_prices is not None:
        main_cleaned_prices.to_csv(os.path.join(intermediate_dir, "dataset_main_cleaned_prices.csv"))
    
    print(f"Saved cleaned company lists to {datasets_dir}")
    print(f"Saved cleaned price data to {intermediate_dir}")

if __name__ == "__main__":
    main()
