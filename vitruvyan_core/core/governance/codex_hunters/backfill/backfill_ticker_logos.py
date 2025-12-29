#!/usr/bin/env python3
"""
TICKER LOGOS BACKFILL SCRIPT

Popola la colonna logo_url in PostgreSQL per tutti i 519 ticker.
Usa mappatura hardcoded + ClearBit fallback.

Usage: python3 scripts/backfill_ticker_logos.py
"""

# Legacy import - use PostgresAgent
# import psycopg2
from core.foundation.persistence.postgres_agent import PostgresAgent
import requests
from typing import Optional
import time

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vitruvyan',
    'user': 'vitruvyan_user',
    'password': '@Caravaggio971'
}

# Hardcoded domain mappings (80+ tickers)
DOMAIN_MAP = {
    'AAPL': 'apple.com',
    'MSFT': 'microsoft.com',
    'GOOGL': 'google.com',
    'GOOG': 'google.com',
    'AMZN': 'amazon.com',
    'TSLA': 'tesla.com',
    'META': 'meta.com',
    'FB': 'facebook.com',
    'NVDA': 'nvidia.com',
    'AMD': 'amd.com',
    'INTC': 'intel.com',
    'IBM': 'ibm.com',
    'ORCL': 'oracle.com',
    'NFLX': 'netflix.com',
    'DIS': 'disney.com',
    'BA': 'boeing.com',
    'GE': 'ge.com',
    'F': 'ford.com',
    'GM': 'gm.com',
    'AAL': 'aa.com',
    'UAL': 'united.com',
    'DAL': 'delta.com',
    'LUV': 'southwest.com',
    'SHOP': 'shopify.com',
    'SQ': 'squareup.com',
    'PYPL': 'paypal.com',
    'V': 'visa.com',
    'MA': 'mastercard.com',
    'JPM': 'jpmorganchase.com',
    'BAC': 'bankofamerica.com',
    'WFC': 'wellsfargo.com',
    'C': 'citigroup.com',
    'GS': 'goldmansachs.com',
    'MS': 'morganstanley.com',
    'BRK.B': 'berkshirehathaway.com',
    'BRK.A': 'berkshirehathaway.com',
    'JNJ': 'jnj.com',
    'PFE': 'pfizer.com',
    'MRNA': 'modernatx.com',
    'UNH': 'unitedhealthgroup.com',
    'CVS': 'cvshealth.com',
    'WMT': 'walmart.com',
    'TGT': 'target.com',
    'COST': 'costco.com',
    'HD': 'homedepot.com',
    'LOW': 'lowes.com',
    'MCD': 'mcdonalds.com',
    'SBUX': 'starbucks.com',
    'KO': 'coca-cola.com',
    'PEP': 'pepsico.com',
    'NKE': 'nike.com',
    'ADBE': 'adobe.com',
    'CRM': 'salesforce.com',
    'CSCO': 'cisco.com',
    'QCOM': 'qualcomm.com',
    'TXN': 'ti.com',
    'AVGO': 'broadcom.com',
    'NOW': 'servicenow.com',
    'SNOW': 'snowflake.com',
    'DDOG': 'datadoghq.com',
    'CRWD': 'crowdstrike.com',
    'ZS': 'zscaler.com',
    'PANW': 'paloaltonetworks.com',
    'TEAM': 'atlassian.com',
    'WDAY': 'workday.com',
    'DOCU': 'docusign.com',
    'ZM': 'zoom.us',
    'UBER': 'uber.com',
    'LYFT': 'lyft.com',
    'ABNB': 'airbnb.com',
    'COIN': 'coinbase.com',
    'ROKU': 'roku.com',
    'SPOT': 'spotify.com',
    'TWLO': 'twilio.com',
    'NET': 'cloudflare.com',
    'OKTA': 'okta.com',
    'PLTR': 'palantir.com',
    'U': 'unity.com',
    'RBLX': 'roblox.com',
}

def guess_domain(ticker: str, company_name: Optional[str]) -> str:
    """Guess company domain from ticker or name"""
    # Check hardcoded map first
    if ticker in DOMAIN_MAP:
        return DOMAIN_MAP[ticker]
    
    # Fallback: extract from company name
    if company_name:
        name = company_name.lower()
        # Remove common suffixes
        name = name.replace(' inc', '').replace(' corp', '').replace(' corporation', '')
        name = name.replace(' ltd', '').replace(' limited', '').replace(' group', '')
        name = name.replace(' holdings', '').replace(' co', '').replace(',', '')
        name = name.strip().split()[0]
        return f"{name}.com"
    
    # Last resort
    return f"{ticker.lower()}.com"

def test_logo_url(url: str, timeout: int = 3) -> bool:
    """Test if logo URL is accessible"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def get_logo_url(ticker: str, company_name: Optional[str]) -> Optional[str]:
    """Get logo URL for ticker"""
    # Try Yahoo Finance (primary source)
    yahoo_url = f"https://logo.yahoo.com/stocks/{ticker.lower()}"
    if test_logo_url(yahoo_url, timeout=2):
        return yahoo_url
    
    # Fallback to generic avatar (ALWAYS works)
    generic_url = f"https://ui-avatars.com/api/?name={ticker}&size=128&background=4A5568&color=fff&font-size=0.4&bold=true"
    return generic_url

def backfill_logos():
    """Main backfill function"""
    print("🚀 Starting ticker logos backfill...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all tickers without logo
    cur.execute("SELECT ticker, company_name FROM tickers WHERE logo_url IS NULL ORDER BY ticker")
    tickers = cur.fetchall()
    
    print(f"📊 Found {len(tickers)} tickers without logo")
    
    success = 0
    failed = 0
    
    for ticker, company_name in tickers:
        print(f"Processing {ticker}...", end=" ")
        
        logo_url = get_logo_url(ticker, company_name)
        
        if logo_url:
            cur.execute(
                "UPDATE tickers SET logo_url = %s WHERE ticker = %s",
                (logo_url, ticker)
            )
            conn.commit()
            print(f"✅ {logo_url}")
            success += 1
        else:
            print("❌ No logo found")
            failed += 1
        
        # Rate limiting
        time.sleep(0.1)
    
    cur.close()
    conn.close()
    
    print(f"\n✅ Backfill complete!")
    print(f"   Success: {success}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(tickers)}")

if __name__ == "__main__":
    backfill_logos()
