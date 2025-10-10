import pandas as pd
import json
from pathlib import Path
from config import PFAD_PREISLISTE_IMPORT, PFAD_PREISLISTE_DATEN
from helpers import data_transformer, generiere_rechnungsnummer

def data_loader(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", names=["id", "beschreibung", "preis"])

def data_exporter(data: dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def import_new_data() -> dict:
    df = data_loader(PFAD_PREISLISTE_IMPORT)
    preisliste_dict = data_transformer(df)
    data_exporter(preisliste_dict, PFAD_PREISLISTE_DATEN)
    return preisliste_dict

def rechnung_dict_csv(df: pd.DataFrame) -> dict:
    rechnung_dict = {}
    jahr = pd.Timestamp.now().year 

    aktuelle_rn = generiere_rechnungsnummer()

    for _, row in df.iterrows():
        try:
            datum, zaehler = aktuelle_rn.split("-")
        except ValueError:
            raise ValueError(f"Ungültiges Rechnungsnummernformat: {aktuelle_rn}")

        rn = f"{datum}-{int(zaehler):03d}"

        aktuelle_rn = f"{datum}-{int(zaehler) + 1:03d}"

        grund = f"Bandenwerbung ASV Untereisenheim {jahr}"
        rechnung_dict[rn] = {
            "name": row["Firmenname"],
            "adresse": row["Straße"],
            "ort": row["Ort"],
            "id": row["ID"],
            "anzahl": int(float(str(row["Anzahl"]).replace(",", "."))) if pd.notna(row["Anzahl"]) else 0,
            "rechnungsgrund": grund,
        }

    return rechnung_dict
