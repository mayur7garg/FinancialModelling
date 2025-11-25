import marimo

__generated_with = "0.18.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    import sys
    mo.md(sys.executable)
    return


@app.cell
def _(mo):
    s = mo.ui.text()
    s
    return (s,)


@app.cell
def _(mo, s):
    mo.md(s.value)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
