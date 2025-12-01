import os
import datetime
import numpy as np

def generate_navbar(active_tab='dashboard'):
    """Generates the navigation bar HTML."""
    return f"""
    <nav class="navbar">
        <div class="nav-container">
            <a href="#" class="nav-logo" onclick="switchTab('dashboard')">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 3v18h18"/><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/>
                </svg>
                RBA Robo-Advisor
            </a>
            <div class="nav-links">
                <a href="javascript:void(0)" class="nav-item {'active' if active_tab=='dashboard' else ''}" onclick="switchTab('dashboard')" id="nav-dashboard">Dashboard</a>
                <a href="javascript:void(0)" class="nav-item {'active' if active_tab=='guide' else ''}" onclick="switchTab('guide')" id="nav-guide">Learning Guide</a>
                <a href="javascript:void(0)" class="nav-item {'active' if active_tab=='optimization' else ''}" onclick="switchTab('optimization')" id="nav-optimization">Optimization</a>
                <a href="javascript:void(0)" class="nav-item {'active' if active_tab=='market' else ''}" onclick="switchTab('market')" id="nav-market">Market Data</a>
            </div>
        </div>
    </nav>
    """

def generate_guide_content():
    """Generates the educational guide content."""
    return """
    <div class="guide-container" style="max-width: 900px; margin: 0 auto;">
        <div class="guide-header">
            <h2>Assignment Learning Guide</h2>
            <p>Understanding the "Why" and "How" of Robo-Advisory Portfolio Optimization.</p>
        </div>

        <div class="guide-section">
            <h3>1. Stock Selection</h3>
            <div class="guide-block">
                <h4>Why?</h4>
                <p>We cannot optimize a portfolio with illiquid or young stocks. The assignment requires stocks with at least <strong>6 years of history</strong> to ensure we have enough data points for statistical significance. We also filter for <strong>high average returns</strong> to improve the chances of finding a profitable portfolio.</p>
                <h4>How?</h4>
                <pre><code># Filter for 6 years of data
years_count = len(prices) / 252.0
if years_count >= 6.0:
    keep_stock()

# Sort by Return
stocks.sort(key=lambda x: x['Avg_Return'], reverse=True)
top_50 = stocks[:50]</code></pre>
            </div>
        </div>

        <div class="guide-section">
            <h3>2. Returns & Volatility</h3>
            <div class="guide-block">
                <h4>Why?</h4>
                <p><strong>Return</strong> tells us how much money we make. <strong>Volatility</strong> (Standard Deviation) tells us how risky the stock is (how much the price swings). In Modern Portfolio Theory, we assume investors are risk-averse: they want maximum return for minimum risk.</p>
                <h4>How?</h4>
                <pre><code># Daily Return
daily_return = (price_today - price_yesterday) / price_yesterday

# Volatility (Standard Deviation)
volatility = std_dev(daily_returns) * sqrt(252) # Annualized</code></pre>
            </div>
        </div>

        <div class="guide-section">
            <h3>3. Sharpe Ratio</h3>
            <div class="guide-block">
                <h4>Why?</h4>
                <p>The <strong>Sharpe Ratio</strong> is the gold standard for comparing portfolios. It measures "Return per unit of Risk". A higher Sharpe Ratio means you are getting more reward for the same amount of risk. The assignment requires a Sharpe Ratio > 2.0.</p>
                <h4>How?</h4>
                <pre><code>Sharpe = (Portfolio_Return - Risk_Free_Rate) / Portfolio_Volatility</code></pre>
            </div>
        </div>

        <div class="guide-section">
            <h3>4. Value at Risk (VaR)</h3>
            <div class="guide-block">
                <h4>Why?</h4>
                <p><strong>VaR</strong> answers the question: "What is my worst-case loss on a bad day?". A 95% Daily VaR of -1.5% means: "We are 95% confident that the portfolio will not lose more than 1.5% in a single day."</p>
                <h4>How?</h4>
                <pre><code>VaR = Mean_Return - (1.645 * Daily_Volatility)</code></pre>
            </div>
        </div>
        
        <div class="guide-section">
            <h3>5. Mean-Variance Optimization (MVO)</h3>
            <div class="guide-block">
                <h4>Why?</h4>
                <p>MVO is an algorithm that finds the "Efficient Frontier". It mathematically calculates the exact combination of weights (e.g., 10% Stock A, 20% Stock B) that gives the highest possible Sharpe Ratio.</p>
                <h4>How?</h4>
                <p>We use Python's <code>scipy.optimize</code> library to minimize the <em>Negative</em> Sharpe Ratio (which is the same as maximizing the Positive Sharpe Ratio).</p>
            </div>
        </div>
    </div>
    """

def generate_scenario_html(name, weights, mean_returns, cov_matrix, ret, vol, sharpe, var, tickers, stocks_info):
    """Generates a detail page for a specific scenario."""
    
    # Create rows for the table
    rows = ""
    sorted_indices = np.argsort(weights)[::-1] # Descending
    
    for i in sorted_indices:
        w = weights[i]
        if w > 0.0001: # Show if weight > 0.01%
            ticker = tickers[i]
            # Find name
            stock_name = "Unknown"
            for s in stocks_info:
                if s['Ticker'] == ticker:
                    stock_name = s['Name']
                    break
            
            rows += f"<tr><td>{ticker}</td><td>{stock_name}</td><td class='num'>{w*100:.2f}%</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scenario Details: {name}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #1e293b; padding: 40px; margin: 0; padding-top: 80px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            h1 {{ margin-top: 0; color: #0f172a; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
            .metric-card {{ background: #f1f5f9; padding: 20px; border-radius: 8px; text-align: center; }}
            .metric-val {{ font-size: 24px; font-weight: 700; color: #2563eb; }}
            .metric-label {{ font-size: 14px; color: #64748b; margin-top: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            th {{ background: #f8fafc; font-weight: 600; }}
            .num {{ text-align: right; font-family: monospace; }}
            .back-link {{ display: inline-block; margin-bottom: 20px; color: #2563eb; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
            .math-box {{ background: #fffbeb; border: 1px solid #fcd34d; padding: 20px; border-radius: 8px; margin-top: 40px; }}
            .math-title {{ font-weight: 600; color: #92400e; margin-bottom: 10px; }}
            code {{ background: #fff; padding: 2px 6px; border-radius: 4px; border: 1px solid #e2e8f0; font-family: monospace; }}
            
            /* Navbar Styles for Detail Page */
            .navbar {{ position: fixed; top: 0; left: 0; width: 100%; height: 60px; background: white; border-bottom: 1px solid #e2e8f0; z-index: 1000; display: flex; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
            .nav-container {{ width: 100%; max-width: 1400px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }}
            .nav-logo {{ font-size: 18px; font-weight: 700; color: #2563eb; text-decoration: none; display: flex; align-items: center; gap: 8px; }}
            .nav-links {{ display: flex; gap: 24px; }}
            .nav-item {{ font-size: 14px; font-weight: 500; color: #64748b; text-decoration: none; transition: color 0.2s; }}
            .nav-item:hover {{ color: #2563eb; }}
            .nav-item.active {{ color: #2563eb; font-weight: 600; }}
        </style>
    </head>
    <body>
        <!-- Navbar -->
        <nav class="navbar">
            <div class="nav-container">
                <a href="../index.html" class="nav-logo">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 3v18h18"/><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/>
                    </svg>
                    RBA Robo-Advisor
                </a>
                <div class="nav-links">
                    <a href="../index.html#dashboard" class="nav-item">Dashboard</a>
                    <a href="../index.html#guide" class="nav-item">Learning Guide</a>
                    <a href="../index.html#optimization" class="nav-item active">Optimization</a>
                    <a href="../index.html#market" class="nav-item">Market Data</a>
                </div>
            </div>
        </nav>
        
        <div class="container">
            <a href="../index.html#optimization" class="back-link">&larr; Back to Optimization</a>
            <h1>Scenario: {name}</h1>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-val">{ret*100:.2f}%</div>
                    <div class="metric-label">Annual Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">{vol*100:.2f}%</div>
                    <div class="metric-label">Volatility</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">{sharpe:.2f}</div>
                    <div class="metric-label">Sharpe Ratio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">{var*100:.2f}%</div>
                    <div class="metric-label">Daily VaR (95%)</div>
                </div>
            </div>
            
            <h2>Portfolio Composition</h2>
            <p>Allocated across {len([w for w in weights if w > 0.0001])} assets.</p>
            <table>
                <thead><tr><th>Ticker</th><th>Company Name</th><th class="num">Weight</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            
            <div class="math-box">
                <div class="math-title">How was this calculated?</div>
                <p><strong>Optimization Objective:</strong> Maximize Sharpe Ratio = (Portfolio Return - Risk Free Rate) / Portfolio Volatility</p>
                <p><strong>Portfolio Return ($R_p$):</strong> Sum of (Weight * Asset Return) for all assets.<br>
                <code>R_p = w₁r₁ + w₂r₂ + ... + wₙrₙ</code></p>
                <p><strong>Portfolio Volatility ($\sigma_p$):</strong> Calculated using the Covariance Matrix ($\Sigma$) to account for correlations between stocks.<br>
                <code>σ_p = √(wᵀ Σ w)</code></p>
                <p><strong>Value at Risk (VaR):</strong> The maximum expected loss over one day with 95% confidence.<br>
                <code>VaR = (Daily Return) - (1.645 * Daily Volatility)</code></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save file
    filename = f"scenario_{name.lower().replace(' ', '_').replace('%', '')}.html"
    filepath = os.path.join("details", filename)
    if not os.path.exists("details"):
        os.makedirs("details")
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
        
    return f"details/{filename}"

def generate_main_html(stocks, market_metrics, optimization_results, table_rows):
    """Generates the main dashboard HTML."""
    
    navbar = generate_navbar()
    guide_content = generate_guide_content()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ACE Market Stock Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="style.css">
    </head>
    <body>
        {navbar}

        <div class="dashboard">
            <div class="header">
                <div>
                    <h1>ACE Market Stock Dashboard</h1>
                    <div class="date">Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button onclick="downloadCSV()" class="btn-action" style="font-size: 14px; padding: 8px 16px; display: flex; align-items: center; gap: 6px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                        Export to Excel
                    </button>
                </div>
            </div>

            <!-- TAB 1: DASHBOARD -->
            <div id="tab-dashboard" class="tab-content active">
                <!-- Summary Cards -->
                <div class="summary-grid">
                    <div class="card">
                        <div class="card-title">Market Overview</div>
                        <div class="card-value">{market_metrics['return_str']}</div>
                        <div class="card-sub {market_metrics['color']}">
                            {market_metrics['arrow']} KLCI Benchmark (1Y)
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-title">Top Performer (1Y)</div>
                        <div class="card-value">{market_metrics['top_ticker']}</div>
                        <div class="card-sub text-green">
                            +{market_metrics['top_return']:.2f}% Return
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-title">Average Daily Return</div>
                        <div class="card-value">{market_metrics['avg_daily']:.4f}%</div>
                        <div class="card-sub text-muted">
                            Across {len(stocks)} stocks
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-title">Data Coverage</div>
                        <div class="card-value">{market_metrics['coverage']}</div>
                        <div class="card-sub text-muted">
                            Stocks with full 6Y history
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 40px; text-align: center; padding: 40px; background: white; border-radius: 12px; border: 1px solid #e2e8f0;">
                    <h2 style="margin-top: 0;">Welcome to the RBA Robo-Advisor</h2>
                    <p style="color: #64748b; max-width: 600px; margin: 10px auto 30px;">
                        Analyze 50 ACE Market stocks, optimize portfolios using Mean-Variance analysis, and explore detailed market data.
                    </p>
                    <div style="display: flex; justify-content: center; gap: 20px;">
                        <button onclick="switchTab('guide')" class="btn-action" style="padding: 12px 24px; font-size: 16px; background: #fffbeb; color: #92400e; border: 1px solid #fcd34d;">Start Learning Guide</button>
                        <button onclick="switchTab('optimization')" class="btn-action" style="padding: 12px 24px; font-size: 16px;">Go to Optimization</button>
                    </div>
                </div>
            </div>
            
            <!-- TAB 2: LEARNING GUIDE -->
            <div id="tab-guide" class="tab-content">
                {guide_content}
            </div>

            <!-- TAB 3: OPTIMIZATION -->
            <div id="tab-optimization" class="tab-content">
                <div class="summary-grid" style="grid-template-columns: 1fr; margin-bottom: 30px;">
                    <div class="card">
                        <div class="card-title">Portfolio Optimization Scenarios (Top 50 Stocks)</div>
                        <div class="card-sub text-muted">Objective: Maximize Sharpe Ratio | Constraints: VaR >= -1.5%</div>
                        <div style="margin-top: 20px; overflow-x: auto;">
                            {optimization_results}
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 4: MARKET DATA -->
            <div id="tab-market" class="tab-content">
                <!-- Controls -->
                <div class="controls-bar">
                    <div class="search-wrapper">
                        <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search by code or name...">
                    </div>
                    <div style="width: 200px;">
                        <select id="dataFilter" onchange="filterTable()">
                            <option value="all">Show All Stocks</option>
                            <option value="target">Target (>6Y Data & High Return)</option>
                            <option value="qualified">Qualified (>6Y Data)</option>
                            <option value="has_5y">Has 5Y Data</option>
                            <option value="unqualified">Unqualified (< 5Y Data)</option>
                        </select>
                    </div>
                    
                    <div class="view-options">
                        <button class="view-btn" onclick="toggleViewMenu()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                            </svg>
                            View Options
                        </button>
                        <div id="viewMenu" class="view-menu">
                            <div class="view-item" onclick="toggleColumnGroup('col-live')">
                                <input type="checkbox" checked id="chk-live"> Live Data
                            </div>
                            <div class="view-item" onclick="toggleColumnGroup('col-perf')">
                                <input type="checkbox" checked id="chk-perf"> Performance
                            </div>
                            <div class="view-item" onclick="toggleColumnGroup('col-status')">
                                <input type="checkbox" checked id="chk-status"> Status
                            </div>
                        </div>
                    </div>
                    <span id="resultCount" style="margin-left: auto; font-size: 14px; color: #64748b;"></span>
                </div>

                <div class="table-container">
                    <div class="table-responsive">
                        <table id="stockTable">
                            <thead>
                                <tr style="background: #f8fafc; border-bottom: 1px solid var(--border-color);">
                                    <th colspan="2">Company Identity</th>
                                    <th colspan="3" class="col-live">Live Data</th>
                                    <th colspan="4" class="col-perf">Performance</th>
                                    <th colspan="2" class="col-status">Status</th>
                                </tr>
                                <tr>
                                    <th onclick="sortTable(0)">Code</th>
                                    <th onclick="sortTable(1)">Company Name</th>
                                    <th class="num col-live" onclick="sortTable(2)">Last Price</th>
                                    <th class="num col-live" onclick="sortTable(3)">Change</th>
                                    <th class="num col-live" onclick="sortTable(4)">% Change</th>
                                    <th class="num col-perf" onclick="sortTable(5)">Avg Daily Return</th>
                                    <th class="num col-perf" onclick="sortTable(6)">Std Dev</th>
                                    <th class="num col-perf" onclick="sortTable(7)">1Y Return</th>
                                    <th class="num col-perf" onclick="sortTable(8)">Sharpe (Est)</th>
                                    <th class="col-status" onclick="sortTable(9)">Data Status</th>
                                    <th class="col-status">Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function toggleViewMenu() {{
                var menu = document.getElementById('viewMenu');
                if (menu.style.display === 'block') {{
                    menu.style.display = 'none';
                }} else {{
                    menu.style.display = 'block';
                }}
            }}

            // Close menu when clicking outside
            window.onclick = function(event) {{
                if (!event.target.matches('.view-btn') && !event.target.closest('.view-btn') && !event.target.closest('.view-menu')) {{
                    var menu = document.getElementById('viewMenu');
                    if (menu && menu.style.display === 'block') {{
                        menu.style.display = 'none';
                    }}
                }}
            }}

            function toggleColumnGroup(className) {{
                var cells = document.getElementsByClassName(className);
                var checkboxId = 'chk-' + className.replace('col-', '');
                var isChecked = document.getElementById(checkboxId).checked;
                
                for (var i = 0; i < cells.length; i++) {{
                    if (isChecked) {{
                        if (cells[i].tagName === 'TH' || cells[i].tagName === 'TD') {{
                            cells[i].style.display = '';
                        }}
                    }} else {{
                        cells[i].style.display = 'none';
                    }}
                }}
            }}

            function switchTab(tabId) {{
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                
                // Show selected tab
                const selectedTab = document.getElementById('tab-' + tabId);
                if (selectedTab) {{
                    selectedTab.classList.add('active');
                }}
                
                // Update nav links
                document.querySelectorAll('.nav-item').forEach(link => {{
                    link.classList.remove('active');
                }});
                const activeLink = document.getElementById('nav-' + tabId);
                if (activeLink) {{
                    activeLink.classList.add('active');
                }}
                
                // Update URL hash without scrolling
                history.pushState(null, null, '#' + tabId);
            }}
            
            // Check hash on load
            window.onload = function() {{
                const hash = window.location.hash.replace('#', '');
                if (hash && (hash === 'dashboard' || hash === 'optimization' || hash === 'market' || hash === 'guide')) {{
                    switchTab(hash);
                }}
                filterTable(); // Initialize count
            }};

            function filterTable() {{
                const searchInput = document.getElementById('searchInput').value.toUpperCase();
                const filterValue = document.getElementById('dataFilter').value;
                const table = document.getElementById("stockTable");
                const tr = table.getElementsByTagName("tr");
                let visibleCount = 0;

                // Start from index 2 to skip the two header rows
                for (let i = 2; i < tr.length; i++) {{
                    const tdCode = tr[i].getElementsByTagName("td")[0];
                    const tdName = tr[i].getElementsByTagName("td")[1];
                    
                    if (tdCode && tdName) {{
                        const txtCode = tdCode.textContent || tdCode.innerText;
                        const txtName = tdName.textContent || tdName.innerText;
                        const matchSearch = txtCode.toUpperCase().indexOf(searchInput) > -1 || txtName.toUpperCase().indexOf(searchInput) > -1;
                        
                        let matchFilter = true;
                        const isTarget = tr[i].getAttribute("data-target") === "true";
                        const isQualified = tr[i].getAttribute("data-qualified") === "true";
                        const has5y = tr[i].getAttribute("data-has5y") === "true";
                        
                        if (filterValue === "target") matchFilter = isTarget;
                        else if (filterValue === "qualified") matchFilter = isQualified;
                        else if (filterValue === "has_5y") matchFilter = has5y;
                        else if (filterValue === "unqualified") matchFilter = !has5y;

                        if (matchSearch && matchFilter) {{
                            tr[i].style.display = "";
                            visibleCount++;
                        }} else {{
                            tr[i].style.display = "none";
                        }}
                    }}
                }}
                document.getElementById('resultCount').innerText = "Showing " + visibleCount + " results";
            }}
            
            function sortTable(n) {{
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("stockTable");
                switching = true;
                dir = "asc";
                
                while (switching) {{
                    switching = false;
                    rows = table.rows;
                    // Start loop from 2 to skip header rows
                    for (i = 2; i < (rows.length - 1); i++) {{
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        
                        var xVal = x.innerHTML.toLowerCase();
                        var yVal = y.innerHTML.toLowerCase();
                        
                        // Check if numeric
                        var xNum = parseFloat(xVal.replace(/[^0-9.-]+/g,""));
                        var yNum = parseFloat(yVal.replace(/[^0-9.-]+/g,""));
                        
                        if (!isNaN(xNum) && !isNaN(yNum)) {{
                            if (dir == "asc") {{
                                if (xNum > yNum) {{ shouldSwitch = true; break; }}
                            }} else {{
                                if (xNum < yNum) {{ shouldSwitch = true; break; }}
                            }}
                        }} else {{
                            if (dir == "asc") {{
                                if (xVal > yVal) {{ shouldSwitch = true; break; }}
                            }} else {{
                                if (xVal < yVal) {{ shouldSwitch = true; break; }}
                            }}
                        }}
                    }}
                    if (shouldSwitch) {{
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount ++;
                    }} else {{
                        if (switchcount == 0 && dir == "asc") {{
                            dir = "desc";
                            switching = true;
                        }}
                    }}
                }}
            }}

            function downloadCSV() {{
                var csv = [];
                var rows = document.querySelectorAll("table tr");
                
                for (var i = 0; i < rows.length; i++) {{
                    var row = [], cols = rows[i].querySelectorAll("td, th");
                    
                    // Skip hidden rows
                    if (rows[i].style.display === 'none') continue;
                    
                    for (var j = 0; j < cols.length; j++) {{
                        // Clean text: remove newlines, extra spaces
                        var data = cols[j].innerText.replace(/(\\r\\n|\\n|\\r)/gm, "").trim();
                        // Escape double quotes
                        data = data.replace(/"/g, '""');
                        // Wrap in quotes
                        row.push('"' + data + '"');
                    }}
                    csv.push(row.join(","));
                }}

                var csvFile = new Blob([csv.join("\\n")], {{type: "text/csv"}});
                var downloadLink = document.createElement("a");
                downloadLink.download = "stock_summary.csv";
                downloadLink.href = window.URL.createObjectURL(csvFile);
                downloadLink.style.display = "none";
                document.body.appendChild(downloadLink);
                downloadLink.click();
            }}
        </script>
    </body>
    </html>
    """
    return html
