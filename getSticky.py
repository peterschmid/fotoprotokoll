import cv2
import numpy as np
import os

# -------------------------------------------------------------
# 1) Parameter anpassen
# -------------------------------------------------------------
BILD_PFAD = "postit.jpg"
OUTPUT_ORDNER = "postit_ausgeschnitten"

# Minimale Konturfläche
MIN_FLAECHE = 500

# Seitenverhältnis-Bereich (Breite/Höhe)
MIN_RATIO = 0.6
MAX_RATIO = 1.8

# HSV-Farbbereiche für typische Post-it-Farben (Richtwerte!)
# Du kannst mehr oder weniger Farben hinzufügen
COLOR_RANGES = {
    "orange": ((10, 100, 150), (30, 180, 255)),
    "blue": ((88, 117, 150), (108, 177, 210)),
    "green": ((64, 128, 112), (84, 188, 172)),
    "yellow": ((14, 200, 180), (34, 255, 255)),
    "pink":   ((140, 50, 50), (170, 255, 255)),
}

# -------------------------------------------------------------
# 2) Hilfsfunktionen
# -------------------------------------------------------------
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
    Führt eine perspektivische Transformation durch, sodass das
    durch pts definierte Viereck "gerade gezogen" wird.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Breiten berechnen
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    # Höhen berechnen
    heightA = np.linalg.norm(br - tr)
    heightB = np.linalg.norm(bl - tl)
    maxHeight = int(max(heightA, heightB))

    # Zielkoordinaten definieren
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

# -------------------------------------------------------------
# 3) Bild laden
# -------------------------------------------------------------
bild = cv2.imread(BILD_PFAD)
if bild is None:
    raise IOError(f"Bild '{BILD_PFAD}' konnte nicht geladen werden.")

if not os.path.exists(OUTPUT_ORDNER):
    os.makedirs(OUTPUT_ORDNER)

# -------------------------------------------------------------
# 4) HSV-Konvertierung und Farbmasken erstellen
# -------------------------------------------------------------
hsv = cv2.cvtColor(bild, cv2.COLOR_BGR2HSV)

# Leere Maske für alle erlaubten Farben
mask_total = np.zeros(hsv.shape[:2], dtype="uint8")

# Für jede definierte Farbe eine Maske erstellen und mit bitwise_or vereinen
for color_name, (lower, upper) in COLOR_RANGES.items():
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")
    mask_color = cv2.inRange(hsv, lower, upper)
    mask_total = cv2.bitwise_or(mask_total, mask_color)

# Optional: Morphologische Operationen, um Rauschen zu entfernen
kernel = np.ones((5, 5), np.uint8)
mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel, iterations=1)
mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel, iterations=1)

# -------------------------------------------------------------
# 5) Konturen finden
# -------------------------------------------------------------
contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

postit_index = 1
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < MIN_FLAECHE:
        continue

    # Rotiertes Rechteck bestimmen
    rect = cv2.minAreaRect(cnt)
    (cx, cy), (w, h), angle = rect

    # Seitenverhältnis (Breite/Höhe) prüfen
    if w == 0 or h == 0:
        continue
    ratio = w / h if w > h else h / w  # Immer >= 1
    if ratio < MIN_RATIO or ratio > MAX_RATIO:
        continue

    # Box-Eckpunkte
    box = cv2.boxPoints(rect).astype("float32")

    # Perspektivische Transformation
    warped = four_point_transform(bild, box)

    # Ergebnis speichern
    filename = os.path.join(OUTPUT_ORDNER, f"postit_{postit_index}.jpg")
    cv2.imwrite(filename, warped)
    print(f"Gespeichert: {filename}")
    postit_index += 1

print(f"Fertig! {postit_index - 1} Post-its gespeichert in '{OUTPUT_ORDNER}'.")
