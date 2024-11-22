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
    last_change: float
    has_PE: bool
    last_PE: float

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
    median_close: float
    lowest_close: float
    hightest_close: float
    mean_value: float
    median_PE: float

class StockData:
    def __init__(
        self,
        symbol: str,
        stock_data_dir: Path,
        company_data_dir: Path,
        image_out_path: Path,
        reload_data: bool = False
    ) -> None:
        self.symbol = symbol
        self.image_out_path = image_out_path.joinpath(symbol)
        self.image_out_path.mkdir(exist_ok = True, parents = True)
        self.consolidated_data_path = stock_data_dir.joinpath(symbol, "consolidated.parquet")

        if reload_data or (not (self.consolidated_data_path.exists() and self.consolidated_data_path.is_file())):
            self.raw_data = self.consolidate_data(
                stock_data_dir,
                company_data_dir
            )
            self.raw_data.to_parquet(self.consolidated_data_path, index = False)
        else:
            self.raw_data = pd.read_parquet(self.consolidated_data_path)

        self.last_close = self.raw_data['Close'].iloc[-1]
        has_PE = 'PE' in self.raw_data.columns

        self.summary = StockSummary(
            self.symbol,
            self.raw_data.shape[0],
            self.raw_data['Date'].min().date(),
            self.raw_data['Date'].max().date(),
            self.last_close,
            (self.raw_data['Close'].iloc[-1] / self.raw_data['Prev Close'].iloc[-1]) - 1,
            has_PE,
            self.raw_data['PE'].iloc[-1] if has_PE else 0
        )
        self.perf_reports: list[PerformanceReport] = []
        self.highlights: list[str] = []

    def consolidate_data(
            self,
            stock_data_dir: Path,
            company_data_dir: Path
        ) -> pd.DataFrame:

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

            eps_file = company_data_dir.joinpath("EPS", f"{self.symbol}.csv")

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

            stock_split_file = company_data_dir.joinpath("StockSplit", f"{self.symbol}.csv")

            if stock_split_file.exists():
                stock_split_df = pd.read_csv(stock_split_file)

                stock_split_df["RecordDate"] = pd.to_datetime(
                    stock_split_df["RecordDate"],
                    format = "%d-%m-%Y"
                )
                stock_split_df['StockMultiplier'] = 1 / stock_split_df['StockMultiplier'].cumprod()

                price_multiplier_df = pd.merge(
                    hist_df[['Date']], 
                    stock_split_df, 
                    how = "left", 
                    left_on = "Date", 
                    right_on = "RecordDate"
                )

                price_multiplier_df['StockMultiplier'] = price_multiplier_df['StockMultiplier'].bfill().fillna(1)
                hist_df['Prev Close'] = hist_df['Prev Close'] * price_multiplier_df['StockMultiplier']

                price_multiplier_df['StockMultiplier'] = price_multiplier_df['StockMultiplier'].shift(-1).fillna(1)

                for col in ["Open", "High", "Low", "LTP", "Close", "VWAP"]:
                    hist_df[col] = hist_df[col] * price_multiplier_df['StockMultiplier']

            print(f"> Loaded {hist_df.shape[0]} records from {len(files)} files with data from {hist_df['Date'].min().date()} to {hist_df['Date'].max().date()}.")
            return hist_df
        else:
            raise Exception(f"Could not load data for '{self.symbol}'")
    
    def create_features(
        self, 
        performance_periods: list[int],
        ma_periods: list[int],
        sp_ma_periods: list[list[int]]
    ):
        self._create_performance_features(performance_periods)
        self._create_ma_features(ma_periods)
        self._create_rolling_features()
        self._create_historical_features()
        self._create_daily_quarterly_features()
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
                    period_df['Close'].median(),
                    period_df['Close'].min(),
                    period_df['Close'].max(),
                    period_df['Value'].mean(),
                    period_df['PE'].median() if self.summary.has_PE else 0
                )
            )

    def _create_ma_features(self, ma_periods: list[int]):
        for period in ma_periods:
            col_name = f'MA {period} days'

            self.raw_data[col_name] = self.raw_data['Close'].rolling(
                window = period,
                min_periods = 1
            ).mean()
            self.raw_data[f'% Change from {period} MA'] = (
                (self.raw_data['Close'] - self.raw_data[col_name]) /
                self.raw_data[col_name]
            ).round(5) * 100
        
        is_above_200_MA = self.raw_data['Close'] >= self.raw_data['MA 200 days']
        is_above_200_MA_si = (
            is_above_200_MA != is_above_200_MA.shift(1)
        ).cumsum()
        is_above_200_MA_streak = (is_above_200_MA.groupby(
            is_above_200_MA_si
        ).cumcount() + 1).iloc[-1]

        if is_above_200_MA_streak >= 200:
            streak_start_date = self.raw_data['Date'][is_above_200_MA_si == is_above_200_MA_si.iloc[-1]].iloc[0].date()
            streak_returns = ((
                self.last_close / self.raw_data[self.raw_data['Date'].dt.date == streak_start_date]['Prev Close']
            ) - 1).values[0]

            if is_above_200_MA.iloc[-1]:
                self.highlights.append(
                    f'<li>This stock has closed above its 200 day moving average since <span class="metric">{streak_start_date:%B %d, %Y}</span> which is <span class="metric color-green">{is_above_200_MA_streak}</span> trading days in a row for a net return of <span class="metric color-green">{streak_returns:.2%}</span>.</li>'
                )
            else:
                self.highlights.append(
                    f'<li>This stock has closed below its 200 day moving average since <span class="metric">{streak_start_date:%B %d, %Y}</span> which is <span class="metric color-red">{is_above_200_MA_streak}</span> trading days in a row for a net return of <span class="metric color-red">{streak_returns:.2%}</span>.</li>'
                )

        self._save_ma_plots(ma_periods)

    def _save_ma_plots(self, ma_periods: list[int]):
        with sns.axes_style('dark'):
            plot_data = self.raw_data.iloc[-1000:]

            plt.figure(figsize = (10, 5), dpi = 125)
            plt.axhline(y = self.last_close, linestyle = "dashdot", label = "Last Close Price")

            for period, color in zip(
                ma_periods,
                ['mediumseagreen', 'goldenrod', 'indianred']
            ):
                sns.lineplot(
                    plot_data,
                    x = 'Date',
                    y = f'MA {period} days',
                    label = f'MA {period}-D',
                    c = color
                )

            plt.legend()
            plt.xlabel("Date", fontsize = 12)
            plt.ylabel("Close Price", fontsize = 12)
            plt.title(f"{self.symbol} - Moving averages of Close price", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_MA_Close_Price.png"), 
                bbox_inches = "tight"
            )
            plt.close()

            for period, color in zip(
                ma_periods,
                ['mediumseagreen', 'goldenrod', 'indianred']
            ):
                plt.figure(figsize = (10, 5), dpi = 125)
                plt.axhline(y = 0, linestyle = "dashdot", color = color, label = f'MA {period}-D')

                sns.lineplot(
                    plot_data,
                    x = 'Date',
                    y = f'% Change from {period} MA',
                    label = f"Latest: {plot_data[f'% Change from {period} MA'].iloc[-1]:.1f}%"
                )

                plt.legend()
                plt.xlabel("Date", fontsize = 12)
                plt.ylabel(f"Change from {period}-D MA (%)", fontsize = 12)
                plt.title(f"{self.symbol} - Change from {period}-D MA", fontsize = 14)
                plt.savefig(
                    self.image_out_path.joinpath(f"{self.symbol}_Pcnt_Change_MA_{period}.png"), 
                    bbox_inches = "tight"
                )
                plt.close()
    
    def _create_rolling_features(self):
        self.raw_data['% Rolling Returns 200 days'] = (
            self.raw_data['Close'] / 
            self.raw_data['Prev Close'].rolling(
                window = 200, 
                min_periods = 1
            ).agg(lambda rows: rows.iloc[0])
        )

        self.raw_data['% Rolling Returns 1000 days'] = (
            self.raw_data['Close'] / 
            self.raw_data['Prev Close'].rolling(
                window = 1000, 
                min_periods = 1
            ).agg(lambda rows: rows.iloc[0])
        )

        self.raw_data['% Rolling Returns 200 days'] = (
            (self.raw_data['% Rolling Returns 200 days'] ** (
                1 / self.raw_data['Prev Close'].rolling(
                    window = 200, 
                    min_periods = 1
                ).count()
            )) - 1
        ).round(5) * 100
        self.raw_data['% Rolling Returns 1000 days'] = (
            (self.raw_data['% Rolling Returns 1000 days'] ** (
                1 / self.raw_data['Prev Close'].rolling(
                    window = 1000, 
                    min_periods = 1
                ).count()
            )) - 1
        ).round(5) * 100

        self._save_rolling_plots()
    
    def _save_rolling_plots(self):
        with sns.axes_style('dark'):
            plot_data = self.raw_data[
                ['Date', '% Rolling Returns 200 days', '% Rolling Returns 1000 days']
            ].iloc[-500:]

            plt.figure(figsize = (10, 5), dpi = 125)

            plt.axhline(y = 0, linestyle = "dashdot", color = "indianred", label = "No change")
            plt.axhline(
                y = self.raw_data['% Rolling Returns 200 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "goldenrod", 
                label = f"Overall median ({self.raw_data['% Rolling Returns 200 days'].median():.3f}%)"
            )
            plt.axhline(
                y = plot_data['% Rolling Returns 200 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "mediumseagreen", 
                label = f"Last 500-D median ({plot_data['% Rolling Returns 200 days'].median():.3f}%)"
            )

            sns.lineplot(
                plot_data,
                x = 'Date',
                y = '% Rolling Returns 200 days',
                label = f"Latest: {plot_data['% Rolling Returns 200 days'].iloc[-1]:.3f}%"
            )

            plt.legend(fontsize = 'small')
            plt.xlabel("End date", fontsize = 12)
            plt.ylabel("Average Daily Return (%)", fontsize = 12)
            plt.title(f"{self.symbol} - Average daily 200 days rolling returns", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Avg_Rolling_Returns_200.png"), 
                bbox_inches = "tight"
            )
            plt.close()

            plt.figure(figsize = (10, 5), dpi = 125)

            plt.axhline(y = 0, linestyle = "dashdot", color = "indianred", label = "No change")
            plt.axhline(
                y = self.raw_data['% Rolling Returns 1000 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "goldenrod", 
                label = f"Overall median ({self.raw_data['% Rolling Returns 1000 days'].median():.3f}%)"
            )
            plt.axhline(
                y = plot_data['% Rolling Returns 1000 days'].median(), 
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "mediumseagreen", 
                label = f"Last 500-D median ({plot_data['% Rolling Returns 1000 days'].median():.3f}%)"
            )

            sns.lineplot(
                plot_data[['Date', '% Rolling Returns 1000 days']],
                x = 'Date',
                y = '% Rolling Returns 1000 days',
                label = f"Latest: {plot_data['% Rolling Returns 1000 days'].iloc[-1]:.3f}%"
            )

            plt.legend(fontsize = 'small')
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
        total_hits = []
        first_hits = []
        last_hits = []
        pcnt_hits = []

        for row in self.raw_data.itertuples():
            row_df = self.raw_data[self.raw_data['Date'] <= row.Date]
            all_hits = row_df["Date"][row_df["Close"] >= row.Close]
            total_hit = len(all_hits)
            first_hit = all_hits.min().date()
            last_hit = all_hits.iloc[-2].date() if total_hit > 1 else first_hit
            pcnt_hit = total_hit / len(row_df[row_df['Date'].dt.date >= first_hit])
            
            total_hits.append(total_hit)
            first_hits.append(first_hit)
            last_hits.append(last_hit)
            pcnt_hits.append(pcnt_hit)
        
        self.raw_data['Total hits of Close'] = total_hits
        self.raw_data['First hit of Close'] = first_hits
        self.raw_data['Last hit of Close'] = last_hits
        self.raw_data['Pcnt hits of Close'] = pcnt_hits
    
    def _save_historical_plots(self):
        with sns.axes_style('dark'):
            plt.figure(figsize = (10, 5), dpi = 125)
            plot_data = self.raw_data.iloc[-500:]

            sns.lineplot(
                x = plot_data['Date'],
                y = pd.to_timedelta(
                    plot_data['Date'].dt.date - plot_data['First hit of Close']
                ).dt.days,
                label = "Max period by date"
            )

            plt.axhline(
                y = pd.to_timedelta(
                    self.raw_data['Date'].dt.date - self.raw_data['First hit of Close']
                ).dt.days.max(),
                linestyle = "dashdot",
                color = "indianred",
                label = 'Overall max period'
            )

            plt.legend()
            plt.xlabel("Date", fontsize = 12)
            plt.ylabel("Calendar days", fontsize = 12)
            plt.title(f"{self.symbol} - Max period of non positive return", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Max_Period_of_No_Return.png"), 
                bbox_inches = "tight"
            )
            plt.close()

            plt.figure(figsize = (10, 5), dpi = 125)
            
            sns.histplot(
                x = self.raw_data["Close"].iloc[-1000:],
                bins = np.linspace(self.last_close * 0.75, self.last_close * 1.25, 21)
            )
            plt.axvline(x = self.last_close, linestyle = "dashdot", color = "goldenrod", label = 'Last Close')
            plt.axhline(
                y = 20,
                xmax = 0.5,
                linestyle = "dashdot",
                color = "mediumseagreen",
                label = 'Support'
            )
            plt.axhline(
                y = 15,
                xmin = 0.5,
                linestyle = "dashdot",
                color = "indianred",
                label = 'Resistance'
            )
            plt.legend()
            plt.xticks(np.linspace(self.last_close * 0.75, self.last_close * 1.25, 11).round())
            plt.xlabel("Close Price", fontsize = 12)
            plt.ylabel("Total hits", fontsize = 12)
            plt.title(f"{self.symbol} - Total hits by Close price", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Total_hits_Close_Price.png"), 
                bbox_inches = "tight"
            )
            plt.close()

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

            plt.axvline(x = self.last_close, linestyle = "dashdot", color = "indianred", label = 'Last Close')
            plt.legend()
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

    def _create_daily_quarterly_features(self):
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

        self._save_quarterly_plots()
    
    def _save_quarterly_plots(self):
        quarterly_results = self.raw_data.groupby(
            [
                self.raw_data['Date'].dt.year,
                self.raw_data['Date'].dt.quarter
            ]
        ).agg(
            {
                "Is Green": lambda x: (sum(x) * 100)/ len(x),
                "Prev Close": "first",
                "Close": "last"
            }
        ).reset_index(
            names = ['Year', 'Quarter']
        ).sort_values(
            ['Year', 'Quarter']
        ).iloc[-21:]

        quarterly_results['Quarter Name'] = (
            "'" +
            quarterly_results['Year'].astype(str).str[2:] + 
            ' Q' +
            quarterly_results['Quarter'].astype(str)
        )

        quarterly_results['Returns'] = ((
            quarterly_results['Close'] / quarterly_results['Prev Close']
        ) - 1) * 100

        with sns.axes_style('dark'):
            plt.figure(figsize = (10, 5), dpi = 125)
            sns.lineplot(
                data = quarterly_results,
                x = "Quarter Name",
                y = "Is Green",
                marker = 'o'
            )
            plt.axhline(
                y = 50,
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "goldenrod"
            )

            plt.ylim((0, 100))
            plt.xticks(
                quarterly_results['Quarter Name'],
                rotation = 45,
                fontsize = 8
            )
            plt.xlabel("Calendar quarter", fontsize = 12)
            plt.ylabel("Percentage", fontsize = 12)
            plt.title(f"{self.symbol} - Percentage of green candles by calendar quarter", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Pcnt_Green_Candles_Quarter.png"), 
                bbox_inches = "tight"
            )
            plt.close()

            plt.figure(figsize = (10, 5), dpi = 125)
            sns.lineplot(
                data = quarterly_results,
                x = "Quarter Name",
                y = "Returns",
                marker = 'o'
            )
            plt.axhline(
                y = 0,
                linestyle = "dashdot",
                linewidth = 1.5,
                color = "goldenrod"
            )

            plt.xticks(
                quarterly_results['Quarter Name'],
                rotation = 45,
                fontsize = 8
            )
            plt.xlabel("Calendar quarter", fontsize = 12)
            plt.ylabel("Net return (%)", fontsize = 12)
            plt.title(f"{self.symbol} - Net returns by calendar quarter", fontsize = 14)
            plt.savefig(
                self.image_out_path.joinpath(f"{self.symbol}_Net_Returns_Candles_Quarter.png"), 
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

        last_candle_streaks = max_streaks[max_streaks['Is Green'] == self.last_candle]

        self.streak_cont_prob = last_candle_streaks[
            last_candle_streaks['Streak'] > self.candle_streak
        ].shape[0] / last_candle_streaks[
            last_candle_streaks['Streak'] >= self.candle_streak
        ].shape[0]

        longest_candle_streak = last_candle_streaks['Streak'].max()
        longest_candle_si = last_candle_streaks[
            last_candle_streaks['Streak'] == longest_candle_streak
        ]['Streak Index'].iloc[-1]
        self.longest_candle_streak: tuple[int, date, date] = (
            longest_candle_streak,
            self.raw_data['Date'][self.raw_data['Streak Index'] == longest_candle_si].min().date(),
            self.raw_data['Date'][self.raw_data['Streak Index'] == longest_candle_si].max().date()
        )

        if self.candle_streak >= 5:
            last_candle = "Green" if self.last_candle == 1 else "Red"
            self.highlights.append(
                f'<li>This stock is on a <span class="metric">{self.candle_streak}</span> day <span class="metric color-{last_candle.lower()}">{last_candle}</span> candle streak on a close by close basis.</li>'
            )

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

        if (self.raw_data['% Down from ATH'].iloc[-1] >= -2) or (self.raw_data['% Down from ATH'].iloc[-1] <= -50):
            self.highlights.append(
                f'<li>Currently, this stock is <span class="metric">{-self.raw_data["% Down from ATH"].iloc[-1]:.2f}%</span> away from its all time high.</li>'
            )

        self._save_ath_plots()

    def _save_ath_plots(self):
        with sns.axes_style('dark'):
            plot_data = self.raw_data[['Date', '% Down from ATH']].iloc[-1000:]

            plt.figure(figsize = (10, 5), dpi = 125)
            plt.axhline(y = 0, linestyle = "dashdot", color = "indianred", label = "ATH")
            
            sns.lineplot(
                plot_data,
                x = 'Date',
                y = '% Down from ATH'
            )

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