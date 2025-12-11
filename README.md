# 📈 AI Algorithmic Trader (SPY)

Profesjonalny bot tradingowy oparty na uczeniu maszynowym (Random Forest), zaprojektowany do handlu funduszem S&P 500 (SPY) na platformie Alpaca. System wykorzystuje zaawansowane zarządzanie ryzykiem, akcje ułamkowe oraz mechanizm wirtualnego subkonta do symulacji procentu składanego.

## 🚀 Główne Funkcje

* **Mózg AI:** Model `RandomForestClassifier` analizujący wskaźniki techniczne (RSI, EMA, ATR, Volume Change) w celu przewidywania kierunku ceny na następną godzinę.
* **Smart Rebalancing:** Dynamiczne dostosowywanie wielkości pozycji w oparciu o pewność modelu (Confidence Score).
    * *Min próg:* 47% (Start inwestycji)
    * *Max próg:* 83% (Pełna ekspozycja kapitału)
* **Fractional Shares (Ułamki Akcji):** Precyzja do 3 miejsc po przecinku (np. kupno 2.455 akcji), co eliminuje zjawisko "Cash Drag" i pozwala pracować całemu kapitałowi.
* **Wirtualne Subkonto (Compounding):** Unikalny mechanizm izolujący wyniki bota od reszty konta brokerskiego. Bot startuje z wirtualnym kapitałem (np. $10k) i automatycznie reinwestuje wypracowane zyski (efekt kuli śnieżnej).
* **Robust Data Pipeline:** System odporny na luki w danych (NaN) z darmowych feedów giełdowych (IEX), wykorzystujący backfilling.
* **System Alertów:** Powiadomienia na Discorda o transakcjach, błędach oraz krytycznym stanie konta.

## 🛠️ Technologie

* **Python 3.10+**
* `alpaca-trade-api` (Komunikacja z brokerem)
* `scikit-learn` (Silnik AI)
* `pandas` & `pandas-ta` (Analiza danych i wskaźniki)
* `joblib` (Obsługa modelu)

## ⚙️ Instalacja i Konfiguracja

1.  **Klonowanie repozytorium:**
    ```bash
    git clone [https://github.com/TwojNick/twoj-repo.git](https://github.com/TwojNick/twoj-repo.git)
    cd twoj-repo
    ```

2.  **Instalacja zależności:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Konfiguracja:**
    Stwórz plik `config.json` w głównym katalogu (nie wrzucaj go do repozytorium!):
    ```json
    {
        "API_KEY": "TWOJ_KLUCZ_ALPACA",
        "SECRET_KEY": "TWOJ_SEKRET_ALPACA",
        "BASE_URL": "[https://paper-api.alpaca.markets](https://paper-api.alpaca.markets)",
        "DISCORD_URL": "TWOJ_WEBHOOK_DISCORD"
    }
    ```

4.  **Model:**
    Upewnij się, że plik modelu `model_volume_fixed.pkl` znajduje się w katalogu projektu.

5.  **Uruchomienie:**
    ```bash
    python live_trader.py
    ```

## 📊 Strategia Zarządzania Ryzykiem

Bot nie działa binarnie (Kup/Sprzedaj). Wykorzystuje logikę **Delta Rebalancing**:
1.  Oblicza docelową wartość portfela na podstawie pewności AI.
2.  Porównuje ją z obecnym stanem posiadania.
3.  Jeśli różnica jest dodatnia -> **Dokupuje** (Scale In).
4.  Jeśli różnica jest ujemna -> **Redukuje** pozycję (Take Profit / Risk Reduction).
5.  Jeśli pewność spadnie poniżej 47% -> **Panic Sell** (Ucieczka do gotówki).

## 🛡️ Disclaimer (Ważne!)

Ten projekt służy wyłącznie celom edukacyjnym i badawczym. Autor nie ponosi odpowiedzialności za jakiekolwiek straty finansowe poniesione w wyniku używania tego oprogramowania. Algorytm jest testowany na środowisku Paper Trading. Pamiętaj, że przeszłe wyniki nie gwarantują przyszłych zysków.

## 📄 Licencja

Projekt objęty licencją **MIT License**. Możesz go dowolnie modyfikować i używać, pod warunkiem zachowania informacji o autorstwie i braku gwarancji.
