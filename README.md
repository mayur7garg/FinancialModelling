# Financial Modelling
Easy to follow stock price analysis on Indian stock data with results hosted at [GitHub Pages - FinancialModelling](https://mayur7garg.github.io/FinancialModelling/)

## Table of content

<details>
<summary>Click to expand</summary>

- [Data](#data)
- [Project Requirements](#project-requirements)
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