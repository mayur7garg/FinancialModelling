import marimo

__generated_with = "0.18.0"
app = marimo.App(width="full")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    return Path, mo


@app.cell
def _(Path, mo):
    STOCK_SYMBOLS = [p.stem for p in Path("..", "..", "data", "NSE").iterdir() if p.is_dir()]
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
