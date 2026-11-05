import sys
import cv2
import numpy as np
x0, y0, x1, y1 = (int(v) for v in sys.argv[2].split(","))
cap = cv2.VideoCapture(sys.argv[1]); frames = []
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1].astype(np.float32))
ref = frames[0]
win = cv2.createHanningWindow(ref.shape[::-1], cv2.CV_32F)
for i in range(0, len(frames), 12):
    (dx, dy), r = cv2.phaseCorrelate(ref, frames[i], win)
    print(f"frame {i:3d}: dx {dx:+.1f}px dy {dy:+.1f}px resp {r:.2f}")
