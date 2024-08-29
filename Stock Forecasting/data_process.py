from datetime import date
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

@dataclass
class StockSummary:
    symbol: str
    num_records: int
    start_date: date
    end_date: date
    last_close: float
    has_PE: bool

@dataclass
class CorrelationReport:
    num_records: int
    start_date: date
    end_date: date
    min_corrs: dict[str, tuple[str, float]]
    max_corrs: dict[str, tuple[str, float]]

class StockData:
    def __init__(
        self,
        symbol: str,
        stock_data_dir: Path,
        eps_data_dir: Path,
        image_out_path: Path,
        reload_data: bool = False
    ) -> None:
        self.symbol = symbol
        self.image_out_path = image_out_path
        consolidated_data_path = stock_data_dir.joinpath(symbol, "consolidated.parquet")

        if reload_data or (not (consolidated_data_path.exists() and consolidated_data_path.is_file())):
            self.raw_data = self.consolidate_data(
                stock_data_dir,
                eps_data_dir
            )
            self.raw_data.to_parquet(consolidated_data_path, index = False)
        else:
            self.raw_data = pd.read_parquet(consolidated_data_path)

        self.last_close = self.raw_data['Close'].iloc[-1]

        self.summary = StockSummary(
            self.symbol,
            self.raw_data.shape[0],
            self.raw_data['Date'].min().date(),
            self.raw_data['Date'].max().date(),
            self.last_close,
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
        self._create_historical_features()
        self._create_daily_candle_features()
        self._create_streak_features()

    def _create_historical_features(self):
        self._get_first_hit_of_last_close()
        self._save_historical_plots()

    def _get_first_hit_of_last_close(self):
        all_hits = self.raw_data[self.raw_data["Close"] >= self.last_close]
        self.total_hits_of_last_close = len(all_hits)

        if self.total_hits_of_last_close > 0:
            self.first_hit_of_last_close = all_hits["Date"].min().date()
            self.pcnt_hit_of_last_close = (
                self.total_hits_of_last_close / 
                len(self.raw_data[self.raw_data["Date"].dt.date >= self.first_hit_of_last_close])
            )
        else:
            self.pcnt_hit_of_last_close = 0
    
    def _save_historical_plots(self):
        with sns.axes_style('dark'):
            plt.figure(figsize = (10, 5), dpi = 125)

            kde_data_x, kde_data_y = sns.kdeplot(
                data = self.raw_data,
                x = "Close",
                cumulative = True
            ).lines[0].get_data()

            xticks = []

            for q in [i/10 for i in range(1, 10)]:
                kde_x, kde_y = kde_data_x[kde_data_y > q][0], kde_data_y[kde_data_y > q][0]

                plt.vlines(
                    x = kde_x,
                    ymin = 0,
                    ymax = kde_y,
                    linestyles = "solid",
                    colors = "mediumseagreen",
                    linewidth = 1
                )

                xticks.append(int(kde_x))

            plt.xlim((0, None))
            plt.xticks(xticks, rotation = 75, fontsize = 8)
            plt.xlabel("Close Price", fontsize = 12)
            plt.ylabel("Density", fontsize = 12)
            plt.title(f"{self.symbol} - CDF and quantiles of Close price", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_CDF_Close_Price.png"), 
                bbox_inches = "tight"
            )
            plt.close()

    def _create_daily_candle_features(self):
        self.raw_data['Range'] = self.raw_data['High'] - self.raw_data['Low']
        self.raw_data['IsGreen'] = (
            self.raw_data['Close'] >= self.raw_data['Prev Close']
        ).astype(np.int8)
        self.last_candle = self.raw_data['IsGreen'].iloc[-1]
        self.last_candle_overall_pcnt = len(
            self.raw_data[
                self.raw_data['IsGreen'] == self.last_candle
            ]['IsGreen']
        ) / self.summary.num_records

        self._save_daily_candle_plots()
    
    def _save_daily_candle_plots(self):
        with sns.axes_style('dark'):
            plt.figure(figsize = (10, 5), dpi = 125)
            sns.barplot(
                data = self.raw_data.groupby(
                    self.raw_data['Date'].dt.quarter, as_index = False
                )['IsGreen'].value_counts(normalize = True),
                x = "Date",
                y = "proportion",
                hue = "IsGreen",
                palette = "blend:indianred,mediumseagreen"
            )
            plt.hlines(y = 0.5, xmin = -0.5, xmax = 5, linestyles = "dotted", colors = "red")
            plt.ylim((0, 1))
            plt.xlim((-0.5, 3.5))
            plt.xlabel("Calendar quarter", fontsize = 12)
            plt.ylabel("Proportion", fontsize = 12)
            plt.title(f"{self.symbol} - Proportion of candle types by calendar quarter", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Pcnt_Candles_Quarter.png"), 
                bbox_inches = "tight"
            )
            plt.close()
            
            plt.figure(figsize = (10, 5), dpi = 125)
            sns.barplot(
                data = self.raw_data.groupby(
                    self.raw_data['Date'].dt.year, as_index = False
                )['IsGreen'].value_counts(normalize = True),
                x = "Date",
                y = "proportion",
                hue = "IsGreen",
                palette = "blend:indianred,mediumseagreen"
            )
            plt.hlines(y = 0.5, xmin = -0.5, xmax = 5, linestyles = "dotted", colors = "red")
            plt.ylim((0, 1))
            plt.xlim((
                -0.5, 
                self.raw_data['Date'].dt.year.max() - self.raw_data['Date'].dt.year.min() + 0.5
            ))
            plt.xlabel("Year", fontsize = 12)
            plt.ylabel("Proportion", fontsize = 12)
            plt.title(f"{self.symbol} - Proportion of candle types by year", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Pcnt_Candles_Year.png"), 
                bbox_inches = "tight"
            )
            plt.close()
    
    def _create_streak_features(self):
        green_filter = self.raw_data['IsGreen'] == 1

        self.raw_data["StreakIndex"] = (self.raw_data["IsGreen"] != self.raw_data["IsGreen"].shift(1)).cumsum()
        self.raw_data["Streak"] = self.raw_data.groupby("StreakIndex").cumcount() + 1
        self.candle_streak = self.raw_data['Streak'].iloc[-1]

        max_streaks = self.raw_data.groupby(
            ['StreakIndex', 'IsGreen'], 
            as_index = False
        )['Streak'].max()

        self.streak_cont_prob = max_streaks[
            (max_streaks['IsGreen'] == self.last_candle) &
            (max_streaks['Streak'] > self.candle_streak)
        ].shape[0] / max_streaks[max_streaks['IsGreen'] == self.last_candle].shape[0]

        self._save_streak_plots(max_streaks)
    
    def _save_streak_plots(self, max_streaks: pd.DataFrame):
        with sns.axes_style('dark'):
            plt.figure(figsize = (10, 5), dpi = 125)
            sns.barplot(
                max_streaks[max_streaks['IsGreen'] == 1]['Streak'].value_counts(normalize = True).sort_index(),
                color = "mediumseagreen",
                label = "Green candles"
            )
            sns.barplot(
                max_streaks[max_streaks['IsGreen'] == 0]['Streak'].value_counts(normalize = True).mul(-1).sort_index(),
                color = "indianred",
                label = "Red candles"
            )
            plt.legend()
            plt.xlabel("Streak length", fontsize = 12)
            plt.ylabel("Percentage", fontsize = 12)
            plt.title(f"{self.symbol} - Percentage of streak lengths by candle type", fontsize = 14)
            plt.yticks(np.linspace(-1, 1, 9), labels = np.abs(np.linspace(-100, 100, 9, dtype = np.int8)))
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Pcnt_Streak_Length.png"), 
                bbox_inches = "tight"
            )
            plt.close()

def get_correlation_report(
    close_prices: list[pd.DataFrame], 
    max_records = 1000
) -> CorrelationReport:
    all_prices = close_prices[0].join(close_prices[1:], how = "outer").sort_index().iloc[-max_records:]
    
    corrs = all_prices.corr("spearman")
    min_corrs = {}
    max_corrs = {}

    for symbol in corrs.columns:
        sym_corr = corrs[symbol].sort_values()
        min_corrs[symbol] = (sym_corr.index[0], sym_corr.iloc[0])
        max_corrs[symbol] = (sym_corr.index[-2], sym_corr.iloc[-2])

    return CorrelationReport(
        len(all_prices),
        all_prices.index.min().date(),
        all_prices.index.max().date(),
        min_corrs,
        max_corrs
    )