import cv2
import numpy as np
import os

# Parameter
BILD_PFAD = "postit.jpg"             # Pfad zum Eingangsbild
OUTPUT_ORDNER = "postit_ausgeschnitten"  # Ordner für ausgeschnittene Post-its
MIN_BREITE = 50                      # Mindestbreite eines Post-its
MIN_HOEHE = 50                       # Mindesthöhe eines Post-its
OVERLAP_THRESHOLD = 0.1              # IoU-Schwelle (Intersection over Union) für NMS

# Sicherstellen, dass der Ausgabeordner existiert
if not os.path.exists(OUTPUT_ORDNER):
    os.makedirs(OUTPUT_ORDNER)

# Bild laden
bild = cv2.imread(BILD_PFAD)
if bild is None:
    print("Fehler: Bild konnte nicht geladen werden.")
    exit()

# Bildvorverarbeitung: in Graustufen umwandeln, Rauschen reduzieren, Kanten finden
grau = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)
gauss = cv2.GaussianBlur(grau, (5, 5), 0)
kanten = cv2.Canny(gauss, 50, 150)

# Konturen im Bild finden
konturen, _ = cv2.findContours(kanten, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Alle relevanten Bounding Boxes sammeln
boxes = []
for kontur in konturen:
    x, y, w, h = cv2.boundingRect(kontur)
    if w < MIN_BREITE or h < MIN_HOEHE:
        continue
    boxes.append([x, y, x+w, y+h])

boxes = np.array(boxes)
if boxes.size == 0:
    print("Keine Post-its erkannt.")
    exit()

# --- Non-Maximum Suppression (NMS) Funktion ---
def non_max_suppression_fast(boxes, overlapThresh):
    """
    Führt Non-Maximum Suppression auf den übergebenen Bounding Boxes durch.
    boxes: numpy Array im Format [[x1, y1, x2, y2], ...]
    overlapThresh: Schwellenwert, ab dem Boxen als überlappend gelten
    Rückgabe: gefilterte Boxen
    """
    if len(boxes) == 0:
        return []
    
    boxes = boxes.astype("float")
    pick = []

    # Koordinaten extrahieren
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # Fläche jeder Box berechnen und nach dem unteren rechten y-Wert sortieren
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    while len(idxs) > 0:
        i = idxs[-1]            # Box mit dem größten y2-Wert (kann als repräsentativ betrachtet werden)
        pick.append(i)

        # Überschneidung mit allen anderen Boxen berechnen
        xx1 = np.maximum(x1[i], x1[idxs[:-1]])
        yy1 = np.maximum(y1[i], y1[idxs[:-1]])
        xx2 = np.minimum(x2[i], x2[idxs[:-1]])
        yy2 = np.minimum(y2[i], y2[idxs[:-1]])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        overlap = (w * h) / area[idxs[:-1]]

        # Alle Boxen löschen, die zu stark überlappen
        idxs = np.delete(idxs, np.concatenate(([len(idxs)-1], np.where(overlap > overlapThresh)[0])))
    
    return boxes[pick].astype("int")

# NMS auf die gefundenen Boxen anwenden
filtered_boxes = non_max_suppression_fast(boxes, OVERLAP_THRESHOLD)

# Die gefilterten Post-its ausschneiden und speichern
postit_index = 1
for (x1, y1, x2, y2) in filtered_boxes:
    postit = bild[y1:y2, x1:x2]
    filename = os.path.join(OUTPUT_ORDNER, f"postit_{postit_index}.jpg")
    cv2.imwrite(filename, postit)
    print("Gespeichert:", filename)
    postit_index += 1

print(f"Es wurden {postit_index-1} Post-its gespeichert in '{OUTPUT_ORDNER}'.")
