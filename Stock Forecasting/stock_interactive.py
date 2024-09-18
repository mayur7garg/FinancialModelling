import marimo

__generated_with = "0.8.15"
app = marimo.App(
    width="medium",
    layout_file="layouts/stock_interactive.grid.json",
)


@app.cell
def __():
    from datetime import date
    from pathlib import Path

    import pandas as pd
    import marimo as mo

    from utility import Config
    from data_process import StockData
    return Config, Path, StockData, date, mo, pd


@app.cell
def __(Config, Path):
    CONFIG = Config(Path("config.json"))
    STOCK_SYMBOLS = CONFIG.get_all_stock_symbols()
    return CONFIG, STOCK_SYMBOLS


@app.cell
def __(STOCK_SYMBOLS, mo):
    symbol = mo.ui.dropdown(
        options = STOCK_SYMBOLS,
        label = "Select symbol",
        value = STOCK_SYMBOLS[0]
    )

    symbol
    return symbol,


@app.cell
def __(mo, symbol):
    mo.md(f"# {symbol.value}")
    return


@app.cell
def __(CONFIG, StockData, symbol):
    stock_data = StockData(
        symbol.value, 
        CONFIG.NSE_DATA_DIR, 
        CONFIG.EPS_DATA_DIR,
        CONFIG.IMAGES_OUT_DIR,
        False
    )

    stock_data.create_features(
        performance_periods = [5, 15, 50, 200, 1000],
        sp_ma_periods = [list(range(1, 21)), list(range(5, 101, 5))]
    )

    raw_df = stock_data.raw_data
    print(f"Loaded {raw_df.shape[0]} records with data from {raw_df['Date'].min().date()} to {raw_df['Date'].max().date()}.")
    return raw_df, stock_data


@app.cell
def __(mo):
    mo.md("""## Stock data""")
    return


@app.cell
def __(raw_df):
    raw_df
    return


@app.cell
def __(mo):
    mo.md("""## Historical performance""")
    return


@app.cell
def __(pd, stock_data):
    perf_reports = pd.DataFrame(
        {
            "Period": [f"Last {perf.period_size} days" for perf in stock_data.perf_reports],
            "Start Date": [f"{perf.start_date:%B %d, %Y}" for perf in stock_data.perf_reports],
            "Net Returns": [f"{perf.net_returns:.2%}" for perf in stock_data.perf_reports],
            "Average Daily Return": [f"{perf.avg_daily_returns:.3%}" for perf in stock_data.perf_reports],
            "Average Close Price": [f"{perf.avg_close:.2f}" for perf in stock_data.perf_reports],
            "Lowest Close Price": [f"{perf.lowest_close:.2f}" for perf in stock_data.perf_reports],
            "Highest Close Price": [f"{perf.hightest_close:.2f}" for perf in stock_data.perf_reports],
        }
    )

    perf_reports
    return perf_reports,


@app.cell
def __(mo):
    mo.md("""## Average daily rolling returns""")
    return


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_Avg_Rolling_Returns_200.png")
    return


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_Avg_Rolling_Returns_1000.png")
    return


@app.cell
def __(mo):
    mo.md("""## Distribution of Close price""")
    return


@app.cell
def __(date, mo, stock_data):
    last_candle = "Green" if stock_data.last_candle == 1 else "Red"

    mo.md(f"""
    ### Last close price: {stock_data.last_close}
    ### Last candle: {last_candle}
    ### {stock_data.symbol} first closed above this last close price on {stock_data.first_hit_of_last_close:%A, %B %d, %Y} which was {(date.today() - stock_data.first_hit_of_last_close).days} days ago.
    ### Since then, it has closed over this price {stock_data.pcnt_hit_of_last_close:.1%} of times which is {stock_data.total_hits_of_last_close} trading days.
    """)
    return last_candle,


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_CDF_Close_Price.png")
    return


@app.cell
def __(mo):
    mo.md("""## Streaks by candle types""")
    return


@app.cell
def __(last_candle, mo, stock_data):
    mo.md(f"""
    ### Overall percentage of {last_candle} candles: {stock_data.last_candle_overall_pcnt:.1%}
    ### Current streak of {last_candle} candles: {stock_data.candle_streak}
    ### Net change so far for the current streak: {stock_data.curr_streak_returns:.2%}
    ### Probability of streak continuing: {stock_data.streak_cont_prob:.1%}
    """)
    return


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_Pcnt_Streak_Length.png")
    return


@app.cell
def __(mo):
    mo.md("""## Proportion by candle types""")
    return


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_Pcnt_Candles_Quarter.png")
    return


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_Pcnt_Candles_Year.png")
    return


@app.cell
def __(mo):
    mo.md("""## Spearman correlation over moving averages""")
    return


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_Close_Price_MA_S_1.png")
    return


@app.cell
def __(mo, symbol):
    mo.image(src = f"../web/images/{symbol.value}_Close_Price_MA_S_2.png")
    return


if __name__ == "__main__":
    app.run()
