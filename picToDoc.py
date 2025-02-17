import os
from docx import Document
from docx.shared import Inches
from PIL import Image

# Konfigurierbare Einstellungen
BILDER_ORDNER = "Pics"  # Name des Ordners mit den Fotos
OUTPUT_DATEI = "Fotoprotokoll.docx"

# 1. Erstelle ein Word-Dokument
doc = Document()
doc.add_heading("Fotoprotokoll", level=1)

# 2. Durchlaufe alle Bilder im Ordner
if not os.path.exists(BILDER_ORDNER):
    print(f"Ordner '{BILDER_ORDNER}' nicht gefunden!")
    exit()

bilder = sorted(os.listdir(BILDER_ORDNER))  # Bilder sortieren

for bild in bilder:
    if bild.lower().endswith((".png", ".jpg", ".jpeg")):
        bildpfad = os.path.join(BILDER_ORDNER, bild)
        
        # Optional: Bildgröße anpassen, um Speicherplatz zu sparen
        with Image.open(bildpfad) as img:
            breite, hoehe = img.size
            faktor = 500 / breite  # Skaliere auf max. 500px Breite
            img = img.resize((500, int(hoehe * faktor)))
            img.save(bildpfad)  # Überschreibe das Bild mit der kleineren Version

        # Füge das Bild in das Word-Dokument ein
        doc.add_paragraph(f"Bild: {bild}")
        doc.add_picture(bildpfad, width=Inches(5))  # Skaliert auf 5 Zoll Breite
        doc.add_paragraph("")  # Leerzeile für bessere Lesbarkeit

# 3. Speichere das Word-Dokument
doc.save(OUTPUT_DATEI)
print(f"Dokument gespeichert als {OUTPUT_DATEI}")

# 4. (Optional) Word-Datei in PDF umwandeln
try:
    import comtypes.client
    wdFormatPDF = 17
    word = comtypes.client.CreateObject("Word.Application")
    doc = word.Documents.Open(os.path.abspath(OUTPUT_DATEI))
    doc.SaveAs(os.path.abspath("Fotoprotokoll.pdf"), FileFormat=wdFormatPDF)
    doc.Close()
    word.Quit()
    print("PDF erfolgreich erstellt: Fotoprotokoll.pdf")
except ImportError:
    print("PDF-Export nicht möglich. Installiere 'comtypes', falls du Word nutzt.")
