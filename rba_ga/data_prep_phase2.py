import pandas as pd
import yfinance as yf
import datetime
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
HTML_FILE = '../ace_market_companies_list.html'
BENCHMARK_TICKER = '^KLSE'
# Note: Yahoo Finance often doesn't have a clean ticker for Malaysia 10Y Bond. 
# We will use a constant approximation if download fails, or try to find one.
# For now, we will create a column with a fixed rate if we can't find it, 
# as is common in academic assignments when data is restricted.
# Current Malaysia 10Y is approx 3.8% - 4.0%.
RISK_FREE_RATE_ANNUAL = 0.04 

def get_stock_codes(html_path):
    if not os.path.exists(html_path):
        # Fallback
        html_path = 'C:/Users/teowz/OneDrive/Documents/GitHub/rba_g2/ace_market_companies_list.html'
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    codes = []
    for row in soup.find_all('tr'):
        link = row.find('a', href=True)
        if link and 'stock_code=' in link['href']:
            code = link['href'].split('stock_code=')[1].split('&')[0]
            codes.append(f"{code}.KL")
    return list(set(codes)) # Remove duplicates

def download_data():
    print("--- Starting Data Preparation Phase 2 ---")
    
    # 1. Get Stock Codes
    tickers = get_stock_codes(HTML_FILE)
    print(f"Found {len(tickers)} tickers in HTML.")
    
    # 2. Define Date Range (6 Years)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365*6)
    
    # 3. Download All Stocks to filter Top 50
    print("Downloading data for all stocks to filter Top 50...")
    # Use auto_adjust=False to ensure we get 'Adj Close' if available, or just standard columns
    data = yf.download(tickers, start=start_date, end=end_date, progress=True, auto_adjust=False)
    
    # Debug: Print columns
    # print("Columns:", data.columns)
    
    # Extract Closing Prices
    if 'Adj Close' in data.columns:
        df_close = data['Adj Close']
    elif 'Close' in data.columns:
        df_close = data['Close']
    else:
        # Fallback for single level columns if only one ticker (unlikely here) or flat format
        # If data is (Ticker, Price) or (Price, Ticker)
        # Let's try to find 'Adj Close' in level 0 or 1
        try:
            df_close = data.xs('Adj Close', axis=1, level=0)
        except:
            try:
                df_close = data.xs('Adj Close', axis=1, level=1)
            except:
                print("Could not find 'Adj Close' or 'Close' in columns.")
                return

    # Calculate Average Daily Return
    # pct_change() gives daily return. mean() gives average.
    avg_daily_returns = df_close.pct_change().mean() * 100
    
    # Sort and take Top 50
    top_50_tickers = avg_daily_returns.sort_values(ascending=False).head(50).index.tolist()
    print(f"Selected Top 50 stocks. Top return: {avg_daily_returns.max():.4f}%, 50th return: {avg_daily_returns[top_50_tickers[-1]]:.4f}%")
    
    # 4. Download Final Dataset (Stocks + Benchmark)
    final_tickers = top_50_tickers + [BENCHMARK_TICKER]
    print("Downloading final dataset (Stocks + Benchmark)...")
    
    # Use auto_adjust=False to be consistent
    df_final = yf.download(final_tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)
    
    df_prices = pd.DataFrame()
    
    for t in final_tickers:
        try:
            # Check if ticker exists in the downloaded data
            if t in df_final.columns.levels[0]:
                # Try to get Adj Close, then Close
                if 'Adj Close' in df_final[t].columns:
                    series = df_final[t]['Adj Close']
                elif 'Close' in df_final[t].columns:
                    series = df_final[t]['Close']
                else:
                    print(f"Warning: No Close price for {t}")
                    continue
                
                df_prices[t] = series
            else:
                print(f"Warning: {t} not found in download columns.")
        except Exception as e:
            print(f"Error extracting {t}: {e}")

    # 5. Add Risk Free Rate
    df_prices['MGS_10Y'] = RISK_FREE_RATE_ANNUAL
    
    # 6. Clean Data
    # Check if Benchmark exists
    if BENCHMARK_TICKER in df_prices.columns:
        # Drop rows where Benchmark is NaN (market closed)
        df_prices = df_prices.dropna(subset=[BENCHMARK_TICKER])
    else:
        print(f"CRITICAL WARNING: Benchmark {BENCHMARK_TICKER} missing from data. Skipping dropna based on benchmark.")
    
    # Forward fill stock prices (if a stock didn't trade but market was open)
    df_prices = df_prices.fillna(method='ffill')
    # Backward fill for initial gaps
    df_prices = df_prices.fillna(method='bfill')
    
    # 7. Save
    output_path = 'cleaned_dataset.csv'
    df_prices.to_csv(output_path)
    print(f"Saved cleaned dataset to {output_path}")
    print(f"Shape: {df_prices.shape}")
    print("Columns:", df_prices.columns.tolist())

if __name__ == "__main__":
    download_data()
