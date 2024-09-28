from datetime import date
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from metrics import spearman_over_ma

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

@dataclass
class PerformanceReport:
    period_size: int
    start_date: date
    net_returns: float
    avg_daily_returns: float
    avg_close: float
    lowest_close: float
    hightest_close: float

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
        self.consolidated_data_path = stock_data_dir.joinpath(symbol, "consolidated.parquet")

        if reload_data or (not (self.consolidated_data_path.exists() and self.consolidated_data_path.is_file())):
            self.raw_data = self.consolidate_data(
                stock_data_dir,
                eps_data_dir
            )
            self.raw_data.to_parquet(self.consolidated_data_path, index = False)
        else:
            self.raw_data = pd.read_parquet(self.consolidated_data_path)

        self.last_close = self.raw_data['Close'].iloc[-1]

        self.summary = StockSummary(
            self.symbol,
            self.raw_data.shape[0],
            self.raw_data['Date'].min().date(),
            self.raw_data['Date'].max().date(),
            self.last_close,
            'PE' in self.raw_data.columns
        )
        self.perf_reports: list[PerformanceReport] = []

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
    
    def create_features(
        self, 
        performance_periods: list[int],
        sp_ma_periods: list[list[int]]
    ):
        self._create_performance_features(performance_periods)
        self._create_rolling_features()
        self._create_historical_features()
        self._create_daily_candle_features()
        self._create_streak_features()
        self._create_sp_ma_features(sp_ma_periods)
        self._create_ath_features()

    def _create_performance_features(self, performance_periods: list[int]):
        for period in performance_periods:
            period_df = self.raw_data.iloc[-period :]
            period_size = len(period_df)
            net_returns = (period_df['Close'].iloc[-1] / period_df['Prev Close'].iloc[0])

            self.perf_reports.append(
                PerformanceReport(
                    period_size,
                    period_df['Date'].min().date(),
                    net_returns - 1,
                    (net_returns ** (1 / period_size)) - 1,
                    period_df['Close'].mean(),
                    period_df['Close'].min(),
                    period_df['Close'].max()
                )
            )
    
    def _create_rolling_features(self):
        self.raw_data['% Rolling Returns 200 days'] = (
            self.raw_data['Close'] / 
            self.raw_data['Prev Close'].rolling(
                window = 200, 
                min_periods = 200
            ).agg(lambda rows: rows.iloc[0])
        )

        self.raw_data['% Rolling Returns 1000 days'] = (
            self.raw_data['Close'] / 
            self.raw_data['Prev Close'].rolling(
                window = 1000, 
                min_periods = 200
            ).agg(lambda rows: rows.iloc[0])
        )

        self.raw_data['% Rolling Returns 200 days'] = (
            (self.raw_data['% Rolling Returns 200 days'] ** (1 / 200)) - 1
        ).round(5) * 100
        self.raw_data['% Rolling Returns 1000 days'] = (
            (self.raw_data['% Rolling Returns 1000 days'] ** (1 / 1000)) - 1
        ).round(5) * 100

        self._save_rolling_plots()
    
    def _save_rolling_plots(self):
        with sns.axes_style('dark'):
            plot_data = self.raw_data[
                ['Date', '% Rolling Returns 200 days', '% Rolling Returns 1000 days']
            ].iloc[-500:]

            plt.figure(figsize = (10, 5), dpi = 125)
            sns.lineplot(
                plot_data,
                x = 'Date',
                y = '% Rolling Returns 200 days'
            )

            plt.axhline(y = 0, linestyle = "dashdot", color = "indianred", label = "No change")
            plt.axhline(
                y = self.raw_data['% Rolling Returns 200 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "goldenrod", 
                label = "Overall median"
            )
            plt.axhline(
                y = plot_data['% Rolling Returns 200 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "mediumseagreen", 
                label = "Last 500 days median"
            )
            plt.legend()
            plt.xlabel("End date", fontsize = 12)
            plt.ylabel("Average Daily Return (%)", fontsize = 12)
            plt.title(f"{self.symbol} - Average daily 200 days rolling returns", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Avg_Rolling_Returns_200.png"), 
                bbox_inches = "tight"
            )
            plt.close()

            plt.figure(figsize = (10, 5), dpi = 125)
            sns.lineplot(
                plot_data[['Date', '% Rolling Returns 1000 days']],
                x = 'Date',
                y = '% Rolling Returns 1000 days'
            )

            plt.axhline(y = 0, linestyle = "dashdot", color = "indianred", label = "No change")
            plt.axhline(
                y = self.raw_data['% Rolling Returns 1000 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "goldenrod", 
                label = "Overall median"
            )
            plt.axhline(
                y = plot_data['% Rolling Returns 1000 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "mediumseagreen", 
                label = "Last 500 days median"
            )
            plt.legend()
            plt.xlabel("End date", fontsize = 12)
            plt.ylabel("Average Daily Return (%)", fontsize = 12)
            plt.title(f"{self.symbol} - Average daily 1000 days rolling returns", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Avg_Rolling_Returns_1000.png"), 
                bbox_inches = "tight"
            )
            plt.close()

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
        self.raw_data['Is Green'] = (
            self.raw_data['Close'] >= self.raw_data['Prev Close']
        ).astype(np.int8)
        self.last_candle = self.raw_data['Is Green'].iloc[-1]
        self.last_candle_overall_pcnt = len(
            self.raw_data[
                self.raw_data['Is Green'] == self.last_candle
            ]['Is Green']
        ) / self.summary.num_records

        self._save_daily_candle_plots()
    
    def _save_daily_candle_plots(self):
        with sns.axes_style('dark'):
            plt.figure(figsize = (10, 5), dpi = 125)
            sns.barplot(
                data = self.raw_data.groupby(
                    self.raw_data['Date'].dt.quarter, as_index = False
                )['Is Green'].value_counts(normalize = True),
                x = "Date",
                y = "proportion",
                hue = "Is Green",
                palette = "blend:indianred,mediumseagreen"
            )
            plt.hlines(
                y = 0.5, 
                xmin = -0.5, 
                xmax = 5, 
                linestyles = "dashdot",
                linewidths = (1.5,),
                colors = "goldenrod"
            )
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
                )['Is Green'].value_counts(normalize = True),
                x = "Date",
                y = "proportion",
                hue = "Is Green",
                palette = "blend:indianred,mediumseagreen"
            )
            plt.hlines(
                y = 0.5, 
                xmin = -0.5, 
                xmax = 5, 
                linestyles = "dashdot",
                linewidths = (1.5,),
                colors = "goldenrod"
            )
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
        self.raw_data["Streak Index"] = (self.raw_data["Is Green"] != self.raw_data["Is Green"].shift(1)).cumsum()
        self.raw_data["Streak"] = self.raw_data.groupby("Streak Index").cumcount() + 1
        self.candle_streak = self.raw_data['Streak'].iloc[-1]
        si = self.raw_data['Streak Index'].iloc[-1]
        curr_si = self.raw_data.loc[self.raw_data['Streak Index'] == si, ['Prev Close', 'Close']]
        self.curr_streak_returns = (curr_si['Close'].iloc[-1] / curr_si['Prev Close'].iloc[0]) - 1

        max_streaks = self.raw_data.groupby(
            ['Streak Index', 'Is Green'], 
            as_index = False
        )['Streak'].max()

        self.streak_cont_prob = max_streaks[
            (max_streaks['Is Green'] == self.last_candle) &
            (max_streaks['Streak'] > self.candle_streak)
        ].shape[0] / max_streaks[
            (max_streaks['Is Green'] == self.last_candle) &
            (max_streaks['Streak'] >= self.candle_streak)
        ].shape[0]

        self._save_streak_plots(max_streaks)
    
    def _save_streak_plots(self, max_streaks: pd.DataFrame):
        with sns.axes_style('dark'):
            plt.figure(figsize = (10, 5), dpi = 125)
            sns.barplot(
                max_streaks[max_streaks['Is Green'] == 1]['Streak'].value_counts(normalize = True).sort_index(),
                color = "mediumseagreen",
                label = "Green candles"
            )
            sns.barplot(
                max_streaks[max_streaks['Is Green'] == 0]['Streak'].value_counts(normalize = True).mul(-1).sort_index(),
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

    def _create_sp_ma_features(self, sp_ma_periods: list[list[int]]):
        sp_col_names = []

        for sp_wins in sp_ma_periods:
            col_name = f"MA-S ({min(sp_wins)}-{max(sp_wins)}-{len(sp_wins)})"
            self.raw_data[col_name] = spearman_over_ma(
                self.raw_data['Close'],
                sp_wins
            )
            sp_col_names.append(col_name)

        self._save_sp_ma_plts(sp_col_names)
    
    def _save_sp_ma_plts(self, sp_col_names: list[str]):
        bins = [-1, -0.3, 0.3, 1]
        plot_data = self.raw_data[
            ['Date', 'Close'] + sp_col_names
        ].iloc[-500:]

        for c_i, col_name in enumerate(sp_col_names, start = 1):
            with sns.axes_style('dark'):
                plt.figure(figsize = (10, 5), dpi = 125)
                colors = pd.cut(
                    plot_data[col_name], 
                    bins = bins, 
                    labels = ['indianred', 'goldenrod', 'mediumseagreen'], 
                    include_lowest = True
                ).values

                labels = pd.cut(
                    plot_data[col_name], 
                    bins = bins, 
                    labels = ['Weak', 'Neutral', 'Strong'], 
                    include_lowest = True
                ).values

                for i in range(1, len(plot_data)):
                    plt.plot(
                        plot_data['Date'].iloc[i - 1 : i + 1],
                        plot_data['Close'].iloc[i - 1 : i + 1],
                        c = colors[i],
                        label = labels[i],
                        linewidth = 1.5
                    )

                handles, hand_labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(hand_labels, handles))
                plt.legend(by_label.values(), by_label.keys())
                plt.xlabel("Date", fontsize = 12)
                plt.ylabel("Close Price", fontsize = 12)
                plt.title(f"{self.symbol} - Close price highlighted by {col_name}", fontsize = 14)
                plt.savefig(
                    self.image_out_path.joinpath(f"{self.symbol}_Close_Price_MA_S_{c_i}.png"), 
                    bbox_inches = "tight"
                )
                plt.close()

    def _create_ath_features(self):
        self.raw_data['ATH'] = self.raw_data['Close'].cummax()
        self.raw_data['% Down from ATH'] = (
            (self.raw_data['Close'] - self.raw_data['ATH']) /
            self.raw_data['ATH']
        ).round(5) * 100

        self.ath_hits_1000_days = (self.raw_data['% Down from ATH'].iloc[-1000:] == 0).sum()
        self.last_ath_date = self.raw_data.loc[
            self.raw_data['% Down from ATH'] == 0, 'Date'
        ].iloc[-1]
        self._save_ath_plots()

    def _save_ath_plots(self):
        with sns.axes_style('dark'):
            plot_data = self.raw_data[['Date', '% Down from ATH']].iloc[-1000:]

            plt.figure(figsize = (10, 5), dpi = 125)
            sns.lineplot(
                plot_data,
                x = 'Date',
                y = '% Down from ATH'
            )

            plt.axhline(y = 0, linestyle = "dashdot", color = "indianred", label = "ATH")
            plt.legend()
            plt.xlabel("Date", fontsize = 12)
            plt.ylabel("Down from ATH (%)", fontsize = 12)
            plt.title(f"{self.symbol} - Drawdown from ATH", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Pcnt_Drawdown_ATH.png"), 
                bbox_inches = "tight"
            )
            plt.close()

def get_correlation_report(
    close_prices: list[pd.DataFrame], 
    max_records = 1000
) -> CorrelationReport:
    all_prices = close_prices[0].join(close_prices[1:], how = "outer").sort_index().iloc[-max_records:]
    
    corrs = all_prices.corr("pearson")
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