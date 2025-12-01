import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import os
from bs4 import BeautifulSoup

def get_stock_list(html_file):
    """Parses the HTML file to get the list of stocks."""
    if not os.path.exists(html_file):
        raise FileNotFoundError(f"{html_file} not found.")
        
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    # Try to find table, otherwise look for rows directly
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')
    else:
        rows = soup.find_all('tr')
        
    if not rows:
        raise ValueError("No rows found in HTML file.")
        
    # Skip header row(s) - usually the first one or two
    # The file seems to have a thead with one tr, so we skip it.
    # Let's verify if the first row is header.
    start_index = 1
    if rows[0].find('th'):
        start_index = 1
    
    stocks = []
    rows = rows[start_index:] 
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            # Code is in the link in the second column (index 1)
            link = cols[1].find('a')
            if link and 'stock_code=' in link.get('href', ''):
                href = link.get('href')
                code = href.split('stock_code=')[1].split('&')[0] # Handle potential extra params
                name = link.text.strip()
                
                ticker = f"{code}.KL"
                stocks.append({
                    "Code": code,
                    "Name": name,
                    "Ticker": ticker,
                    "Sector": "N/A" # Sector info not readily available in this table
                })
    return stocks

def download_and_process_data(stocks, start_date, end_date):
    """Downloads data for all stocks and processes it."""
    tickers = [s['Ticker'] for s in stocks]
    tickers.append('^KLSE') # Add Benchmark
    
    print(f"Downloading and analyzing data for {len(tickers)} tickers... (This may take a minute)")
    
    # Download Close prices
    # Use auto_adjust=False to get 'Adj Close' if possible
    data = yf.download(tickers, start=start_date, progress=True, auto_adjust=False, group_by='ticker')
    
    klse_data = None
    processed_stocks = []
    
    for s in stocks:
        t = s['Ticker']
        try:
            # Extract data for this ticker
            if len(tickers) == 1:
                df = data
            else:
                df = data[t]
                
            # Check if empty
            if df.empty:
                continue
                
            # Get Adj Close
            if 'Adj Close' in df.columns:
                series = df['Adj Close']
            elif 'Close' in df.columns:
                series = df['Close']
            else:
                continue
                
            # Drop NaNs
            series = series.dropna()
            
            if series.empty:
                continue
                
            # Calculate Daily Returns
            daily_returns = series.pct_change().dropna()
            
            # Basic Stats
            avg_daily_ret = daily_returns.mean()
            std_dev = daily_returns.std()
            
            # Check Data Length (approx 252 trading days per year)
            days_count = len(series)
            years_count = days_count / 252.0
            
            s['Has_6Y_Data'] = years_count >= 6.0
            s['Avg_Return'] = avg_daily_ret if not np.isnan(avg_daily_ret) else 0.0
            s['Std_Dev'] = std_dev if not np.isnan(std_dev) else 0.0
            
            # Store series for later use (e.g. optimization)
            s['Series'] = series
            s['Daily_Returns'] = daily_returns
            
            # Calculate Performance Metrics for Display
            last_price = series.iloc[-1]
            s['Last_Price'] = last_price
            
            # 1 Year Return
            try:
                one_year_ago_date = series.index[-1] - datetime.timedelta(days=365)
                # Find nearest index
                if series.index[0] <= pd.Timestamp(one_year_ago_date):
                    idx = series.index.get_indexer([one_year_ago_date], method='nearest')[0]
                    if idx >= 0 and idx < len(series):
                        price_1y = series.iloc[idx]
                        one_y_ret = (last_price - price_1y) / price_1y
                        s['1Y_Return'] = one_y_ret * 100 # Store as percentage
                    else:
                        s['1Y_Return'] = None
                else:
                    s['1Y_Return'] = None
            except:
                s['1Y_Return'] = None

            processed_stocks.append(s)
            
        except Exception as e:
            print(f"Error processing {t}: {e}")
            pass
            
    # Process KLSE separately
    try:
        if len(tickers) == 1:
            df_klse = data
        else:
            df_klse = data['^KLSE']
            
        if not df_klse.empty:
            if 'Adj Close' in df_klse.columns:
                k_series = df_klse['Adj Close'].dropna()
            else:
                k_series = df_klse['Close'].dropna()
                
            if not k_series.empty:
                last_price = k_series.iloc[-1]
                
                # 1Y Return
                one_year_ago = k_series.index[-1] - datetime.timedelta(days=365)
                idx = k_series.index.get_indexer([one_year_ago], method='nearest')[0]
                price_1y = k_series.iloc[idx]
                ret_1y = (last_price - price_1y) / price_1y
                
                klse_data = {
                    'Last_Price': last_price,
                    '1Y_Return': ret_1y * 100
                }
    except Exception as e:
        print(f"Error processing KLSE: {e}")
        
    return processed_stocks, klse_data

def prepare_optimization_data(stocks, top_n=50):
    """Selects top stocks and prepares DataFrame for optimization."""
    # Filter for 6Y data
    valid_stocks = [s for s in stocks if s.get('Has_6Y_Data', False)]
    
    # Sort by Avg Return
    valid_stocks.sort(key=lambda x: x['Avg_Return'], reverse=True)
    
    # Top N
    top_stocks = valid_stocks[:top_n]
    
    # Create DataFrame of Adj Close
    data = {}
    for s in top_stocks:
        data[s['Ticker']] = s['Series']
        
    df_prices = pd.DataFrame(data)
    
    # Forward fill then drop remaining NaNs
    df_prices = df_prices.ffill().dropna()
    
    return top_stocks, df_prices
