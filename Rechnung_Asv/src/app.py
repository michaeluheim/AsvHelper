from services import rechnungspositionen_erstellen, import_new_data 
from config import PFAD_PREISLISTE_DATEN
import streamlit as st
import pandas as pd
import json
import os

from config import PFAD_PREISLISTE_DATEN
from services import rechnungspositionen_erstellen, import_new_data, rechnungspositionen_erstellen_csv_upload, rechnung_dict_csv
from streamlit_option_menu import option_menu

# --- Seite konfigurieren ---
st.set_page_config(layout="wide")
st.title("Preisliste & Rechnungs-Tool")

# --- Daten laden (global) ---
try:
    with open(PFAD_PREISLISTE_DATEN, "r", encoding="utf-8") as f:
        daten = json.load(f)
    df_preisliste = pd.DataFrame.from_dict(daten, orient="index")
    df_preisliste.index.name = "ID"
except FileNotFoundError:
    df_preisliste = pd.DataFrame()

# --- Seitenleiste mit Menü ---
with st.sidebar:
    selected = option_menu(
        "Navigation",
        ["Preisliste laden", "Rechnung erstellen", "CSV hochladen"],
        icons=["file-earmark-arrow-up", "receipt", "file-earmark-spreadsheet"],
        menu_icon="cast",
        default_index=0,
    )

# --- Helferfunktionen / Modulare Teile ---

def seite_preisliste_laden():
    st.subheader("Preisliste neu laden")
    # Hier machst du das, was import_new_data tut
    preisliste_dict = import_new_data()
    st.success("Preisliste wurde neu geladen und gespeichert.")
    st.write("Anzahl Artikel geladen:", len(preisliste_dict))

def seite_rechnung_erstellen():
    st.subheader("Rechnung erstellen")

    # Stammdaten
    empfaenger = {
        "name": st.text_input("Empfänger Name"),
        "adresse": st.text_input("Straße und Hausnummer"),
        "ort": st.text_input("PLZ und Ort")
    }
    rechnungsgrund = st.text_input("Rechnungsgrund", value="Raummiete")

    rabatt = st.slider("Rabatt in % (auf Positionen)", 0, 100, 20)
    raummiete = st.number_input("Raummiete (Brutto) in EUR", value=0.00, step=1.0)
    ust = st.slider("Umsatzsteuer in %", 0, 25, 19)

    # Prüfen, ob Preisliste geladen
    if df_preisliste.empty:
        st.error("Preisliste noch nicht vorhanden. Bitte zuerst laden.")
        return

    # Bestimme Spalten “beschreibung” und “preis”
    col_beschr = "beschreibung" if "beschreibung" in df_preisliste.columns else df_preisliste.columns[0]
    col_preis = None
    if "preis" in df_preisliste.columns:
        col_preis = "preis"
    else:
        # falls nur zwei Spalten, nehme die zweite als Preis
        if len(df_preisliste.columns) > 1:
            col_preis = df_preisliste.columns[1]

    # Baue df_artikel mit LABEL
    df_artikel = df_preisliste.reset_index()[["ID", col_beschr] + ([col_preis] if col_preis else [])]

    def make_label(row):
        if col_preis:
            try:
                preis_val = float(row[col_preis])
                # Formatieren wie “xx,yy €”
                preis_txt = f"{preis_val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            except Exception:
                preis_txt = str(row[col_preis])
            return f"{row[col_beschr]}  —  {preis_txt}  (ID {row['ID']})"
        else:
            return f"{row[col_beschr]}  (ID {row['ID']})"

    df_artikel["LABEL"] = df_artikel.apply(make_label, axis=1)
    label_to_id = dict(zip(df_artikel["LABEL"], df_artikel["ID"]))
    options_labels = list(label_to_id.keys())

    # Eingabetabelle für Artikel + Menge
    eingabe_df = pd.DataFrame({
        "Artikel": [None for _ in range(5)],
        "Menge": [None for _ in range(5)],
    })

    edited_df = st.data_editor(
        eingabe_df,
        num_rows="dynamic",
        use_container_width=True,
        key="eingabetabelle_artikel",
        column_config={
            "Artikel": st.column_config.SelectboxColumn(
                "Artikel",
                options=options_labels,
                required=False
            ),
            "Menge": st.column_config.NumberColumn(
                "Menge",
                min_value=1,
                step=1
            ),
        }
    )

    # Baue rechnung_dict
    rechnung_dict = {}
    for row in edited_df.itertuples():
        label = row.Artikel
        menge = row.Menge
        if label and pd.notna(label) and menge and pd.notna(menge):
            try:
                menge_int = int(menge)
                if menge_int > 0:
                    id_from_label = label_to_id.get(label)
                    try:
                        id_int = int(str(id_from_label))
                    except Exception:
                        id_int = id_from_label
                    rechnung_dict[id_int] = rechnung_dict.get(id_int, 0) + menge_int
            except (ValueError, TypeError):
                continue

    # Button zum Erstellen und Download anbieten
    if rechnung_dict:
        if st.button("Rechnung erstellen und speichern"):
            ergebnis = rechnungspositionen_erstellen(
                rechnung_dict=rechnung_dict,
                empfaenger=empfaenger,
                raummiete=raummiete,
                rabatt=rabatt,
                ust=ust,
                rechnungsgrund=rechnungsgrund
            )
            if ergebnis:
                st.success("Rechnung wurde erstellt und gespeichert.")
                pdf_path = ergebnis.get("pdf_path")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button("Rechnung als PDF herunterladen", f, file_name=os.path.basename(pdf_path))
                else:
                    st.warning("PDF-Pfad nicht gefunden.")
            else:
                st.error("Es gab ein Problem beim Erstellen der Rechnung.")
    else:
        st.info("Bitte mindestens einen Artikel mit Menge hinzufügen.")

def seite_csv_upload():
    st.subheader("CSV für Massenerstellung hochladen")
    hochgeladene_datei = st.file_uploader("CSV-Datei hochladen", type="csv")
    if hochgeladene_datei is not None:
        try:
            df_csv = pd.read_csv(hochgeladene_datei, sep=";", dtype=str)
            st.write("Vorschau der CSV-Daten:")
            st.dataframe(df_csv)
            rechnung_dict = rechnung_dict_csv(df_csv)
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")

        if st.button("Rechnungen aus CSV erstellen und speichern"):
                ergebnis = rechnungspositionen_erstellen_csv_upload(
                    rechnung_dict=rechnung_dict
                )
                if ergebnis:
                    st.success("Rechnungen wurde erstellt und gespeichert.") 
                else:
                    st.error("Es gab ein Problem beim Erstellen der Rechnung.")
    

# --- Haupt-Logik: Auswahl und Anzeige ---

if selected == "Preisliste laden":
    seite_preisliste_laden()
elif selected == "Rechnung erstellen":
    seite_rechnung_erstellen()
elif selected == "CSV hochladen":
    seite_csv_upload()
else:
    st.write("Bitte wähle im Menü eine Aktion aus.")
