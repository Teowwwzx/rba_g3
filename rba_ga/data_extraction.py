from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import datetime
import os

# --- PART A: EXTRACT STOCK CODES FROM HTML ---
# Read the HTML file from the parent directory
file_path = '../ace_market_companies_list.html'
if not os.path.exists(file_path):
    # Fallback absolute path if running differently
    file_path = 'C:/Users/teowz/OneDrive/Documents/GitHub/rba_g2/ace_market_companies_list.html'

print(f"Reading HTML from: {file_path}")
with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')
stocks = []

# Find all rows in the table
rows = soup.find_all('tr')

for row in rows:
    # Find the link that contains 'stock_code='
    link = row.find('a', href=True)
    if link and 'stock_code=' in link['href']:
        # Extract 4-digit code (e.g., "0328")
        code = link['href'].split('stock_code=')[1].split('&')[0]
        name = link.text.strip()
        # Format for Yahoo Finance: Code + .KL
        stocks.append({'Name': name, 'Code': f"{code}.KL"})

df_stocks = pd.DataFrame(stocks)
print(f"Found {len(df_stocks)} stock codes. Example: {df_stocks['Code'][0]}")

# --- PART B: DOWNLOAD & FILTER (The "Robo" Logic) ---
print("\nStarting analysis... this may take a few minutes.")
valid_stocks = []

# Define Date Range (6 Years as per mandate)
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=365*6)

for index, row in df_stocks.iterrows():
    ticker = row['Code']
    name = row['Name']
    
    try:
        # Download data (quietly)
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        # Check 1: Must have data (not empty)
        if len(data) > 0:
            # Check 2: Calculate Average Daily Return
            # Formula: (Today - Yesterday) / Yesterday
            # Use 'Adj Close' if available, else 'Close'
            col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            
            # Handle MultiIndex columns in newer yfinance versions
            if isinstance(data.columns, pd.MultiIndex):
                try:
                    series = data[col]
                    if isinstance(series, pd.DataFrame): 
                        series = series.iloc[:, 0]
                except:
                     series = data.iloc[:, 0]
            else:
                series = data[col]

            daily_return = series.pct_change()
            
            # The mandate asks for "Average Daily Return" over 6 years
            # We calculate the mean of the daily % change
            avg_daily_return = daily_return.mean() * 100  # Convert to percentage
            
            # Store data if it exists
            valid_stocks.append({
                'Code': ticker,
                'Name': name,
                'Avg_Daily_Return_%': avg_daily_return,
                'Data_Points': len(data)
            })
            
    except Exception as e:
        # print(f"Could not process {ticker}: {e}")
        pass

# --- PART C: SELECT THE TOP 50 ---
df_results = pd.DataFrame(valid_stocks)

if not df_results.empty:
    # Filter: Apply the 0.25% threshold
    qualified_df = df_results[df_results['Avg_Daily_Return_%'] >= 0.25]

    # Sort by highest return first
    qualified_df = qualified_df.sort_values(by='Avg_Daily_Return_%', ascending=False)

    print("\n--- RESULTS ---")
    print(f"Total stocks analyzed: {len(df_results)}")
    print(f"Stocks meeting 0.25% requirement: {len(qualified_df)}")

    # Display top 5 to check
    print(qualified_df.head(5))

    # Save the best 50 (or all qualified) to CSV for the next step
    final_50 = qualified_df.head(50)
    final_50.to_csv('selected_50_stocks.csv', index=False)
    print("Saved top candidates to 'selected_50_stocks.csv'")
else:
    print("No valid stock data found.")
