from datetime import datetime
import os
import json
import pandas as pd
from helpers import (
    generiere_rechnungsnummer,
    gross_to_net,
)
from config import (
    ORDNER_REPO,
    ORDNER_DOCS,
    PFAD_PREISLISTE_DATEN,
    PFAD_RECHNUNGSPOS_DATEN,
    PFAD_RECHNUNGSPKOPF_DATEN
)
from services.dataloader import data_exporter
from domain import erzeuge_pdf
import streamlit as st
from pathlib import Path
from decimal import Decimal

def rechnungspositionen_erstellen(
    rechnung_dict: dict
) -> dict:
    try:
        with open(PFAD_PREISLISTE_DATEN, "r", encoding="utf-8") as f:
            preisliste = json.load(f)
    except FileNotFoundError:
        st.error("Preisliste nicht gefunden. Bitte zuerst laden.")
        return {}

    rechnungsnummer = generiere_rechnungsnummer()
    pdf_output_path = ORDNER_DOCS / f"rechnung_{rechnungsnummer}.pdf"

    rechnungspositionen = {}
    summe_netto_pos = 0.0
    summe_ust_pos = 0.0
    summe_brutto_pos = 0.0

    # Positionen aus Preisliste (Brutto) rückwärts rechnen
    for pos_nr, (id_, menge) in enumerate(rechnung_dict["positionen"].items(), start=1):
        if str(id_) not in preisliste:
            st.warning(f"ID {id_} nicht in Preisliste gefunden.")
            continue

        artikel = preisliste[str(id_)]
        beschreibung = artikel["beschreibung"]
        einzelpreis_brutto = float(artikel["preis"])
        einzelpreis_netto, einzel_ust = gross_to_net(einzelpreis_brutto, rechnung_dict["ust"])

        gesamt_netto = round(einzelpreis_netto * menge, 2)
        gesamt_brutto = round(einzelpreis_brutto * menge, 2)
        ust_betrag = round(gesamt_brutto - gesamt_netto, 2)  # entspricht gesamt_netto * ust%

        summe_netto_pos += gesamt_netto
        summe_ust_pos += ust_betrag
        summe_brutto_pos += gesamt_brutto

        positions_id = f"{rechnungsnummer}_{pos_nr}"
        rechnungspositionen[positions_id] = {
            "rechnungsnr": rechnungsnummer,
            "positionsnr": pos_nr,
            "id": id_,
            "beschreibung": beschreibung,
            "menge": menge,
            "einzelpreis_brutto": round(einzelpreis_brutto, 2),
            "einzelpreis_netto": einzelpreis_netto,
            "gesamt_netto": gesamt_netto,
            "ust_betrag": ust_betrag,
            "gesamt_brutto": gesamt_brutto,
            "erstellt_am": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # Rabatt auf Netto-Summe der Positionen
    rabatt_betrag_netto = round(summe_netto_pos * (rechnung_dict["rabatt"] / 100.0), 2)

    # Raummiete: Eingabe als Brutto interpretiert → rückwärts rechnen
    raum_brutto = float(rechnung_dict["raummiete"])
    raum_netto, raum_ust = gross_to_net(raum_brutto, rechnung_dict["ust"])

    # Netto-Gesamt nach Rabatt + Raummiete
    netto_gesamt = round((summe_netto_pos - rabatt_betrag_netto) + raum_netto, 2)
    ust_gesamt = round(netto_gesamt * (rechnung_dict["ust"] / 100.0), 2)
    brutto_gesamt = round(netto_gesamt + ust_gesamt, 2)

    # Kopf speichern
    if os.path.exists(PFAD_RECHNUNGSPKOPF_DATEN):
        with open(PFAD_RECHNUNGSPKOPF_DATEN, "r", encoding="utf-8") as f:
            rechnungskopf = json.load(f)
    else:
        rechnungskopf = {}

    rechnungskopf[rechnungsnummer] = {
        "empfaenger": rechnung_dict["empfaenger"],
        "datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "anzahl_positionen": len(rechnungspositionen) + (1 if raum_brutto > 0 else 0),
        "netto_gesamt": netto_gesamt,
        "ust_gesamt": ust_gesamt,
        "brutto_gesamt": brutto_gesamt
    }
    data_exporter(rechnungskopf, PFAD_RECHNUNGSPKOPF_DATEN)

    # Rechnungspositionen anhängen
    if os.path.exists(PFAD_RECHNUNGSPOS_DATEN):
        with open(PFAD_RECHNUNGSPOS_DATEN, "r", encoding="utf-8") as f:
            bestehende_positionen = json.load(f)
    else:
        bestehende_positionen = {}

    bestehende_positionen.update(rechnungspositionen)
    data_exporter(bestehende_positionen, PFAD_RECHNUNGSPOS_DATEN)

    # PDF erzeugen (Positionstabelle inkl. Netto/UST/Brutto, Summen, Rabatt, Raummiete)
    erzeuge_pdf(
        pdf_output_path=pdf_output_path,
        rechnungsnummer=rechnungsnummer,
        empfaenger=rechnung_dict["empfaenger"],
        positionen=rechnungspositionen,
        rabatt_prozent=rechnung_dict["rabatt"],
        umsatzsteuer_prozent=rechnung_dict["ust"],
        rechnungsgrund=rechnung_dict["rechnungsgrund"],
        raum_netto=raum_netto,
        raum_ust=raum_ust,
        raum_brutto=raum_brutto,
        summe_netto_pos=round(summe_netto_pos, 2),
        summe_ust_pos=round(summe_ust_pos, 2),
        summe_brutto_pos=round(summe_brutto_pos, 2),
        rabatt_betrag_netto=rabatt_betrag_netto
    )

    return {
        "rechnungsnummer": rechnungsnummer,
        "pdf_path": pdf_output_path,
        "summen": {
            "pos_netto": round(summe_netto_pos, 2),
            "pos_ust": round(summe_ust_pos, 2),
            "pos_brutto": round(summe_brutto_pos, 2),
            "rabatt_netto": rabatt_betrag_netto,
            "raum_netto": raum_netto,
            "raum_ust": raum_ust,
            "raum_brutto": raum_brutto,
            "netto_gesamt": netto_gesamt,
            "ust_gesamt": ust_gesamt,
            "brutto_gesamt": brutto_gesamt
        }
    }


def rechnung_dict_csv(df: pd.DataFrame):
    jahr = datetime.now().year
    for row in df.itertuples():
        rechnung_dict = {}
        rechnung_dict["empfaenger"]   = {
                "name": row.Firmenname,
                "adresse": row.Straße,
                "ort": row.Ort
            }
        rechnung_dict["rechnungsgrund"] = rf"Bandenwerbung ASV Untereisenheim {jahr}"
        rechnung_dict["rabatt"] = 0
        rechnung_dict["raummiete"] = 0
        rechnung_dict["ust"] = 19
        rechnung_dict["positionen"] = {
            row.ID : float(str(row.Anzahl).replace(",", "."))
        }
        
        rechnungspositionen_erstellen(rechnung_dict)

    return 

