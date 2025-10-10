import pandas as pd
import os
import json
from datetime import datetime
from config import PFAD_RECHNUNGSPKOPF_DATEN

def data_transformer(df: pd.DataFrame) -> dict:
    # Preis aus CSV (deutsche Schreibweise) nach float
    df["preis"] = df["preis"].astype(str).str.replace(",", ".").astype(float)
    return df.set_index("id")[["beschreibung", "preis"]].to_dict(orient="index")

def generiere_rechnungsnummer() -> str:
    heute = datetime.now().strftime("%Y%m%d")
    if not os.path.exists(PFAD_RECHNUNGSPKOPF_DATEN):
        rechnungskopf = {}
    else:
        with open(PFAD_RECHNUNGSPKOPF_DATEN, "r", encoding="utf-8") as f:
            rechnungskopf = json.load(f)
    laufende_nummern = [int(rn.split("-")[-1]) for rn in rechnungskopf.keys() if rn.startswith(heute)]
    naechste_nr = max(laufende_nummern, default=0) + 1
    return f"{heute}-{naechste_nr:03d}"

def gross_to_net(brutto: float, ust_prozent: float) -> tuple[float, float]:
    """
    Rechnet einen Bruttopreis (inkl. USt) in Netto und USt-Betrag um.
    Rundung auf 2 Nachkommastellen für Rechnungsausweis.
    """
    faktor = 1 + (ust_prozent / 100.0)
    netto = round(brutto / faktor, 2)
    ust_betrag = round(brutto - netto, 2)
    return netto, ust_betrag

def fmt_eur(v: float) -> str:
    # Einfache Euro-Formatierung 1.234,56 €
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"