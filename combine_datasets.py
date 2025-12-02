import pandas as pd
import os

DATA_DIR = "datasets"
OUTPUT_DIR = "final_datasets"

def combine_market(market_name, companies_file, prices_file, output_prefix):
    print(f"--- Combining {market_name} ---")
    comp_path = os.path.join(DATA_DIR, companies_file)
    price_path = os.path.join(DATA_DIR, prices_file)
    
    if not os.path.exists(comp_path) or not os.path.exists(price_path):
        print(f"Error: Files missing for {market_name}")
        return

    # Load Data
    df_comp = pd.read_csv(comp_path)
    df_prices = pd.read_csv(price_path, index_col=0)
    
    # Ensure Output Directory Exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 1. Excel Output
    excel_file = os.path.join(OUTPUT_DIR, f"{output_prefix}_cleaned_combined.xlsx")
    try:
        with pd.ExcelWriter(excel_file) as writer:
            df_comp.to_excel(writer, sheet_name='Companies', index=False)
            df_prices.to_excel(writer, sheet_name='Prices')
        print(f"Saved Excel to {excel_file}")
    except Exception as e:
        print(f"Error saving Excel: {e}")

    # 2. Long CSV Output
    # Reset index to make Date a column
    df_prices_reset = df_prices.reset_index().rename(columns={'index': 'Date', 'Date': 'Date'})
    # Melt
    df_long = df_prices_reset.melt(id_vars=['Date'], var_name='Ticker', value_name='Price')
    
    # Merge with Company Name
    # Create a mapping dictionary for faster merge
    ticker_to_name = pd.Series(df_comp.Name.values, index=df_comp.Ticker).to_dict()
    df_long['Company_Name'] = df_long['Ticker'].map(ticker_to_name)
    
    # Reorder columns
    df_long = df_long[['Date', 'Ticker', 'Company_Name', 'Price']]
import pandas as pd
import os

DATA_DIR = "datasets"
OUTPUT_DIR = "final_datasets"

def combine_market(market_name, companies_file, prices_file, output_prefix):
    print(f"--- Combining {market_name} ---")
    comp_path = os.path.join(DATA_DIR, companies_file)
    
    # Modify price_path to look into an 'intermediate' subfolder within DATA_DIR
    intermediate_dir = os.path.join(DATA_DIR, "intermediate")
    price_path = os.path.join(intermediate_dir, prices_file)
    
    if not os.path.exists(comp_path) or not os.path.exists(price_path):
        print(f"Error: Files missing for {market_name}")
        print(f"Expected company file at: {comp_path}")
        print(f"Expected price file at: {price_path}")
        return

    # Load Data
    df_comp = pd.read_csv(comp_path)
    df_prices = pd.read_csv(price_path, index_col=0, parse_dates=True) # Added parse_dates=True as per the example in the instruction
    
    # Ensure Output Directory Exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 1. Excel Output
    excel_file = os.path.join(OUTPUT_DIR, f"{output_prefix}_cleaned_combined.xlsx")
    try:
        with pd.ExcelWriter(excel_file) as writer:
            df_comp.to_excel(writer, sheet_name='Companies', index=False)
            df_prices.to_excel(writer, sheet_name='Prices')
        print(f"Saved Excel to {excel_file}")
    except Exception as e:
        print(f"Error saving Excel: {e}")

    # 2. Long CSV Output
    # Reset index to make Date a column
    df_prices_reset = df_prices.reset_index().rename(columns={'index': 'Date', 'Date': 'Date'})
    # Melt
    df_long = df_prices_reset.melt(id_vars=['Date'], var_name='Ticker', value_name='Price')
    
    # Merge with Company Name
    # Create a mapping dictionary for faster merge
    ticker_to_name = pd.Series(df_comp.Name.values, index=df_comp.Ticker).to_dict()
    df_long['Company_Name'] = df_long['Ticker'].map(ticker_to_name)
    
    # Reorder columns
    df_long = df_long[['Date', 'Ticker', 'Company_Name', 'Price']]
    
    long_csv_file = os.path.join(OUTPUT_DIR, f"{output_prefix}_cleaned_long.csv")
    df_long.to_csv(long_csv_file, index=False)
    print(f"Saved Long CSV to {long_csv_file}")

def main():
    # ACE Market
    combine_market("ACE Market", "dataset_ace_cleaned_companies.csv", "dataset_ace_cleaned_prices.csv", "dataset_ace")
    
    # Main Market
    combine_market("Main Market", "dataset_main_cleaned_companies.csv", "dataset_main_cleaned_prices.csv", "dataset_main")

if __name__ == "__main__":
    main()
