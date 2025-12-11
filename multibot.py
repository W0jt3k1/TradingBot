import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
import pandas as pd
import pandas_ta as ta
import numpy as np
import joblib
import time
import json
import os
import requests
import traceback
from datetime import datetime, timedelta

# --- KONFIGURACJA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
MODEL_FILE = os.path.join(BASE_DIR, 'model_volume_fixed.pkl')
STATE_FILE = os.path.join(BASE_DIR, 'virtual_account.json') # Plik subkonta
SYMBOLS = ['SPY'] 

# === USTAWIENIA STRATEGII ===
MIN_CONFIDENCE = 0.47      
MAX_CONFIDENCE_CAP = 0.83
STARTING_CAPITAL = 10000.0 # Wirtualny start
CRITICAL_BALANCE_THRESHOLD = 100.0 # Alarmuj jeśli na Alpaca jest mniej niż $100

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Brak pliku {CONFIG_FILE}!")
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Błąd pliku JSON: {e}")
        return None

config = load_config()
if config is None: exit()

API_KEY = config['API_KEY']
SECRET_KEY = config['SECRET_KEY']
BASE_URL = config['BASE_URL']
DISCORD_URL = config.get('DISCORD_URL', None)

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

# --- ZARZĄDZANIE SUBKONTEM ---
def get_virtual_cash():
    if not os.path.exists(STATE_FILE):
        initial_state = {"virtual_cash": STARTING_CAPITAL}
        with open(STATE_FILE, 'w') as f:
            json.dump(initial_state, f)
        return STARTING_CAPITAL
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            return float(data.get("virtual_cash", STARTING_CAPITAL))
    except:
        return STARTING_CAPITAL

def update_virtual_cash(change_amount):
    current_cash = get_virtual_cash()
    new_cash = current_cash + change_amount
    with open(STATE_FILE, 'w') as f:
        json.dump({"virtual_cash": new_cash}, f)
    return new_cash

def notify(message):
    print(message)
    if DISCORD_URL:
        try:
            requests.post(DISCORD_URL, json={"content": message})
        except: pass

def get_market_data(symbol):
    try:
        bars = api.get_bars(symbol, TimeFrame.Hour, limit=500, feed='iex').df
        if bars.empty: return None
        if not isinstance(bars.index, pd.DatetimeIndex):
            bars.index = pd.to_datetime(bars.index)
        return bars
    except Exception as e:
        print(f"⚠️ Błąd pobierania {symbol}: {e}")
        return None

def prepare_features(df):
    df = df.copy()
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['ema_50'] = ta.ema(df['close'], length=50)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['vol_change'] = df['volume'].pct_change()
    df['dist_ema'] = (df['close'] - df['ema_50']) / df['ema_50']
    df['return'] = df['close'].pct_change()
    
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(method='bfill', inplace=True)
    df.fillna(0, inplace=True)
    return df

def get_position_qty(symbol):
    try:
        pos = api.get_position(symbol)
        return float(pos.qty)
    except:
        return 0.0

def calculate_target_qty(confidence, price, virtual_equity):
    if confidence < MIN_CONFIDENCE:
        return 0.0, 0.0
    
    ratio = (confidence - MIN_CONFIDENCE) / (MAX_CONFIDENCE_CAP - MIN_CONFIDENCE)
    if ratio > 1.0: ratio = 1.0
    if ratio < 0.0: ratio = 0.0
    
    target_equity = virtual_equity * ratio
    target_qty = round(target_equity / price, 3)
    
    return target_qty, ratio

def handle_trade(symbol, proba, current_price):
    current_qty = get_position_qty(symbol)
    
    # Stan wirtualny
    virtual_cash = get_virtual_cash()
    current_stock_value = current_qty * current_price
    virtual_equity = virtual_cash + current_stock_value
    
    # Stan fizyczny (Alpaca)
    try:
        account = api.get_account()
        real_cash = float(account.buying_power)
        
        # --- BEZPIECZNIK: Sprawdzenie stanu konta ---
        if real_cash < CRITICAL_BALANCE_THRESHOLD:
            notify(f"⚠️ **ALARM: NISKI STAN KONTA ALPACA!** Dostępne tylko: ${real_cash:.2f}")
    except:
        real_cash = 0.0

    # Obliczenie celu
    target_qty, ratio = calculate_target_qty(proba, current_price, virtual_equity)
    
    # Sprawdzenie czy fizycznie nas stać
    limit_hit = False
    if target_qty > current_qty:
        cost = (target_qty - current_qty) * current_price
        
        if cost > real_cash:
            # Obliczamy ile maksymalnie możemy kupić
            buyable_qty = round(real_cash / current_price, 3) * 0.995 
            
            # Jeśli brakuje środków na pełną realizację planu
            notify(f"⛔ **BRAK ŚRODKÓW:** Chciałem kupić za ${cost:.0f}, ale na koncie jest ${real_cash:.2f}.")
            notify(f"   Dostosowuję zakup do dostępnej gotówki...")
            
            target_qty = current_qty + buyable_qty
            target_qty = round(target_qty, 3)
            limit_hit = True

    delta = target_qty - current_qty
    delta = round(delta, 3)
    
    if abs(delta) < 0.001: delta = 0

    print(f"   📊 {symbol}: Pewność {proba:.1%}")
    print(f"      💰 Subkonto: ${virtual_equity:.2f} (Cash: ${virtual_cash:.2f})")
    print(f"      🎯 Cel: {target_qty:.3f} szt. {'(Ograniczony budżetem!)' if limit_hit else ''}")

    # --- EGZEKUCJA ---
    
    if proba < MIN_CONFIDENCE:
        if current_qty > 0.001:
            api.close_position(symbol)
            revenue = current_qty * current_price
            update_virtual_cash(revenue)
            notify(f"🔴 **ZAMYKAM {symbol}** (Pewność {proba:.1%} < Min).")
            notify(f"   Sprzedano: {current_qty:.3f} szt. | Portfel: ${virtual_equity:.2f}")
        else:
            print(f"   ⚪ {symbol}: Czekam (Słaby sygnał).")
            
    else:
        if delta == 0:
            print(f"   🟢 {symbol}: Pozycja idealna. Trzymam.")
            
        elif delta > 0:
            cost = delta * current_price
            if cost > 1.0:
                if real_cash < cost and not limit_hit: 
                     # Podwójne zabezpieczenie, gdyby buyable_qty źle policzyło
                     notify(f"❌ Błąd krytyczny: Brak środków na zakup (Wymagane ${cost:.2f}).")
                     return

                notify(f"🔵 **KUPNO {symbol}** (+{delta:.3f} szt)")
                notify(f"   Koszt: ${cost:.2f} | Portfel: ${virtual_equity:.2f} (Ekspozycja: {ratio:.1%})")
                
                try:
                    api.submit_order(symbol=symbol, qty=delta, side='buy', type='market', time_in_force='day')
                    update_virtual_cash(-cost) 
                except Exception as e:
                    notify(f"❌ Błąd API przy zakupie: {e}")

            else:
                print(f"   Info: Zmiana zbyt mała (${cost:.2f}), pomijam.")

        elif delta < 0:
            sell_qty = abs(delta)
            est_value = sell_qty * current_price
            if est_value > 1.0:
                notify(f"🟠 **REDUKCJA {symbol}** (-{sell_qty:.3f} szt)")
                notify(f"   Wartość: ${est_value:.2f} | Portfel: ${virtual_equity:.2f}")
                
                try:
                    api.submit_order(symbol=symbol, qty=sell_qty, side='sell', type='market', time_in_force='day')
                    update_virtual_cash(est_value)
                except Exception as e:
                    notify(f"❌ Błąd API przy sprzedaży: {e}")
            else:
                print(f"   Info: Redukcja zbyt mała (${est_value:.2f}), pomijam.")

def run_analysis():
    print(f"\n🔍 --- ANALIZA SUB-KONTA: {datetime.now().strftime('%H:%M')} ---")
    
    try:
        model = joblib.load(MODEL_FILE)
    except Exception as e:
        notify(f"❌ Błąd modelu: {e}")
        return

    for symbol in SYMBOLS:
        try:
            raw_data = get_market_data(symbol)
            if raw_data is None: continue
            
            data = prepare_features(raw_data)
            if len(data) == 0: continue

            last_row = data.iloc[[-1]]
            features = ['rsi', 'dist_ema', 'atr', 'vol_change', 'return']
            
            if not all(col in last_row.columns for col in features):
                print(f"   ⚠️ Brakujące kolumny: {list(last_row.columns)}")
                continue

            X_live = last_row[features]
            current_price = float(last_row['close'].iloc[0])
            
            proba = model.predict_proba(X_live)[:, 1][0]
            
            handle_trade(symbol, proba, current_price)
            
        except Exception as e:
            print(f"❌ Błąd analizy {symbol}: {e}")
            traceback.print_exc()

def wait_for_next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    next_run = next_hour + timedelta(seconds=30)
    seconds = (next_run - now).total_seconds()
    if seconds < 0: seconds = 60
    print(f"💤 Czekam do {next_run.strftime('%H:%M:%S')}")
    time.sleep(seconds)

if __name__ == "__main__":
    notify(f"🚀 Bot PRO: Subkonto + Alerty. Start: ${STARTING_CAPITAL}")
    while True:
        try:
            clock = api.get_clock()
            if clock.is_open:
                run_analysis()
                wait_for_next_hour()
            else:
                print("Giełda zamknięta.")
                time_to_open = (clock.next_open - clock.timestamp).total_seconds()
                sleep_time = 3600 if time_to_open > 3600 else time_to_open + 60
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"⚠️ Błąd pętli: {e}")
            time.sleep(60)