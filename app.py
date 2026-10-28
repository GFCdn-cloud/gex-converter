import re
import datetime
from dataclasses import dataclass
from typing import Optional

import streamlit as st

st.set_page_config(page_title="GEX//CONVERTER", page_icon="🟢", layout="wide")

# ---------- GEX//CONVERTER logic ----------
MINUS = r"\-\u2212\u2013\u2014"
LINE_RE = re.compile(
    r"^\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{3,6}(?:\.\d+)?)\s+(.*)$"
)
VAL_RE = re.compile(r"([+" + MINUS + r"])\s?([\d,]+)")

@dataclass
class Level:
    price: float
    value: int
    label: str
    type: str
    name: str
    included: bool = True

def to_float(s):
    return float(s.replace(",", ""))

def to_int(sign, digits):
    v = int(re.sub(r"[^\d]", "", digits) or 0)
    return v if sign == "+" else -v

def classify(label):
    l = label.lower()
    if not label:
        return "gex", "NetGEX"
    if "0dte" in l:
        return "zero", label
    if "call resistance" in l:
        return "call", label
    if "put support" in l:
        return "put", label
    if l.startswith("hvl"):
        return "hvl", label
    return "gex", label

def parse_message(text):
    meta, levels, seen = {}, [], set()
    m = re.search(r"^\s*([A-Z0-9_.]+!?)\s*\(", text, re.M)
    if m:
        meta["symbol"] = m.group(1)
    m = re.search(r"Key Metrics\s*[—–-]\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        meta["date"] = m.group(1)
    m = re.search(r"Spot Price:\s*\$?\s*([\d,]+(?:\.\d+)?)", text)
    if m:
        meta["spot"] = to_float(m.group(1))

    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        price = to_float(m.group(1))
        if price < 100:
            continue
        left, _, right = m.group(2).partition("←")
        v = VAL_RE.search(left)
        if not v:
            continue
        value = to_int(v.group(1), v.group(2))
        label = re.sub(r"\s+", " ", right.replace(",", " ")).strip()
        if (price, value) in seen:
            continue
        seen.add((price, value))
        t, name = classify(label)
        levels.append(Level(price, value, label, t, name))

    m = re.search(r"1D Max\s*\(?([\d,]+(?:\.\d+)?)\)?", text)
    if m:
        levels.append(Level(to_float(m.group(1)), 0, "1D Max", "max", "1D Max"))
    levels.sort(key=lambda x: -x.price)
    return meta, levels

def fmt_price(p):
    return ("%.2f" % p).rstrip("0").rstrip(".")

def build_output(meta, levels):
    head = "// " + " ".join(x for x in (meta.get("symbol"), meta.get("date")) if x)
    rows = [f"{l.type},{l.name},{fmt_price(l.price)},{l.value}" for l in levels if l.included]
    return "\n".join([head] + rows)

def auto_include(level, spot, threshold, distance, use_gex, use_zero, use_max):
    if level.type == "gex":
        ok = abs(level.value) >= threshold if level.label == "" else use_gex
    elif level.type == "zero":
        ok = use_zero
    elif level.type == "max":
        ok = use_max
    else:
        ok = True
    if ok and distance > 0 and spot and level.type not in ("call", "put", "hvl"):
        ok = abs(level.price - spot) <= distance
    return ok

# ---------- Style ----------
st.markdown("""
<style>
.stApp { background: #000; color: #d7f5e5; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container { padding-top: 1.5rem; max-width: 1500px; }
h1, h2, h3 { color: #00ff88 !important; }
p, label, span, div { }
div[data-testid="stMetric"] { background:#070a08; border:1px solid #12301f; padding:14px; border-radius:10px; }
.stTextArea textarea, .stTextInput input, .stNumberInput input { background:#070a08 !important; color:#d7f5e5 !important; border:1px solid #12301f !important; }
.stButton button { background:#00ff88; color:#000; border:0; font-weight:700; border-radius:7px; }
.stButton button:hover { background:#5bffb0; color:#000; }
hr { border-color:#12301f; }
</style>
""", unsafe_allow_html=True)

st.markdown("# GEX<span style='color:#00ff88'>//CONVERTER</span>", unsafe_allow_html=True)
st.caption("MenthorQ → Pine Script · Web edition")

today = datetime.date.today().isoformat()
if "prompt_text" not in st.session_state:
    st.session_state.prompt_text = (
        f"Fetch the updated Net GEX, OI, IV, week change and monthly change about nq1! "
        f"for date {today}. Analyze the Net GEX distribution for nq1! for date {today}. "
        "Identify where the largest GEX concentrations are located relative to spot price "
        "highlight the transition zone where GEX flips from negative to positive. "
        "Also make a Diagram or histogram to visually analyze."
    )

with st.expander("00 · PROMPT GIORNALIERO", expanded=False):
    pcol1, pcol2 = st.columns([1, 2])
    with pcol1:
        prompt_date = st.date_input("Data del prompt", value=datetime.date.today())
        if st.button("Aggiorna data"):
            st.session_state.prompt_text = re.sub(
                r"\d{4}-\d{2}-\d{2}", prompt_date.isoformat(), st.session_state.prompt_text
            )
    with pcol2:
        st.session_state.prompt_text = st.text_area("Prompt modificabile", st.session_state.prompt_text, height=130)
    st.code(st.session_state.prompt_text, language="text")

st.markdown("### 01 · INPUT — messaggio MenthorQ")
input_text = st.text_area("Incolla qui il messaggio completo", height=230, placeholder="Incolla qui il testo copiato da MenthorQ…", label_visibility="collapsed")

c1, c2, c3, c4 = st.columns(4)
with c1:
    threshold = st.number_input("MIN |GEX| senza nome", min_value=0, value=200000, step=50000)
with c2:
    distance = st.number_input("Distanza max dallo spot (pt; 0 = off)", min_value=0.0, value=0.0, step=10.0)
with c3:
    use_gex = st.checkbox("GEX 1–9", value=True)
with c4:
    use_zero = st.checkbox("0DTE", value=True)
use_max = st.checkbox("1D MAX", value=True)

if "levels" not in st.session_state:
    st.session_state.levels = []
    st.session_state.meta = {}

if st.button("INCOLLA / CONVERTI", type="primary"):
    st.session_state.meta, st.session_state.levels = parse_message(input_text)
    st.session_state.last_input = input_text

meta = st.session_state.meta
levels = st.session_state.levels

if levels:
    for lv in levels:
        lv.included = auto_include(lv, meta.get("spot"), threshold, distance, use_gex, use_zero, use_max)
    st.markdown("### Riepilogo")
    cols = st.columns(4)
    cols[0].metric("SYMBOL", meta.get("symbol", "—"))
    cols[1].metric("DATE", meta.get("date", "—"))
    cols[2].metric("SPOT", fmt_price(meta["spot"]) if "spot" in meta else "—")
    cols[3].metric("LIVELLI ATTIVI", f"{sum(l.included for l in levels)}/{len(levels)}")

    st.markdown("### 02 · LIVELLI — seleziona quelli da includere")
    edited = []
    for i, lv in enumerate(levels):
        row = st.columns([0.45, 0.8, 2.2, 1, 1.2])
        checked = row[0].checkbox("Includi", value=lv.included, key=f"lv_{i}", label_visibility="collapsed")
        row[1].write(lv.type.upper())
        row[2].write(lv.name or "NetGEX")
        row[3].write(fmt_price(lv.price))
        row[4].write(f"{lv.value:+,}" if lv.value else "—")
        lv.included = checked
    output = build_output(meta, levels)
    st.markdown("### 03 · OUTPUT — Pine Script")
    st.code(output or "// Nessun livello selezionato", language="text")
    st.download_button("Scarica output .txt", data=output, file_name="gex_levels.txt", mime="text/plain")
else:
    if input_text and st.button("Riprova conversione"):
        st.session_state.meta, st.session_state.levels = parse_message(input_text)
        st.rerun()
    st.info("Incolla il messaggio MenthorQ e premi **INCOLLA / CONVERTI** per estrarre i livelli.")
