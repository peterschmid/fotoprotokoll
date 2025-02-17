import cv2
import numpy as np
import os

# Eingangsbild (ändern, falls nötig)
BILD_PFAD = "postit.jpg"  # Bild mit mehreren Post-its
OUTPUT_ORDNER = "postit_ausgeschnitten"

# Stelle sicher, dass der Ordner existiert
if not os.path.exists(OUTPUT_ORDNER):
    os.makedirs(OUTPUT_ORDNER)

# 1. Lade das Bild
bild = cv2.imread(BILD_PFAD)
if bild is None:
    print("Fehler: Bild konnte nicht geladen werden.")
    exit()

# 2. Bild in Graustufen umwandeln & Kanten hervorheben
grau = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)
gauss = cv2.GaussianBlur(grau, (5, 5), 0)
kanten = cv2.Canny(gauss, 50, 150)

# 3. Konturen erkennen
konturen, _ = cv2.findContours(kanten, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

postit_index = 1
for kontur in konturen:
    # Begrenzungsrechteck um jede erkannte Form
    x, y, w, h = cv2.boundingRect(kontur)

    # Filter: Nur größere Objekte (keine kleinen Störungen)
    if w > 50 and h > 50:
        postit = bild[y:y+h, x:x+w]  # Ausschneiden

        # Speichern
        postit_datei = os.path.join(OUTPUT_ORDNER, f"postit_{postit_index}.jpg")
        cv2.imwrite(postit_datei, postit)
        print(f"✅ Gespeichert: {postit_datei}")

        postit_index += 1

print(f"🎉 {postit_index - 1} Post-its wurden erkannt & gespeichert in '{OUTPUT_ORDNER}'")
