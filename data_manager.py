import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import os
from bs4 import BeautifulSoup

def get_stock_list_from_html(html_file, market_name="ACE"):
    """Parses the HTML file to get the list of stocks."""
    if not os.path.exists(html_file):
        print(f"Warning: {html_file} not found.")
        return []
        
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    # Try to find table, otherwise look for rows directly
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')
    else:
        rows = soup.find_all('tr')
        
    if not rows:
        return []
        
    # Skip header row(s)
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
                    "Sector": "N/A",
                    "Market": market_name
                })
    return stocks

def get_stock_list_from_csv(csv_file, market_name="Main"):
    """Reads stock list from CSV."""
    if not os.path.exists(csv_file):
        print(f"Warning: {csv_file} not found.")
        return []
    
    try:
        df = pd.read_csv(csv_file)
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                "Code": str(row['Code']),
                "Name": row['Name'],
                "Ticker": row['Ticker'],
                "Sector": row.get('Sector', 'N/A'),
                "Market": market_name
            })
        return stocks
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return []

def get_bond_yield_data(csv_file):
    """Reads historical bond yield data from CSV."""
    if not os.path.exists(csv_file):
        print(f"Warning: {csv_file} not found. Using default risk-free rate.")
        return None
        
    try:
        # Try reading with parse_dates first
        df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date')
        df.sort_index(inplace=True)
        
        # 'Price' column contains the yield in percent (e.g., 3.473)
        # We need it as a decimal (0.03473)
        if 'Price' in df.columns:
            # Check if Price is string and clean it if necessary
            if df['Price'].dtype == object:
                 df['Price'] = df['Price'].astype(str).str.replace(',', '').astype(float)
            
            series = df['Price'] / 100.0
            return series
        else:
            print("Column 'Price' not found in bond yield CSV.")
            return None
    except Exception as e:
        print(f"Error reading bond yield CSV: {e}")
        return None

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
            s['Has_5Y_Data'] = years_count >= 5.0
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
                
                klci_data = {
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

def load_data_from_local_datasets(datasets_dir="datasets"):
    """Loads data from local CSV datasets instead of downloading."""
    print(f"Loading data from {datasets_dir}...")
    
    # 1. Load Companies (All)
    ace_comp = pd.read_csv(os.path.join(datasets_dir, "dataset_ace_companies.csv"))
    main_comp = pd.read_csv(os.path.join(datasets_dir, "dataset_main_companies.csv"))
    all_companies = pd.concat([ace_comp, main_comp], ignore_index=True)
    
    # 2. Load Qualified Tickers
    ace_cleaned = pd.read_csv(os.path.join(datasets_dir, "dataset_ace_cleaned_companies.csv"))
    main_cleaned = pd.read_csv(os.path.join(datasets_dir, "dataset_main_cleaned_companies.csv"))
    qualified_tickers = set(ace_cleaned['Ticker'].astype(str)) | set(main_cleaned['Ticker'].astype(str))
    
    # 3. Load Prices
    print("Loading price data...")
    ace_prices = pd.read_csv(os.path.join(datasets_dir, "dataset_ace_prices_wide.csv"), index_col=0, parse_dates=True)
    main_prices = pd.read_csv(os.path.join(datasets_dir, "dataset_main_prices_wide.csv"), index_col=0, parse_dates=True)
    # Combine prices (aligning columns/index)
    all_prices = pd.concat([ace_prices, main_prices], axis=1)
    
    processed_stocks = []
    
    print(f"Processing {len(all_companies)} companies...")
    
    for _, row in all_companies.iterrows():
        ticker = str(row['Ticker'])
        
        s = row.to_dict()
        s['Qualified'] = ticker in qualified_tickers
        
        if ticker in all_prices.columns:
            series = all_prices[ticker].dropna()
            
            if not series.empty:
                # Calculate Metrics
                daily_returns = series.pct_change().dropna()
                avg_daily_ret = daily_returns.mean()
                std_dev = daily_returns.std()
                last_price = series.iloc[-1]
                
                # 1Y Return
                try:
                    one_year_ago = series.index[-1] - datetime.timedelta(days=365)
                    idx = series.index.get_indexer([one_year_ago], method='nearest')[0]
                    price_1y = series.iloc[idx]
                    one_y_ret = (last_price - price_1y) / price_1y
                    s['1Y_Return'] = one_y_ret * 100
                except:
                    s['1Y_Return'] = None
                
                s['Avg_Return'] = avg_daily_ret if not np.isnan(avg_daily_ret) else 0.0
                s['Std_Dev'] = std_dev if not np.isnan(std_dev) else 0.0
                s['Last_Price'] = last_price
                s['Series'] = series
                s['Daily_Returns'] = daily_returns
                
                processed_stocks.append(s)
    
    # 4. Load KLCI
    klci_data = None
    try:
        # KLCI CSV might have multi-level headers from yfinance
        # Read without header first to inspect or just skip known bad rows
        # The file content shows:
        # Line 1: Price,Adj Close...
        # Line 2: Ticker,^KLSE...
        # Line 3: Date,,,,,,
        # Line 4: 2018-01-02...
        
        # We can try reading with header=0, then dropping rows where index is not a date
        klci_df = pd.read_csv(os.path.join(datasets_dir, "dataset_klci.csv"))
        
        # Rename first column to Date if it's not
        if 'Date' not in klci_df.columns:
             klci_df.rename(columns={klci_df.columns[0]: 'Date'}, inplace=True)
        
        # Drop rows where 'Date' is 'Ticker' or 'Date' or NaN
        klci_df = klci_df[pd.to_numeric(klci_df['Date'].str[0], errors='coerce').notnull()]
        
        # Now parse dates
        klci_df['Date'] = pd.to_datetime(klci_df['Date'])
        klci_df.set_index('Date', inplace=True)
        
        if not klci_df.empty:
            # The columns might be 'Adj Close' or just 'Adj Close' depending on how it was read
            # If header was 0, columns are 'Adj Close', 'Close' etc.
            # But if there were multiple header rows, we might have issues.
            # Let's just look for a column that contains 'Close'
            
            target_col = None
            for col in klci_df.columns:
                if 'Adj Close' in str(col):
                    target_col = col
                    break
            if not target_col:
                for col in klci_df.columns:
                    if 'Close' in str(col):
                        target_col = col
                        break
            
            if target_col:
                # Ensure numeric
                k_series = pd.to_numeric(klci_df[target_col], errors='coerce').dropna()
            
                if not k_series.empty:
                    last_price = k_series.iloc[-1]
                    one_year_ago = k_series.index[-1] - datetime.timedelta(days=365)
                    # Use get_indexer with method='nearest'
                    idx = k_series.index.get_indexer([one_year_ago], method='nearest')[0]
                    price_1y = k_series.iloc[idx]
                    ret_1y = (last_price - price_1y) / price_1y
                    
                    klci_data = {
                        'Last_Price': last_price,
                        '1Y_Return': ret_1y * 100
                    }
    except Exception as e:
        print(f"Error loading KLCI: {e}")

    return processed_stocks, klci_data
