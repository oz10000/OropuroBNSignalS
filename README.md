# OroPuro

**OroPuro** es un sistema probabilístico de escaneo de mercado basado en microestructura. Analiza en tiempo real los principales pares USDT de Binance, Bybit y KuCoin, seleccionando aquel con mayor probabilidad estadística de movimiento direccional a corto plazo.

**OroPuro** is a probabilistic market scanning system based on microstructure. It analyzes top USDT pairs from Binance, Bybit, and KuCoin in real time, selecting the one with the highest statistical likelihood of short‑term directional movement.

---

## 🧠 How it works / Cómo funciona

1. **Obtiene datos** de los exchanges (orden de prioridad: Binance → Bybit → KuCoin).
2. **Calcula características** microestructurales:
   - Order Book Imbalance (OBI)
   - Trade Flow Imbalance (TFI)
   - Spread
   - Momentum
   - ATR
   - Alineación multi‑timeframe (5m vs 1h)
3. **Filtra** los activos que no cumplen criterios mínimos de liquidez, spread y presión de ejecución.
4. **Calcula un Edge Score (0‑1)** para cada activo válido.
5. **Selecciona el mejor activo** (single‑asset), evitando correlaciones redundantes.
6. **Estima tiempos** entre señales basándose en el historial reciente.

El modelo **no predice** el futuro; simplemente identifica configuraciones donde el desequilibrio de órdenes y el flujo de trades han mostrado, históricamente, una ventaja estadística.

---

## 📤 Output / Salida

Cada ejecución manual devuelve:

- Estado: `SIGNAL` o `NO SIGNAL`
- Si hay señal:
  - Símbolo
  - Dirección (LONG/SHORT)
  - Score (0‑1)
  - Exchange utilizado
  - Take Profit y Stop Loss sugeridos (basados en ATR)
- Métricas de tiempo:
  - Minutos desde la última señal
  - Estimación de minutos hasta la próxima señal

---

## 📊 Trading Logic / Lógica de Trading

- **No es predictivo.** Es un filtro de oportunidades con edge estadístico.
- **Gestión recomendada:**
  - Riesgo por trade: **1‑2%** del capital.
  - Apalancamiento sugerido: **x3 – x5**.
  - Apalancamiento máximo razonable: **x10**.
  - Capital mínimo: **$50**.
  - Capital recomendado: **$200+**.
  - Número mínimo de trades para evaluar el sistema: **50**.
  - Rango estable: **100‑200 trades**.

---

## 📈 Market Adaptation / Adaptación al Mercado

El universo de activos se construye dinámicamente con los **Top 100 por volumen** de Binance y Bybit, asegurando que siempre se opere sobre los pares más líquidos. El sistema elige el activo que, en ese instante, presenta las mejores condiciones de microestructura, sin apegarse a un símbolo fijo.

---

## ⚠️ Disclaimer / Aviso Legal

**ES:** Este sistema no es asesoramiento financiero. Es un modelo probabilístico basado en microestructura de mercado. No garantiza resultados. El usuario asume todo el riesgo.

**EN:** This system is not financial advice. It is a probabilistic model based on market microstructure. No results are guaranteed. The user assumes all risk.

---

## ☕ Donations / Donaciones

Las donaciones son opcionales. Algunos usuarios destinan una parte de sus ganancias como práctica personal de disciplina.

Donations are optional. Some users allocate a portion of their gains as a personal discipline practice.

- **Alias:** `<INSERT_ALIAS>`
- **USDT TRC20:** `<INSERT_ADDRESS>`

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
