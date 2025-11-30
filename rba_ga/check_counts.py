from bs4 import BeautifulSoup
import pandas as pd

def check_counts():
    html_path = 'ace_market_summary.html'
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except FileNotFoundError:
        print(f"File not found: {html_path}")
        return

    # Find the table with id 'stockTable'
    table = soup.find('table', id='stockTable')
    if not table:
        print("Stock table not found")
        return

    rows = table.find('tbody').find_all('tr')
    stocks = []

    for r in rows:
        cols = r.find_all('td')
        if not cols or len(cols) < 7:
            continue
        
        # Column 3 (0-indexed) is Has 5Y Data
        # Column 6 is Avg Daily Return %
        
        # Check 5Y Data
        status_span = cols[3].find('span')
        has_5y = False
        if status_span and 'Yes' in status_span.text:
            has_5y = True
            
        # Check Return
        ret_text = cols[6].text.strip().replace('%', '')
        try:
            ret = float(ret_text)
        except:
            ret = 0.0
            
        stocks.append({'5Y': has_5y, 'Ret': ret})

    df = pd.DataFrame(stocks)
    
    print(f"Total Stocks Scanned: {len(df)}")
    print("-" * 30)
    print(f"Stocks with 5Y Data: {len(df[df['5Y']==True])}")
    print(f"Stocks with Avg Return >= 0.25%: {len(df[df['Ret']>=0.25])}")
    print("-" * 30)
    print("Combined Criteria (5Y Data AND Return >= X):")
    print(f"  >= 0.25%: {len(df[(df['5Y']==True) & (df['Ret']>=0.25)])}")
    print(f"  >= 0.20%: {len(df[(df['5Y']==True) & (df['Ret']>=0.20)])}")
    print(f"  >= 0.15%: {len(df[(df['5Y']==True) & (df['Ret']>=0.15)])}")
    print(f"  >= 0.10%: {len(df[(df['5Y']==True) & (df['Ret']>=0.10)])}")
    print(f"  >= 0.05%: {len(df[(df['5Y']==True) & (df['Ret']>=0.05)])}")
    print(f"  >  0.00%: {len(df[(df['5Y']==True) & (df['Ret']>0.0)])}")

if __name__ == "__main__":
    check_counts()
