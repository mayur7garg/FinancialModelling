from pathlib import Path
from datetime import datetime

import pandas as pd

import constants as cnst

class StockData():
    def __init__(
        self,
        stock_symbol: str
    ) -> None:
        self.stock_symbol: str = stock_symbol
        self.processed: pd.DataFrame = pd.read_parquet(
            cnst.PROCESSED_DATA_DIR.joinpath(
                f'{stock_symbol}-processed.parquet'
            )
        )
        self.standardized: pd.DataFrame = pd.read_parquet(
            cnst.PROCESSED_DATA_DIR.joinpath(
                f'{stock_symbol}-standardized.parquet'
            )
        )

    def print_info(self) -> str:
        info: str = f"Symbol: {self.stock_symbol}\n"
        info += f"Total records: {self.processed.shape[0]}\n"
        info += f"First record: {self.processed['Date'].min().date()}\n"
        info += f"Last record: {self.processed['Date'].max().date()}"

        return info
    
    def __repr__(self) -> str:
        return self.print_info()
    
    def get_first_hit(
        self,
        target: float, 
        metric = "Close"
    ):
        all_hits = self.processed[self.processed[metric] >= target]

        if len(all_hits) > 0:
            first_hit = all_hits["Date"].min()
            print(f"Target: {target}")
            print(f"First hit: {first_hit.date()} | {(datetime.today().date() - first_hit.date()).days} days ago")
            print(f"'{metric}' at first hit: {all_hits[all_hits['Date'] == first_hit][metric].values[0]}")
            print(f"Total hits: {len(all_hits)}")
        else:
            print(f"No matching record for target = {target} and metric = {metric}.")

def get_all_stock_symbols(stock_data_dir: Path):
    return [
        f.stem for f in stock_data_dir.glob("*") if f.is_dir()
    ]

def get_consolidated_stock_data(
    stock_symbol: str,
    stock_data_dir: Path,
    eps_data_dir: Path
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
        
        hist_df = hist_df.sort_values("Date").reset_index(drop = True)
        eps_file = eps_data_dir.joinpath(f"{stock_symbol}.csv")

        if eps_file.exists():
            eps_df = pd.read_csv(eps_file)

            eps_df["FirstDateAfterFYReport"] = pd.to_datetime(
                eps_df["FirstDateAfterFYReport"],
                format = "%d-%m-%Y"
            )

            hist_df = pd.merge(
                hist_df,
                eps_df,
                how = "left",
                left_on = [hist_df['Date'].dt.strftime("%Y-%m")],
                right_on = [eps_df['FirstDateAfterFYReport'].dt.strftime("%Y-%m")]
            )

            hist_df['EPS'] = hist_df['EPS'].ffill()
            hist_df['EPS'] = hist_df['EPS'].fillna(
                value = eps_df[
                    eps_df["FirstDateAfterFYReport"] < hist_df["Date"].min()
                ]["EPS"].iloc[-1]
            )
            hist_df["PE"] = (hist_df["close"] / hist_df["EPS"]).round(3)

            hist_df = hist_df.drop(
                axis = "columns", 
                labels = ["key_0", "FirstDateAfterFYReport", "EPS"]
            )

        return hist_df
    else:
        return None

def consolidate_all_stock_data(
    stock_data_dir: Path,
    eps_data_dir: Path
):
    for stock_symbol in get_all_stock_symbols(stock_data_dir):
        stock_dir = stock_data_dir.joinpath(stock_symbol)
        file_count = len(list(stock_dir.glob('*.csv')))
        print(f"{stock_symbol} - {file_count} files")
        stock_df = get_consolidated_stock_data(
            stock_symbol, 
            stock_data_dir,
            eps_data_dir
        )
        
        if stock_df is not None:
            print(f"\t{stock_df.shape[0]} records")
            print(f"\t{stock_df['Date'].min().date()} to {stock_df['Date'].max().date()}")
            filename = stock_dir.joinpath("consolidated.parquet")
            stock_df.to_parquet(filename, index = False)
            print(f"\tSaved to '{filename}'")