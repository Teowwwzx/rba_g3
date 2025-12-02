import pandas as pd
import yfinance as yf
import data_manager
import os
import datetime

# Configuration
START_DATE = '2018-01-01'
END_DATE = '2025-12-31'
ACE_HTML = 'ace_market_companies_list.html'
MAIN_CSV = 'main_market_companies.csv'
BOND_CSV = 'Malaysia 10-Year Bond Yield Historical Data.csv'

def generate_market_dataset(market_name, stock_list, output_prefix):
    print(f"--- Generating {market_name} Dataset ---")
    
    # 1. Metadata
    print(f"Processing {len(stock_list)} companies...")
    df_meta = pd.DataFrame(stock_list)
    
    # 2. Download Prices
    tickers = [s['Ticker'] for s in stock_list]
    print(f"Downloading price data for {len(tickers)} tickers ({START_DATE} to {END_DATE})...")
    
    # Download in chunks to avoid overwhelming or timeouts if list is huge
    # But yfinance handles lists well usually.
    try:
        data = yf.download(tickers, start=START_DATE, end=END_DATE, group_by='ticker', auto_adjust=False, progress=True)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    # Process Data
    price_data = {}
    valid_tickers = []
    
    for s in stock_list:
        ticker = s['Ticker']
        try:
            if len(tickers) == 1:
                df = data
            else:
                if ticker not in data.columns.levels[0]:
                    continue
                df = data[ticker]
def process_bond_data():
    print("--- Processing Bond Data ---")
    if not os.path.exists(BOND_CSV):
        print(f"Error: {BOND_CSV} not found.")
        return

    try:
        df = pd.read_csv(BOND_CSV)
        # Expected format: "Date","Price",...
        # "12/01/2025"
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        # Clean Price
        if df['Price'].dtype == object:
             df['Price'] = df['Price'].astype(str).str.replace(',', '').astype(float)
             
        # Save
        output_file = "dataset_bond_yield.csv"
        df.to_csv(output_file)
        print(f"Saved bond data to {output_file}")
        
    except Exception as e:
        print(f"Error processing bond data: {e}")

def generate_klci_dataset():
    print("--- Generating KLCI Dataset ---")
    ticker = "^KLSE"
    try:
        data = yf.download(ticker, start=START_DATE, end=END_DATE, auto_adjust=False, progress=True)
        if not data.empty:
            output_file = "dataset_klci.csv"
            data.to_csv(output_file)
            print(f"Saved KLCI data to {output_file}")
        else:
            print("KLCI data is empty.")
    except Exception as e:
        print(f"Error downloading KLCI: {e}")

def main():
    # 1. ACE Market
    ace_stocks = data_manager.get_stock_list_from_html(ACE_HTML, market_name="ACE")
    generate_market_dataset("ACE Market", ace_stocks, "dataset_ace")
    
    # 2. Main Market
    main_stocks = data_manager.get_stock_list_from_csv(MAIN_CSV, market_name="Main")
    generate_market_dataset("Main Market", main_stocks, "dataset_main")
    
    # 3. Bond Data
    process_bond_data()
    
    # 4. KLCI Data
    generate_klci_dataset()
    
    print("\nAll datasets generated successfully.")

if __name__ == "__main__":
    main()
