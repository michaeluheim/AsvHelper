from fpdf import FPDF
from datetime import datetime
import os
from config import (
    PFAD_NIMBUS_FONT,
    PFAD_NIMBUS_BOLD,
    PFAD_NIMBUS_ITALIC,
    PFAD_LOGO,
)
from helpers import fmt_eur

def erzeuge_pdf(
    pdf_output_path: str,
    rechnungsnummer: str,
    empfaenger: dict,
    positionen: dict,
    rabatt_prozent: float,
    umsatzsteuer_prozent: float,
    rechnungsgrund: str,
    raum_netto: float,
    raum_ust: float,
    raum_brutto: float,
    summe_netto_pos: float,
    summe_ust_pos: float,
    summe_brutto_pos: float,
    rabatt_betrag_netto: float
) -> str:
    r, g, b = 219, 73, 74
    logo_path = PFAD_LOGO

    pdf = FPDF()
    footer_height = 28
    pdf.set_auto_page_break(auto=True, margin=5) 
    pdf.add_page()

    # --- Fonts registrieren ---
    pdf.add_font("NimbusSans", "", PFAD_NIMBUS_FONT, uni=True)
    pdf.add_font("NimbusSans", "B", PFAD_NIMBUS_BOLD, uni=True)
    pdf.add_font("NimbusSans", "I", PFAD_NIMBUS_ITALIC, uni=True)


    # --- Header Hintergrund ---
    pdf.set_fill_color(r, g, b)
    pdf.rect(0, 10, pdf.w, 30, style="F")

    # --- Header: zentriert mit Logo rechts ---
    if os.path.exists(logo_path):
        pdf.image(str(logo_path), x=pdf.w - 45, y=5, w=40)

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("NimbusSans", "B", 16)
    pdf.set_xy(10, 15)
    pdf.cell(0, 8, "ASV Untereisenheim 1928 e.V.", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("NimbusSans", "", 14)
    pdf.cell(0, 5, "Maintorstraße, 97247 Eisenheim", ln=True, align="C")
    pdf.ln(15)

    # --- Empfängerblock ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("NimbusSans", "", 10)
    pdf.cell(0, 5, empfaenger.get("name", ""), ln=True)
    pdf.cell(0, 5, empfaenger.get("adresse", ""), ln=True)
    pdf.cell(0, 5, empfaenger.get("ort", ""), ln=True)
    pdf.ln(15)

    # --- Rechnungsinfo ---
    datum = datetime.now().strftime("%d.%m.%Y")
    pdf.cell(0, 5, f"Datum: {datum}", ln=True)
    pdf.cell(0, 5, f"Beleg-Nr.: {rechnungsnummer}", ln=True)
    pdf.ln(12)

    pdf.set_font("NimbusSans", "", 16)
    pdf.cell(0, 8, f"Rechnung – {rechnungsgrund}", ln=True)
    pdf.ln(6)

    # --- Tabelle (Positionsliste) ---
    pdf.set_font("NimbusSans", "", 10)
    pdf.set_fill_color(230, 230, 230)

    # Fixe Spaltenbreiten (die letzte Spalte nimmt Restbreite)
    col = {
        "artikel": 70,
        "menge": 15,
        "ep_netto": 20,
        "ges_netto": 20,
        "ust_pct": 20,
        "ust_betrag": 20,
    }

    # Tabellenkopf
    pdf.cell(col["artikel"],    8, "Artikel",           border=1, fill=True)
    pdf.cell(col["menge"],      8, "Menge",             border=1, fill=True, align="R")
    pdf.cell(col["ep_netto"],   8, "Stk. Netto",        border=1, fill=True, align="R")
    pdf.cell(col["ges_netto"],  8, "Pos Netto",         border=1, fill=True, align="R")
    pdf.cell(col["ust_pct"],    8, "USt %",             border=1, fill=True, align="R")
    pdf.cell(col["ust_betrag"], 8, "Stk. Brutto",       border=1, fill=True, align="R")
    pdf.cell(0,                  8, "Pos Brutto",        border=1, fill=True, ln=True, align="R")

    # Positionszeilen
    for pos in positionen.values():
        pdf.cell(col["artikel"],    8, str(pos["beschreibung"]),         border=1)
        pdf.cell(col["menge"],      8, f"{pos['menge']}",                border=1, align="R")
        pdf.cell(col["ep_netto"],   8, fmt_eur(pos["einzelpreis_netto"]), border=1, align="R")
        pdf.cell(col["ges_netto"],  8, fmt_eur(pos["gesamt_netto"]),     border=1, align="R")
        pdf.cell(col["ust_pct"],    8, f"{int(umsatzsteuer_prozent)}",   border=1, align="R")
        pdf.cell(col["ust_betrag"], 8, fmt_eur(pos["einzelpreis_brutto"]),       border=1, align="R")
        pdf.cell(0,                  8, fmt_eur(pos["gesamt_brutto"]),    border=1, ln=True, align="R")

    # Raummiete als separate Zeile (falls > 0)
    if raum_brutto > 0:
        pdf.cell(col["artikel"],    8, "Raummiete",      border=1)
        pdf.cell(col["menge"],      8, "1",              border=1, align="R")
        pdf.cell(col["ep_netto"],   8, fmt_eur(raum_netto), border=1, align="R")
        pdf.cell(col["ges_netto"],  8, fmt_eur(raum_netto), border=1, align="R")
        pdf.cell(col["ust_pct"],    8, f"{int(umsatzsteuer_prozent)}", border=1, align="R")
        pdf.cell(col["ust_betrag"], 8, fmt_eur(raum_brutto),  border=1, align="R")
        pdf.cell(0,                  8, fmt_eur(raum_brutto), border=1, ln=True, align="R")

    # Summen/Abschluss
    pdf.ln(6)
    pdf.set_font("NimbusSans", "", 10)
    pdf.cell(0, 6, f"Zwischensumme Positionen (netto): {fmt_eur(summe_netto_pos)}", ln=True)
    if rabatt_prozent and rabatt_prozent > 0:
        pdf.cell(0, 6, f"abzgl. Rabatt {int(rabatt_prozent)}% (auf Positionen, netto): {fmt_eur(rabatt_betrag_netto)}", ln=True)

    netto_nach_rabatt_und_raum = round((summe_netto_pos - rabatt_betrag_netto) + raum_netto, 2)
    ust_gesamt = round(netto_nach_rabatt_und_raum * (umsatzsteuer_prozent / 100.0), 2)
    brutto_gesamt = round(netto_nach_rabatt_und_raum + ust_gesamt, 2)

    pdf.cell(0, 6, f"Netto Gesamtbetrag: {fmt_eur(netto_nach_rabatt_und_raum)}", ln=True)
    pdf.cell(0, 6, f"Umsatzsteuer {int(umsatzsteuer_prozent)}%: {fmt_eur(ust_gesamt)}", ln=True)
    pdf.set_font("NimbusSans", "B", 14)
    pdf.cell(0, 8, f"Rechnungsbetrag insgesamt: {fmt_eur(brutto_gesamt)}", ln=True)

    pdf.ln(8)
    pdf.set_font("NimbusSans", "", 10)
    pdf.multi_cell(0, 5, "Sofern nicht anders angegeben, entspricht das Liefer-/Leistungsdatum dem Rechnungsdatum.")
    pdf.ln(10)
    pdf.cell(0, 5, "Michael Stühler", ln=True)
    pdf.cell(0, 5, "Vorstand", ln=True)
    pdf.cell(0, 5, "ASV Untereisenheim", ln=True)

    # --- Footer (vollflächig) ---
    page_width = pdf.w
    pdf.set_fill_color(r, g, b)
    pdf.rect(0, pdf.h - footer_height, page_width, footer_height, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(-footer_height + 3)
    pdf.set_font("NimbusSans", "", 8)

    pdf.cell(65, 6, "ASV Untereisenheim e.V.", ln=0)
    pdf.cell(65, 6, "Telefon: (09386)903280", ln=0)
    pdf.cell(0, 6, "Raiffeisenbank fränk. Weinland", ln=1)

    pdf.cell(65, 6, "Maintorstraße", ln=0)
    pdf.cell(65, 6, "Steuer-Nr: 257/107/00314", ln=0)
    pdf.cell(0, 6, "IBAN: DE17 7906 9001 0006 5152 82", ln=1)

    pdf.cell(65, 6, "97247 Eisenheim", ln=0)
    pdf.cell(65, 6, "", ln=0)
    pdf.cell(0, 6, "BIC: GENODEF1ERN", ln=1)

    pdf.output(pdf_output_path)
    return pdf_output_path