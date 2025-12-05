import marimo

__generated_with = "0.18.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    STOCK_SYMBOLS = ['ADANIPOWER', 'BHARTIARTL', 'BSOFT', 'DEEPAKFERT', 'DLF', 'GOKULAGRO', 'GOLDBEES', 'HAL', 'HDFCBANK', 'HDFCSML250', 'ICICIBANK', 'INDIGO', 'INDIGOPNTS', 'INFY', 'ITBEES', 'ITC', 'JSWSTEEL', 'JUBLFOOD', 'JUNIORBEES', 'LIQUIDCASE', 'MARUTI', 'MID150BEES', 'MON100', 'NH', 'NIFTYBEES', 'PAGEIND', 'RBA', 'SILVERBEES', 'TANLA', 'TCS', 'TMPV', 'VEDL', 'WAAREEENER']
    symbol = mo.ui.dropdown(
        STOCK_SYMBOLS,
        value = STOCK_SYMBOLS[0],
        label = "Select symbol"
    )
    symbol
    return (symbol,)


@app.cell
def _(mo, symbol):
    mo.md(f"""
    # {symbol.value}
    """)
    return


@app.cell
def _(mo, symbol):
    mo.image(src = f"../images/{symbol.value}/{symbol.value}_Max_Period_of_No_Return.png")
    return


@app.cell
def _(mo, symbol):
    mo.image(src = f"../images/{symbol.value}/{symbol.value}_Volume_by_VWAP.png")
    return


@app.cell
def _():
    # marimo export html-wasm stock_interactive.py -o . --mode run
    return


if __name__ == "__main__":
    app.run()
