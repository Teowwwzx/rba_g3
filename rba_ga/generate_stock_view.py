import pandas as pd
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
HTML_FILE = '../ace_market_companies_list.html'
OUTPUT_FILE = 'ace_market_stocks_view.csv'

def generate_stock_view():
    if not os.path.exists(HTML_FILE):
        # Fallback path
        html_path = 'C:/Users/teowz/OneDrive/Documents/GitHub/rba_g2/ace_market_companies_list.html'
    else:
        html_path = HTML_FILE
        
    print(f"Reading HTML from: {html_path}")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    stocks = []
    for row in soup.find_all('tr'):
        link = row.find('a', href=True)
        if link and 'stock_code=' in link['href']:
            code = link['href'].split('stock_code=')[1].split('&')[0]
            name = link.text.strip()
            stocks.append({'Stock Code': code, 'Company Name': name})
            
    df = pd.DataFrame(stocks)
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"Successfully generated '{OUTPUT_FILE}' with {len(df)} companies.")
    print(df.head())

if __name__ == "__main__":
    generate_stock_view()
