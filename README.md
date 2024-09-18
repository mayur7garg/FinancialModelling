# Financial Modelling
Easy to follow stock price analysis on Indian stock data with results hosted at [GitHub Pages - FinancialModelling](https://mayur7garg.github.io/FinancialModelling/)

## Table of content

<details>
<summary>Click to expand</summary>

- [Data](#data)
- [Project Prerequisites](#project-prerequisites)
- [Usage](#usage)
- [Notes and Caveats](#notes-and-caveats)
- [About this project](#about-this-project)
</details>

## Data

### Sources
This project uses historical data acquired from publicly available sources listed below:

1. [NSE India](https://www.nseindia.com/) - Daily stock prices
2. [Screener.in](https://www.screener.in/) - Stock PE

### Update schedule
Stock pricing data is updated 3 times a week for a set of symbols via a [cron workflow](.github/workflows/main.yml) running on GitHub actions.

Updating PE data, however, is a manual process. Hence, PE information is not likely to be correct for recent dates and should not be relied upon.

## Project Prerequisites

### Docker
Development of this project was done inside a Docker container using the base image of `Python v3.11.6`. The same environment can be set up using the `docker-compose.yml` available [here](./docker-compose.yml).

If using VS Code or GitHub Codespaces, a developmental container can be instantiated using the [devcontainer.json](.devcontainer/devcontainer.json) file

### Requirements
All top level packages used in this project are listed in the [requirements](./requirements.txt) file. This project does not use any niche functionality from any of the listed packages and hence should work with their most recent releases.

## Usage

### Static reports
This project generates static HTML reports which are hosted using GitHub Pages which can be viewed at [FinancialModelling](https://mayur7garg.github.io/FinancialModelling/).

To regenerate the reports and the associated plots, run the following command:
```sh
cd 'Stock Forecasting' && python main.py
```

Once generated, the reports can be viewed by opening [index.html](index.html) in any web browser.

### Interactive notebook
An interactive [marimo](https://marimo.io/) notebook has been included which can be run using the following command:
```sh
cd 'Stock Forecasting' && marimo run stock_interactive.py
```

## Notes and Caveats
- This project is only meant to be educational and analytical purposes and should not be interpreted as a financial advice.
- This project only focuses on day level stock price data and does not factor in intraday price changes or company fundamentals.
- Data used in this project is not updated in realtime and may be out of date.
- Currently, the analysis doesn't factor in stock splits, bonus shares, etc. as structured data for the same is difficult to obtain.

## About this project

Feel free to leave a star if you liked this project.

```bibtex
@misc{MayurGarg_FinancialModelling,
    title={Financial Modelling},
    author={Mayur Garg},
    year={2024},
    url={https://github.com/mayur7garg/FinancialModelling}
}
```

> Developed by - Mayur Garg