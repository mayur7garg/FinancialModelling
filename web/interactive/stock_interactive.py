import marimo

__generated_with = "0.18.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    symbol = mo.ui.text(placeholder = "Enter symbol: ")
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
    mo.image(src = f"../images/{symbol.value}/{symbol.value}_Volume_density_by_VWAP.png")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

# marimo export html-wasm stock_interactive.py -o . --mode run