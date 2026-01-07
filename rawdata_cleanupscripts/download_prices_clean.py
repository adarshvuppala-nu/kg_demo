import yfinance as yf
import pandas as pd
import numpy as np

symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "NVDA", "TSLA", "JPM", "UNH", "BRK-B"]

all_rows = []

for sym in symbols:
    print(f"Downloading {sym}...")
    df = yf.download(sym, start="2010-01-01", progress=False, auto_adjust=False)
    
    # Reset index to get Date as column
    df = df.reset_index()
    
    # Handle multi-index columns if present (yfinance sometimes returns this)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    
    # Add symbol column
    df["symbol"] = sym
    
    # Rename columns explicitly
    df = df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    
    # Select only required columns in exact order
    required_cols = ["date", "open", "high", "low", "close", "adj_close", "volume", "symbol"]
    
    # Handle missing adj_close column (some symbols might not have it)
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]  # Use close as fallback
    
    # Select and reorder columns
    df = df[required_cols]
    
    # Convert volume to integer (handle NaN by filling with 0)
    df["volume"] = df["volume"].fillna(0).astype(int)
    
    # Remove rows with NaN in critical columns (date, symbol, close)
    df = df.dropna(subset=["date", "symbol", "close"])
    
    # Fill remaining numeric NaNs with 0 (shouldn't happen, but safety)
    numeric_cols = ["open", "high", "low", "close", "adj_close"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    all_rows.append(df)

# Concatenate all symbols
final = pd.concat(all_rows, ignore_index=True)

# Ensure date is datetime and sort
final["date"] = pd.to_datetime(final["date"])
final = final.sort_values(["symbol", "date"])

# Write to CSV
final.to_csv("stock_prices_pg.csv", index=False)

print(f"\n✓ Total rows: {len(final)}")
print(f"✓ Columns: {list(final.columns)}")
print(f"✓ Date range: {final['date'].min()} to {final['date'].max()}")
print(f"\nFirst 5 rows:")
print(final.head())
print(f"\n✓ File saved: stock_prices_pg.csv")
