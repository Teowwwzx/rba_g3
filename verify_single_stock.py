import pandas as pd
import numpy as np

def verify_stock(ticker, prices_file):
    print(f"--- Verifying {ticker} ---")
    
    # 1. Load Prices
    print(f"Loading prices from {prices_file}...")
    df = pd.read_csv(prices_file, index_col=0, parse_dates=True)
    
    if ticker not in df.columns:
        print(f"Error: {ticker} not found in file.")
        return

    # 2. Extract Series
    series = df[ticker].dropna()
    print(f"\nTotal Data Points: {len(series)}")
    
    if series.empty:
        print("Series is empty.")
        return

    # 3. Check Duration
    start_date = series.index[0]
    end_date = series.index[-1]
    duration_days = (end_date - start_date).days
    duration_years = duration_days / 365.25
    
    print(f"Start Date: {start_date.date()}")
    print(f"End Date:   {end_date.date()}")
    print(f"Duration:   {duration_days} days (~{duration_years:.2f} years)")
    
    is_5y = duration_years >= 5.0
    print(f"Passes 5Y Check? {'YES' if is_5y else 'NO'}")

    # 4. Calculate Returns
    # Formula: (Price_t - Price_t-1) / Price_t-1
    daily_returns = series.pct_change().dropna()
    
    avg_daily_return = daily_returns.mean()
    avg_daily_return_pct = avg_daily_return * 100
    
    print(f"\nAverage Daily Return: {avg_daily_return:.6f} ({avg_daily_return_pct:.4f}%)")
    
    is_qualified = avg_daily_return > 0.0025
    print(f"Passes >0.25% Check? {'YES' if is_qualified else 'NO'}")
    
    # Show first 5 and last 5 prices
    print("\nFirst 5 Prices:")
    print(series.head())
    print("\nLast 5 Prices:")
    print(series.tail())

if __name__ == "__main__":
    # BCM ALLIANCE BERHAD (0187.KL) from ACE Market
    verify_stock("0187.KL", "datasets/dataset_ace_prices_wide.csv")
