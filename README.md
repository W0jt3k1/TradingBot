# SPY Algorithmic Trading Bot

A Python-based algorithmic trading project combining machine learning, technical indicators, and automated order execution through the Alpaca API.

The bot uses a **Random Forest classifier** to estimate the probability of an upward price movement in SPY (SPDR S&P 500 ETF Trust). Based on this prediction, it dynamically adjusts portfolio exposure in a paper trading environment.

This is a personal, experimental project exploring the integration of machine learning with automated trading systems.

## Features

- **Machine learning predictions:** Uses a pre-trained Random Forest classifier to generate trading signals from hourly market data.
- **Technical indicators:** Calculates RSI, EMA distance, ATR, volume change, and price returns.
- **Dynamic position sizing:** Adjusts portfolio exposure based on the model's predicted probability.
- **Automated execution:** Places simulated buy and sell orders through the Alpaca API.
- **Fractional shares:** Supports position adjustments with fractional-share quantities.
- **Virtual portfolio tracking:** Maintains a locally tracked cash balance separate from the broker's account balance.
- **Monitoring:** Supports Discord notifications for trading events and errors.

## Machine Learning Model

The project uses a previously trained classification model saved as `model_volume_fixed.pkl`.

### Model specifications

| Property | Value |
|---|---|
| Algorithm | Random Forest Classifier |
| Library | scikit-learn |
| Training library version | 1.6.1 |
| Number of estimators | 300 |
| Input features | 5 |
| Prediction output | Class probabilities |

### Input features

| Feature | Description |
|---|---|
| `rsi` | Relative Strength Index (14 periods) |
| `dist_ema` | Relative distance between the closing price and the 50-period EMA |
| `atr` | Average True Range (14 periods) |
| `vol_change` | Percentage change in trading volume |
| `return` | Percentage change in closing price |

The trading script passes these features to the model in the specified order.

### Model availability and reproducibility

The trained model has been preserved locally, but the original Google Colab notebooks used for training are no longer available.

Consequently:

- The original training procedure cannot currently be reproduced.
- The exact training dataset and validation methodology are not documented.
- No verified out-of-sample performance metrics are available.
- The model's predictive performance and generalization have not been independently established.

The repository focuses on the trading application and inference pipeline rather than reproducible model training.

The serialized model file is not included in the public repository. Running the application requires a compatible local model file.

## Trading Strategy

The bot follows a confidence-based position allocation strategy.

After retrieving hourly SPY market data, it calculates technical indicators and passes them to the classifier. The probability assigned to the positive class is used to determine target portfolio exposure.

### Position allocation

| Model probability | Target allocation |
|---|---|
| Below 47% | 0% |
| 47%–83% | Linear increase from 0% to 100% |
| Above 83% | 100% |

The target position is compared with the currently held quantity. The bot then purchases additional shares, reduces the position, or leaves it unchanged.

These confidence thresholds are manually configured parameters and should not be interpreted as experimentally optimized values.

### Virtual Portfolio

The application initializes a local virtual cash balance of $10,000.

This balance is used to calculate the strategy's target exposure and is updated when orders are submitted.

The virtual portfolio is an internal accounting mechanism within the paper trading environment. It does not represent an independently reconciled brokerage subaccount.

## Technologies

- **Python** – application logic
- **scikit-learn** – Random Forest classifier
- **pandas / NumPy** – data processing
- **pandas-ta** – technical indicators
- **Alpaca API** – market data and paper trading
- **joblib** – model serialization
- **Discord Webhooks** – notifications

## Project Structure

```text
TradingBot/
├── multibot.py
├── requirements.txt
├── README.md
└── .gitignore
```

Additional local files required or created during execution:

```text
config.json             # API credentials and configuration
model_volume_fixed.pkl  # Pre-trained classification model
virtual_account.json    # Virtual cash balance
```

These files should not be committed if they contain sensitive information or private trading data.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/W0jt3k1/TradingBot.git
cd TradingBot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The preserved model was serialized using scikit-learn 1.6.1. Using a compatible scikit-learn environment is recommended, since serialized scikit-learn models are not guaranteed to work across library versions.

### 4. Configure Alpaca

Create a `config.json` file in the project directory:

```json
{
  "API_KEY": "YOUR_PAPER_API_KEY",
  "SECRET_KEY": "YOUR_PAPER_SECRET_KEY",
  "BASE_URL": "https://paper-api.alpaca.markets",
  "DISCORD_URL": null
}
```

Use paper trading credentials. Keep the configuration file out of version control.

### 5. Provide the model

Place the preserved model in the project directory as:

`model_volume_fixed.pkl`

The model must be compatible with the five expected features.

**Security note:** Serialized Python models can execute arbitrary code during deserialization. Only load model files from trusted sources.

### 6. Run the application

```bash
python multibot.py
```

The bot checks market status and performs analysis periodically while the market is open.

## Current Limitations

This project is an experimental prototype and has several limitations:

- The original training notebook is unavailable.
- No reproducible training pipeline or verified backtesting results are provided.
- The application does not include automated tests.
- The virtual cash balance is updated using estimated order values rather than confirmed execution prices.
- Backward filling during feature preparation can introduce future-data leakage into earlier observations.
- Model predictions are not guaranteed to produce profitable trading decisions.
- The application has not been validated for live trading with real funds.

## Potential Improvements

- Rebuild the model training pipeline with reproducible dataset preparation.
- Implement chronological train/validation/test splits and walk-forward evaluation.
- Compare Random Forest against simpler prediction baselines.
- Add backtesting with realistic transaction costs and slippage.
- Synchronize portfolio accounting with confirmed order executions.
- Add automated tests and structured logging.

## Disclaimer

This project is intended for educational and experimental purposes only.

The bot uses Alpaca's paper trading environment, where orders are simulated rather than executed with real funds.

No investment returns or predictive performance guarantees are claimed.

## Author

[W0jt3k1](https://github.com/W0jt3k1)
