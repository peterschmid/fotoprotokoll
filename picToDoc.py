import os
from docx import Document
from docx.shared import Inches
from PIL import Image, ExifTags

# Konfigurierbare Einstellungen
BILDER_ORDNER = "Pics"  # Name des Ordners mit den Fotos
OUTPUT_DATEI = "Fotoprotokoll.docx"
MAX_BREITE_INCHES = 5  # Maximale Bildbreite im Dokument (angepasst)

# Funktion: Bild drehen (falls nötig) & optimierte Skalierung
def verarbeite_bild(bildpfad):
    with Image.open(bildpfad) as img:
        # 1. Exif-Daten prüfen und Bild richtig drehen
        try:
            for tag in ExifTags.TAGS:
                if ExifTags.TAGS[tag] == "Orientation":
                    orientation_tag = tag
                    break
            exif = img._getexif()
            if exif and orientation_tag in exif:
                orientation = exif[orientation_tag]
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass  # Falls Exif-Daten fehlen, nichts tun

        # 2. Bildgröße beibehalten oder leicht skalieren
        breite, hoehe = img.size
        faktor = (MAX_BREITE_INCHES * 96) / breite  # 96 DPI für Word
        if faktor < 1:  # Nur verkleinern, nicht vergrößern
            img = img.resize((int(breite * faktor), int(hoehe * faktor)), Image.LANCZOS)

        # 3. Bearbeitetes Bild temporär speichern
        tmp_bildpfad = bildpfad.replace(".", "_tmp.")
        img.save(tmp_bildpfad, quality=95)  # Qualität beibehalten
        return tmp_bildpfad

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
        optimiertes_bild = verarbeite_bild(bildpfad)  # Korrigiertes Bild holen


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
