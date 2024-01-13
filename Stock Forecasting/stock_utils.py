from pathlib import Path

import pandas as pd

def get_all_stock_symbols(stock_data_dir: Path):
    return [
        f.stem for f in stock_data_dir.glob("*") if f.is_dir()
    ]

def get_consolidated_stock_data(
    stock_symbol: str,
    stock_data_dir: Path
):
    hist_dfs = []
    file_pattern = f"*{stock_symbol}*.csv"

    for f in stock_data_dir.joinpath(stock_symbol).glob(file_pattern):
        hist_df = pd.read_csv(f, thousands = ',')
        hist_df.columns = [c.strip() for c in hist_df.columns]
        hist_df["Date"] = pd.to_datetime(hist_df["Date"])
        hist_dfs.append(hist_df)
    
    if len(hist_dfs) > 0:
        hist_df: pd.DataFrame = hist_dfs[0]

        for df in hist_dfs[1:]:
            hist_df = hist_df.merge(df, how = "outer")

        return hist_df.sort_values("Date").reset_index(drop = True)
    else:
        return None

def consolidate_all_stock_data(
    stock_data_dir: Path
):
    for stock_symbol in get_all_stock_symbols(stock_data_dir):
        stock_dir = stock_data_dir.joinpath(stock_symbol)
        file_count = len(list(stock_dir.glob('*.csv')))
        print(f"{stock_symbol} - {file_count} files")
        stock_df = get_consolidated_stock_data(stock_symbol, stock_data_dir)
        
        if stock_df is not None:
            print(f"\t{stock_df.shape[0]} records")
            print(f"\t{stock_df['Date'].min().date()} to {stock_df['Date'].max().date()}")
            filename = stock_dir.joinpath("consolidated.parquet")
            stock_df.to_parquet(filename, index = False)
            print(f"\tSaved to '{filename}'")