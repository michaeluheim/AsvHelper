import pandas as pd
import os
import json
from datetime import datetime
from config import PFAD_RECHNUNGSPKOPF_DATEN, PFAD_PREISLISTE_DATEN

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

def baue_rechnung_dict(
    empfaenger: dict,
    rechnungsgrund: str,
    rabatt: int,
    raummiete: float,
    ust: int,
    rechnung_pos: pd.DataFrame,
) -> dict:
    # Baue mapping von Label zu ID
    with open(PFAD_PREISLISTE_DATEN, "r", encoding="utf-8") as f:
        preisliste_daten = json.load(f)
        
    label_to_id = {v["beschreibung"]: k for k, v in preisliste_daten.items()}

    positionen = {}
    for row in rechnung_pos.itertuples():
        label = row.Artikel
        menge = row.Menge
        if label and pd.notna(label) and menge and pd.notna(menge):
            try:
                menge_int = int(menge)
                if menge_int > 0:
                    id_from_label = label_to_id.get(label)
                    if id_from_label is None:
                        continue  # Label nicht gefunden
                    positionen[id_from_label] = positionen.get(id_from_label, 0) + menge_int
            except (ValueError, TypeError):
                continue  # Ungültige Menge → überspringen

    rechnung_dict = {}
    rechnung_dict["empfaenger"] = empfaenger
    rechnung_dict["rechnungsgrund"] = rechnungsgrund
    rechnung_dict["rabatt"] = rabatt
    rechnung_dict["raummiete"] = raummiete
    rechnung_dict["ust"] = ust
    rechnung_dict["positionen"] = positionen

    return rechnung_dict