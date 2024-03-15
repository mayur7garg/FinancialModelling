# Financial Modelling
> Easy to follow stock price analysis forecasting techniques on Indian stock data

## Table of content

<details>
<summary>Click to expand</summary>

- [Data](#data)
- [Project Requirements](#project-requirements)
- [Modelling](#modelling)
- [Notes and Caveats](#notes-and-caveats)
- [About this project](#about-this-project)
</details>

## Data
This project uses historical data acquired from publicly available sources listed below:

1. [NSE India](https://www.nseindia.com/)
2. [Screener.in](https://www.screener.in/)

## Project Requirements

### Docker
Development of this project was done inside a developmental Docker container using the base image of `Python v3.11.6`. The same environment can be set up using the `docker-compose.yml` available [here](./docker-compose.yml).

### Requirements
All top level packages used in this project are listed in the [requirements](./requirements.txt) file. This project does not use any niche functionality from any of the listed packages and hence should work with their most recent releases.

## Modelling
The code in this project consists primarily of notebooks with some utility code available as scripts. Currently, there are 5 notebooks as described below:

### 1. Data Consolidation
- Consolidates historical and PE data from multiple years for each available stock ticker symbol into a parquet file
- Must be run once before any of the following notebooks

### 2. Data Processing
- Performs data processing on the consolidated data and generates new features for analysis and forecasting such as:
    - Candle ranges
    - Whether the candle is green or red
    - Running streak
    - Moving averages over multiple periods for fields such as stock prices, volumes and number of trades
- Generates two parquet files for each ticker symbol:
    - `processed` - Original data with new features. Primarily used for analysis.
    - `standardized` - Features standardized to denote percentage changes within the same row. Primarily used for forecasting.
- Must be run for each available `STOCK_SYMBOL` once before any of the following notebooks

### 3. EDA
- Exploratory data analysis using various visualisations
- Analysis is divided into 3 sections:
    - **Historical** - Descriptive, cumulative and grouped statistics over the entire historical data such as:
        - `Close` price CDF
        - Proportion of candle types by year and quarter
        - Normalized candle size by type, year and quarter
        - Streaks of green and red candles and their overall distribution
    - **Current** - Analysis of the most recent stock prices such as:
        - The time when the latest price was first reached
        - Momentum using ADAM for past few trading days
    - **Trends** - Overall trend of various features over the entire period

### 4. Forecasting using Random Forests
- Stock price forecasting for multiple time periods using `RandomForestRegressor`
- Data for each day is assumed to be independent and an individual data point
- All models are hyperparameter tuned for best performance

### 5. Quantile forecasting using Gradient Boosted Trees
- Stock price forecasting for multiple time periods using `GradientBoostingRegressor`
- Lower and upper bounds are also calculated using Quantile regression
- Data for each day is assumed to be independent and an individual data point
- All models are hyperparameter tuned for best performance

## Notes and Caveats
- This project only focuses on day level stock price data and does not factor in intraday price changes.
- Currently, the analysis doesn't factor in stock splits, bonus shares, etc. as structured data for the same is difficult to obtain.
- This project is only meant to be educational and should not be interpreted as a financial advice.

## About this project

```bibtex
@misc{MayurGarg_FinancialModelling,
    title={Financial Modelling},
    author={Mayur Garg},
    year={2024},
    url={https://github.com/mayur7garg/FinancialModelling}
}
```

> Developed by - Mayur Garg