# Project Overview

This project is an independent replication and adaptation of:

Zarattini, Carlo and Aziz, Andrew and Barbon, Andrea, Beat the Market An Effective Intraday Momentum Strategy for S&P500 ETF (SPY) (May 10, 2024). Swiss Finance Institute Research Paper No. 24-97, Available at SSRN: https://ssrn.com/abstract=4824172 or http://dx.doi.org/10.2139/ssrn.4824172  

The objective is to study the methodology proposed in the original paper, reproduce its main ideas and results where possible, and develop a personal Python implementation.

This project should not be considered an exact reproduction of the original study. The implementation may differ because of:

- different datasets or data providers;
- different sample periods or markets;
- alternative assumptions and parameter choices;
- transaction costs and execution constraints;
- modifications to the original methodology;
- additional robustness checks or extensions;

# How to Run

1. Clone the repository:

    git clone https://github.com/roman-terentiev/noise_area_mom

2. Get required dependencies in:

    runs/.../in/requirements.txt  

3. Install the required dependencies: 

    pip install -r requirements.txt 

4. Run the orchestrator:

    python main.py  

5. Results are stored in:

    runs/.../out/

# Data

Provider: https://databento.com/

Dataset: CME Globex MDP 3.0

Schema: ohlcv-1m

The raw market data used in this project are not included in this repository.

# Disclaimer

This repository is an independent research and educational project. It is not affiliated with or endorsed by the authors of the original paper. Any errors, interpretations, or modifications are my own.

The code and results are provided for research and educational purposes only and do not constitute financial or investment advice.