from pathlib import Path
from datetime import datetime

# Basis ist das Projekt-Root (egal ob lokal oder im Container)
ORDNER_REPO = Path(__file__).resolve().parents[2]

# Unterordner
ORDNER_APP =    ORDNER_REPO / "src"
ORDNER_DATA =   ORDNER_REPO / "data" / str(datetime.now().year)
ORDNER_IMPORT = ORDNER_REPO / "import"
ORDNER_DOCS = ORDNER_REPO / "docs" / str(datetime.now().year)
ORDNER_DOCS.mkdir(parents=True, exist_ok=True)
ORDNER_DATA.mkdir(parents=True, exist_ok=True)

# Eingabe/Import
PFAD_PREISLISTE_IMPORT   = ORDNER_IMPORT / "preisliste.csv"

# Ausgaben/Daten
PFAD_PREISLISTE_DATEN    = ORDNER_IMPORT / "preisliste.json"
PFAD_RECHNUNGSPOS_DATEN   = ORDNER_DATA / "rechnungspositionen.json"
PFAD_RECHNUNGSPKOPF_DATEN  = ORDNER_DATA / "rechnungskopf.json"

# Assets
PFAD_LOGO                = ORDNER_IMPORT / "Logo Mail.png"
PFAD_NIMBUS_FONT         = ORDNER_IMPORT / "Nimbus_Sans_ttf" / "NimbusSans-Regular.ttf"
PFAD_NIMBUS_BOLD         = ORDNER_IMPORT / "Nimbus_Sans_ttf" / "NimbusSans-Bold.ttf"
PFAD_NIMBUS_ITALIC       = ORDNER_IMPORT / "Nimbus_Sans_ttf" / "NimbusSans-Italic.ttf"

# Fallback-Schrift (systemweit)
PFAD_FALLBACK_FONT       = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
