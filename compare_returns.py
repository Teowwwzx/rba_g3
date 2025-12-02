import pandas as pd
import numpy as np
import os

def compare_stock_returns(tickers, prices_file):
    print(f"--- Comparing Returns (Full vs 5Y) ---")
    print(f"File: {prices_file}")
    
    if not os.path.exists(prices_file):
        print("File not found.")
        return

    df = pd.read_csv(prices_file, index_col=0, parse_dates=True)
    
    print(f"{'Ticker':<10} | {'Full Avg (%)':<12} | {'5Y Avg (%)':<12} | {'Diff (%)':<10} | {'Status'}")
    print("-" * 70)
    
    for ticker in tickers:
        if ticker not in df.columns:
            continue
            
        series = df[ticker].dropna()
        if series.empty:
            continue
            
        # Daily Returns
        daily_returns = series.pct_change().dropna()
        
        # 1. Full History Average
        full_avg = daily_returns.mean() * 100
        
        # 2. Last 5 Years (1260 Days) Average
        recent_returns = daily_returns.tail(1260)
        five_year_avg = recent_returns.mean() * 100
        
        diff = five_year_avg - full_avg
        
        # Status change? (Threshold 0.25%)
        passed_full = full_avg > 0.25
        passed_5y = five_year_avg > 0.25
        
        status = "Same"
        if passed_full and not passed_5y:
            status = "DROPPED"
        elif not passed_full and passed_5y:
            status = "GAINED"
            
        print(f"{ticker:<10} | {full_avg:<12.4f} | {five_year_avg:<12.4f} | {diff:<10.4f} | {status}")

if __name__ == "__main__":
    # Sample Tickers from ACE Market
    # 0187.KL (BCM), 0079.KL (Aldrich), 0152.KL (DGB)
    tickers = ["0187.KL", "0079.KL", "0152.KL", "0335.KL"]
    compare_stock_returns(tickers, "datasets/dataset_ace_prices_wide.csv")
