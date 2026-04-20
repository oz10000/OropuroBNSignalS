"""
Microstructural Volume Intelligent Engine – Lightweight Mobile Execution
=======================================================================
Single-file, REST-based, multi-exchange (Binance > Bybit > KuCoin).
Now with persistent storage integration.
"""

import json
import math
import statistics
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import storage  # <-- NEW persistent storage

# -----------------------------------------------------------------------------
# Minimal HTTP client (uses requests if available, else urllib fallback)
# -----------------------------------------------------------------------------
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    import urllib.parse
    _HAS_REQUESTS = False


def _http_get(url: str, timeout: int = 10) -> Optional[bytes]:
    if _HAS_REQUESTS:
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            return None
    else:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            return None
    return None


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
MAX_SPREAD_BPS = 15.0
MIN_OBI_THRESHOLD = 0.12
MIN_EPS_THRESHOLD = 0.18
ATR_PERIOD = 14
MOMENTUM_PERIOD = 20
TOP_VOLUME_LIMIT = 100

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
                   "ADAUSDT", "MATICUSDT", "LINKUSDT", "AVAXUSDT", "LTCUSDT"]


# -----------------------------------------------------------------------------
# Exchange connectors (REST only) - same as before, omitted for brevity
# ... (full implementations of BinanceREST, BybitREST, KuCoinREST)
# -----------------------------------------------------------------------------
# (For brevity I'll include a condensed version; in final code they are identical to previous core.py)
class ExchangeBase:
    def fetch_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]: pass
    def fetch_orderbook(self, symbol: str, depth: int = 20) -> Optional[Dict]: pass
    def fetch_trades(self, symbol: str, limit: int = 200) -> List[Dict]: pass
    def fetch_24hr_tickers(self) -> List[Dict]: pass


class BinanceREST(ExchangeBase):
    BASE = "https://api.binance.com"
    def fetch_klines(self, symbol, interval="5m", limit=100):
        url = f"{self.BASE}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        data = _http_get(url)
        if not data: return []
        try: raw = json.loads(data)
        except: return []
        candles = []
        for c in raw:
            candles.append({"time": c[0]//1000, "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": float(c[5])})
        return candles
    def fetch_orderbook(self, symbol, depth=20):
        url = f"{self.BASE}/api/v3/depth?symbol={symbol}&limit={depth}"
        data = _http_get(url)
        if not data: return None
        try:
            raw = json.loads(data)
            bids = [(float(p), float(q)) for p,q in raw["bids"]]
            asks = [(float(p), float(q)) for p,q in raw["asks"]]
            return {"bids": bids, "asks": asks}
        except: return None
    def fetch_trades(self, symbol, limit=200):
        url = f"{self.BASE}/api/v3/trades?symbol={symbol}&limit={limit}"
        data = _http_get(url)
        if not data: return []
        try: raw = json.loads(data)
        except: return []
        trades = []
        for t in raw:
            trades.append({"price": float(t["price"]), "qty": float(t["qty"]), "time": t["time"]//1000, "isBuyerMaker": t["isBuyerMaker"]})
        return trades
    def fetch_24hr_tickers(self):
        url = f"{self.BASE}/api/v3/ticker/24hr"
        data = _http_get(url)
        if not data: return []
        try: raw = json.loads(data)
        except: return []
        tickers = []
        for t in raw:
            if t["symbol"].endswith("USDT"):
                tickers.append({"symbol": t["symbol"], "volume": float(t["quoteVolume"]), "bid": float(t["bidPrice"]), "ask": float(t["askPrice"])})
        return tickers


class BybitREST(ExchangeBase):
    BASE = "https://api.bybit.com"
    def fetch_klines(self, symbol, interval="5", limit=100):
        url = f"{self.BASE}/v5/market/kline?category=spot&symbol={symbol}&interval={interval}&limit={limit}"
        data = _http_get(url)
        if not data: return []
        try:
            raw = json.loads(data)
            if raw["retCode"] != 0: return []
            candles = []
            for c in raw["result"]["list"]:
                candles.append({"time": int(c[0])//1000, "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": float(c[5])})
            candles.reverse()
            return candles
        except: return []
    def fetch_orderbook(self, symbol, depth=20):
        url = f"{self.BASE}/v5/market/orderbook?category=spot&symbol={symbol}&limit={depth}"
        data = _http_get(url)
        if not data: return None
        try:
            raw = json.loads(data)
            if raw["retCode"] != 0: return None
            bids = [(float(p), float(q)) for p,q in raw["result"]["bids"]]
            asks = [(float(p), float(q)) for p,q in raw["result"]["asks"]]
            return {"bids": bids, "asks": asks}
        except: return None
    def fetch_trades(self, symbol, limit=200):
        url = f"{self.BASE}/v5/market/recent-trade?category=spot&symbol={symbol}&limit={limit}"
        data = _http_get(url)
        if not data: return []
        try:
            raw = json.loads(data)
            if raw["retCode"] != 0: return []
            trades = []
            for t in raw["result"]["list"]:
                trades.append({"price": float(t["price"]), "qty": float(t["size"]), "time": int(t["time"])//1000, "side": t["side"]})
            trades.reverse()
            return trades
        except: return []
    def fetch_24hr_tickers(self):
        url = f"{self.BASE}/v5/market/tickers?category=spot"
        data = _http_get(url)
        if not data: return []
        try:
            raw = json.loads(data)
            if raw["retCode"] != 0: return []
            tickers = []
            for t in raw["result"]["list"]:
                if t["symbol"].endswith("USDT"):
                    tickers.append({"symbol": t["symbol"], "volume": float(t["turnover24h"]), "bid": float(t["bid1Price"]), "ask": float(t["ask1Price"])})
            return tickers
        except: return []


class KuCoinREST(ExchangeBase):
    BASE = "https://api.kucoin.com"
    def fetch_klines(self, symbol, interval="5min", limit=100):
        url = f"{self.BASE}/api/v1/market/candles?type={interval}&symbol={symbol}&limit={limit}"
        data = _http_get(url)
        if not data: return []
        try:
            raw = json.loads(data)
            if raw["code"] != "200000": return []
            candles = []
            for c in raw["data"]:
                candles.append({"time": int(c[0]), "open": float(c[1]), "close": float(c[2]), "high": float(c[3]), "low": float(c[4]), "volume": float(c[5])})
            candles.reverse()
            return candles
        except: return []
    def fetch_orderbook(self, symbol, depth=20):
        url = f"{self.BASE}/api/v1/market/orderbook/level2_{depth}?symbol={symbol}"
        data = _http_get(url)
        if not data: return None
        try:
            raw = json.loads(data)
            if raw["code"] != "200000": return None
            bids = [(float(p), float(q)) for p,q in raw["data"]["bids"]]
            asks = [(float(p), float(q)) for p,q in raw["data"]["asks"]]
            return {"bids": bids, "asks": asks}
        except: return None
    def fetch_trades(self, symbol, limit=200):
        url = f"{self.BASE}/api/v1/market/histories?symbol={symbol}&limit={limit}"
        data = _http_get(url)
        if not data: return []
        try:
            raw = json.loads(data)
            if raw["code"] != "200000": return []
            trades = []
            for t in raw["data"]:
                trades.append({"price": float(t["price"]), "qty": float(t["size"]), "time": int(t["time"])//1000000000, "side": t["side"]})
            return trades
        except: return []
    def fetch_24hr_tickers(self):
        url = f"{self.BASE}/api/v1/market/allTickers"
        data = _http_get(url)
        if not data: return []
        try:
            raw = json.loads(data)
            if raw["code"] != "200000": return []
            tickers = []
            for t in raw["data"]["ticker"]:
                if t["symbol"].endswith("USDT"):
                    tickers.append({"symbol": t["symbol"], "volume": float(t["volValue"]), "buy": float(t["buy"]), "sell": float(t["sell"])})
            return tickers
        except: return []


# -----------------------------------------------------------------------------
# Fallback exchange manager
# -----------------------------------------------------------------------------
class ExchangeManager:
    def __init__(self):
        self.exchanges = [("binance", BinanceREST()), ("bybit", BybitREST()), ("kucoin", KuCoinREST())]
        self.universe = self._build_universe()

    def _build_universe(self):
        symbols = set()
        for name, ex in self.exchanges[:2]:
            tickers = ex.fetch_24hr_tickers()
            if not tickers: continue
            sorted_tickers = sorted(tickers, key=lambda x: x["volume"], reverse=True)[:TOP_VOLUME_LIMIT]
            symbols.update(t["symbol"] for t in sorted_tickers)
        symbols.update(DEFAULT_SYMBOLS)
        return list(symbols)

    def get_klines(self, symbol, interval, limit=100):
        for name, ex in self.exchanges:
            klines = ex.fetch_klines(symbol, interval, limit)
            if klines: return name, klines
        return "", []

    def get_orderbook(self, symbol, depth=20):
        for name, ex in self.exchanges:
            ob = ex.fetch_orderbook(symbol, depth)
            if ob: return name, ob
        return "", None

    def get_trades(self, symbol, limit=200):
        for name, ex in self.exchanges:
            trades = ex.fetch_trades(symbol, limit)
            if trades: return name, trades
        return "", []


# -----------------------------------------------------------------------------
# Feature engineering (same as before)
# -----------------------------------------------------------------------------
def compute_obi(orderbook): pass  # ... (implemented identically)
def compute_tfi(trades): pass
def compute_spread_bps(orderbook): pass
def compute_momentum(klines, period=MOMENTUM_PERIOD): pass
def compute_atr(klines, period=ATR_PERIOD): pass
def check_alignment(klines_5m, klines_1h): pass
def _ema(values, period): pass

# (For brevity, I'll include stubs; in final code they are identical to previous core.py)
def compute_obi(orderbook):
    bid_vol = sum(q for _, q in orderbook["bids"])
    ask_vol = sum(q for _, q in orderbook["asks"])
    total = bid_vol + ask_vol
    return (bid_vol - ask_vol) / total if total > 0 else 0.0

def compute_tfi(trades):
    buy_vol = sell_vol = 0.0
    for t in trades:
        qty = t.get("qty", 0.0)
        if "isBuyerMaker" in t:
            if not t["isBuyerMaker"]: buy_vol += qty
            else: sell_vol += qty
        elif "side" in t:
            if t["side"].lower() == "buy": buy_vol += qty
            else: sell_vol += qty
    total = buy_vol + sell_vol
    return (buy_vol - sell_vol) / total if total > 0 else 0.0

def compute_spread_bps(orderbook):
    if not orderbook["bids"] or not orderbook["asks"]: return 0.0
    best_bid = orderbook["bids"][0][0]
    best_ask = orderbook["asks"][0][0]
    mid = (best_bid + best_ask) / 2
    return (best_ask - best_bid) / mid * 10000 if mid > 0 else 0.0

def compute_momentum(klines, period=MOMENTUM_PERIOD):
    if len(klines) <= period: return 0.0
    return (klines[-1]["close"] - klines[-period]["close"]) / klines[-period]["close"]

def compute_atr(klines, period=ATR_PERIOD):
    if len(klines) < period + 1: return 0.01
    tr_values = []
    for i in range(1, len(klines)):
        h = klines[i]["high"]
        l = klines[i]["low"]
        pc = klines[i-1]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_values.append(tr)
    return sum(tr_values[-period:]) / period

def check_alignment(klines_5m, klines_1h):
    if len(klines_5m) < 5 or len(klines_1h) < 3: return False
    close_5m = [c["close"] for c in klines_5m]
    close_1h = [c["close"] for c in klines_1h]
    ema5_5m = _ema(close_5m, 5)
    ema20_5m = _ema(close_5m, 20)
    ema5_1h = _ema(close_1h, 5)
    ema20_1h = _ema(close_1h, 20)
    trend_5m = ema5_5m > ema20_5m
    trend_1h = ema5_1h > ema20_1h
    return trend_5m == trend_1h

def _ema(values, period):
    if len(values) < period: return values[-1] if values else 0.0
    k = 2.0 / (period + 1)
    ema = values[0]
    for v in values[1:]: ema = v * k + ema * (1 - k)
    return ema


# -----------------------------------------------------------------------------
# Edge Score & Filters
# -----------------------------------------------------------------------------
class EdgeCalculator:
    @staticmethod
    def compute(features):
        obi = abs(features.get("obi", 0))
        tfi = abs(features.get("tfi", 0))
        spread = features.get("spread", MAX_SPREAD_BPS)
        momentum = abs(features.get("momentum", 0))
        aligned = features.get("aligned_htf", False)
        score = 0.0
        score += min(obi * 3.0, 1.0) * 0.30
        score += min(tfi * 3.0, 1.0) * 0.20
        score += max(0.0, 1.0 - spread / 30.0) * 0.20
        score += min(momentum * 50.0, 1.0) * 0.20
        if aligned: score += 0.10
        return min(score, 1.0)

class SignalFilters:
    @staticmethod
    def passes(features):
        obi = abs(features.get("obi", 0))
        tfi = abs(features.get("tfi", 0))
        spread = features.get("spread", MAX_SPREAD_BPS + 1)
        eps = obi * 0.4 + tfi * 0.4
        if spread > MAX_SPREAD_BPS: return False
        if obi < MIN_OBI_THRESHOLD: return False
        if eps < MIN_EPS_THRESHOLD: return False
        return True

class WalkForward:
    def __init__(self): self.params = defaultdict(lambda: {"obi": MIN_OBI_THRESHOLD, "eps": MIN_EPS_THRESHOLD})
    def get(self, symbol): p = self.params[symbol]; return p["obi"], p["eps"]

class CorrelationFilter:
    CLUSTERS = [{"BTCUSDT","ETHUSDT","SOLUSDT"}, {"BNBUSDT","MATICUSDT","LINKUSDT","AVAXUSDT"}]
    def allow(self, selected, candidate):
        for cluster in self.CLUSTERS:
            if selected in cluster and candidate in cluster: return False
        return True

class SingleAssetSelector:
    def __init__(self):
        self.calc = EdgeCalculator()
        self.filters = SignalFilters()
        self.corr = CorrelationFilter()
        self.wf = WalkForward()
    def select(self, market_features):
        best_symbol = None
        best_score = -1.0
        best_feat = None
        for sym, feat in market_features.items():
            if not self.filters.passes(feat): continue
            obi_thr, _ = self.wf.get(sym)
            if abs(feat["obi"]) < obi_thr: continue
            score = self.calc.compute(feat)
            if score > best_score:
                if best_symbol is None or self.corr.allow(best_symbol, sym):
                    best_symbol = sym
                    best_score = score
                    best_feat = feat.copy()
                    best_feat["score"] = score
        if best_symbol: return best_symbol, best_feat
        return None


# -----------------------------------------------------------------------------
# Main Scanner Runner (now with persistent storage)
# -----------------------------------------------------------------------------
_SELECTOR = SingleAssetSelector()
_EXCHANGE_MGR = ExchangeManager()


def run_scanner():
    now = datetime.utcnow()
    universe = _EXCHANGE_MGR.universe
    market_features = {}

    for sym in universe:
        ex_name, klines_5m = _EXCHANGE_MGR.get_klines(sym, "5m", 100)
        if not klines_5m: continue
        ex_name, klines_1h = _EXCHANGE_MGR.get_klines(sym, "1h", 100)
        if not klines_1h: continue
        ex_name, orderbook = _EXCHANGE_MGR.get_orderbook(sym, 20)
        if not orderbook: continue
        ex_name, trades = _EXCHANGE_MGR.get_trades(sym, 200)
        if not trades: continue

        obi = compute_obi(orderbook)
        tfi = compute_tfi(trades)
        spread = compute_spread_bps(orderbook)
        momentum = compute_momentum(klines_5m)
        atr = compute_atr(klines_5m)
        aligned = check_alignment(klines_5m, klines_1h)

        market_features[sym] = {
            "obi": obi,
            "tfi": tfi,
            "spread": spread,
            "momentum": momentum,
            "atr": atr,
            "aligned_htf": aligned,
            "exchange": ex_name
        }

    result = _SELECTOR.select(market_features)

    if result is not None:
        sym, feat = result
        direction = "LONG" if feat["momentum"] > 0 else "SHORT"
        signal_data = {
            "timestamp": now.isoformat() + "Z",
            "exchange": feat.get("exchange", "UNKNOWN"),
            "symbol": sym,
            "direction": direction,
            "score": round(feat["score"], 3),
            "expected_move": round(feat["atr"] * 1.2, 2)
        }
        storage.record_signal(signal_data)  # <-- PERSISTENCE
        time_since = storage.get_time_since_last_signal()
        est_next = storage.get_estimated_next_signal()
        return {
            **signal_data,
            "time_since_last_signal_min": round(time_since, 1),
            "estimated_time_to_next_signal_min": round(est_next, 1),
            "status": "SIGNAL"
        }
    else:
        time_since = storage.get_time_since_last_signal()
        est_next = storage.get_estimated_next_signal()
        return {
            "timestamp": now.isoformat() + "Z",
            "status": "NO SIGNAL",
            "time_since_last_signal_min": round(time_since, 1),
            "estimated_time_to_next_signal_min": round(est_next, 1)
        }
