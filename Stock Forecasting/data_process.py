from datetime import date
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

@dataclass
class StockSummary:
    symbol: str
    num_records: int
    start_date: date
    end_date: date
    has_PE: bool

class StockData:
    def __init__(
        self,
        symbol: str,
        stock_data_dir: Path,
        eps_data_dir: Path,
        reload_data: bool = False
    ) -> None:
        self.symbol = symbol
        consolidated_data_path = stock_data_dir.joinpath(symbol, "consolidated.parquet")

        if reload_data or (not (consolidated_data_path.exists() and consolidated_data_path.is_file())):
            self.raw_data = self.consolidate_data(
                stock_data_dir,
                eps_data_dir
            )
            self.raw_data.to_parquet(consolidated_data_path, index = False)
        else:
            self.raw_data = pd.read_parquet(consolidated_data_path)

        self.summary = StockSummary(
            self.symbol,
            self.raw_data.shape[0],
            self.raw_data['Date'].min().date(),
            self.raw_data['Date'].max().date(),
            'PE' in self.raw_data.columns
        )

    def consolidate_data(
            self,
            stock_data_dir: Path,
            eps_data_dir: Path
        ) -> pd.DataFrame:
        print(f"\nReloading data for '{self.symbol}'...")

        hist_dfs = []
        files = list(stock_data_dir.joinpath(self.symbol).glob(f"*{self.symbol}*.csv"))

        for f in files:
            hist_df = pd.read_csv(f, thousands = ',')
            hist_df.columns = [c.strip() for c in hist_df.columns]
            hist_df["Date"] = pd.to_datetime(hist_df["Date"], format = r"%d-%b-%Y")
            hist_dfs.append(hist_df)
        
        if len(hist_dfs) > 0:
            hist_df: pd.DataFrame = hist_dfs[0]

            for df in hist_dfs[1:]:
                hist_df = hist_df.merge(df, how = "outer")
            
            hist_df = hist_df.sort_values(
                "Date"
            ).drop_duplicates(
                keep = 'first'
            ).reset_index(
                drop = True
            ).drop(
                labels = "series",
                axis = "columns"
            )

            col_names = [
                "Date", "Open", "High", "Low", "Prev Close", "LTP", "Close",
                "VWAP", "52W H", "52W L", "Volume", "Value", "Num Trades"
            ]

            eps_file = eps_data_dir.joinpath(f"{self.symbol}.csv")

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

                col_names.append("PE")
            
            hist_df.columns = col_names

            print(f"Loaded {hist_df.shape[0]} records from {len(files)} files with data from {hist_df['Date'].min().date()} to {hist_df['Date'].max().date()}.")
            return hist_df
        else:
            raise Exception(f"Could not load data for '{self.symbol}'")
    
    def create_features(self):
        self._create_daily_candle_features()
        self._create_streak_features()

    def _create_daily_candle_features(self):
        self.raw_data['Range'] = self.raw_data['High'] - self.raw_data['Low']
        self.raw_data['IsGreen'] = (
            self.raw_data['Close'] >= self.raw_data['Prev Close']
        ).astype(np.int8)
    
    def _create_streak_features(self):
        green_filter = self.raw_data['IsGreen'] == 1

        self.raw_data["StreakIndex"] = (self.raw_data["IsGreen"] != self.raw_data["IsGreen"].shift(1)).cumsum()
        self.raw_data["Streak"] = self.raw_data.groupby("StreakIndex").cumcount() + 1

        self.last_candle = self.raw_data['IsGreen'].iloc[-1]
        self.candle_streak = self.raw_data['Streak'].iloc[-1]

        max_streaks = self.raw_data.groupby(
            ['StreakIndex', 'IsGreen'], 
            as_index = False
        )['Streak'].max()

        self.streak_cont_prob = max_streaks[
            (max_streaks['IsGreen'] == self.last_candle) &
            (max_streaks['Streak'] > self.candle_streak)
        ].shape[0] / max_streaks[max_streaks['IsGreen'] == self.last_candle].shape[0]