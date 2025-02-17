import cv2
import numpy as np
import os

# 1) Einstellungen anpassen
BILD_PFAD = "postit.jpg"              # Pfad zum Eingangsbild
OUTPUT_ORDNER = "postit_ausgeschnitten"
MIN_FLAECHE = 500                     # Minimale Konturfläche, um Kleinstes zu filtern
THRESHOLD_S = 50                      # Sättigungs-Schwelle (je höher, desto strenger)

# Ordner für Ergebnisbilder
if not os.path.exists(OUTPUT_ORDNER):
    os.makedirs(OUTPUT_ORDNER)

def order_points(pts):
    """
    Sortiert 4 Punkte eines Vierecks in der Reihenfolge:
    [oben-links, oben-rechts, unten-rechts, unten-links]
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    """
    Perspektivische Transformation: 'zieht' ein Viereck so,
    dass wir ein aufrechtes, rechteckiges Bild erhalten.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Breite berechnen
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    # Höhe berechnen
    heightA = np.linalg.norm(br - tr)
    heightB = np.linalg.norm(bl - tl)
    maxHeight = int(max(heightA, heightB))

    # Ziel-Koordinaten definieren
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Transformation anwenden
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

# 2) Bild laden
bild = cv2.imread(BILD_PFAD)
if bild is None:
    print("Fehler: Bild konnte nicht geladen werden.")
    exit()

# 3) In HSV umwandeln und nur Sättigung (S-Channel) extrahieren
hsv = cv2.cvtColor(bild, cv2.COLOR_BGR2HSV)
s_channel = hsv[:, :, 1]

# 4) Threshold auf die Sättigung anwenden: alles über 'THRESHOLD_S' gilt als "farbig"
_, mask_s = cv2.threshold(s_channel, THRESHOLD_S, 255, cv2.THRESH_BINARY)

# 5) Rauschen entfernen (morphologische Operationen)
kernel = np.ones((5, 5), np.uint8)
mask_s = cv2.morphologyEx(mask_s, cv2.MORPH_OPEN, kernel, iterations=1)
mask_s = cv2.morphologyEx(mask_s, cv2.MORPH_CLOSE, kernel, iterations=1)

# 6) Konturen in der Maske finden
konturen, _ = cv2.findContours(mask_s, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

postit_index = 1
for cnt in konturen:
    area = cv2.contourArea(cnt)
    if area < MIN_FLAECHE:
        continue  # zu klein, wahrscheinlich kein Post-it

    # 7) Gedrehtes Rechteck bestimmen und 'geradeziehen'
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect).astype("float32")
    warped = four_point_transform(bild, box)

    # 8) Speichern
    filename = os.path.join(OUTPUT_ORDNER, f"postit_{postit_index}.jpg")
    cv2.imwrite(filename, warped)
    print("Gespeichert:", filename)
    postit_index += 1

print(f"Es wurden {postit_index - 1} Post-its gespeichert in '{OUTPUT_ORDNER}'.")
