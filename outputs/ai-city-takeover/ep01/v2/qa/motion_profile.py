"""Per-second camera motion profile of a clip: median optical-flow magnitude and scale change (px at 960 wide)."""
import sys
import cv2
import numpy as np

cap = cv2.VideoCapture(sys.argv[1])
prev, rows, i = None, [], 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
    g = cv2.cvtColor(cv2.resize(frame, (960, 540)), cv2.COLOR_BGR2GRAY)
    if prev is not None:
        pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 8)
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, pts, None)
        a, b = pts[st == 1].reshape(-1, 2), nxt[st == 1].reshape(-1, 2)
        m, _ = cv2.estimateAffinePartial2D(a, b)
        scale = float(np.hypot(m[0, 0], m[1, 0])) if m is not None else 1.0
        tx, ty = (float(m[0, 2]), float(m[1, 2])) if m is not None else (0.0, 0.0)
        rows.append((t, float(np.median(np.linalg.norm(b - a, axis=1))), scale, tx, ty))
    prev = g
    i += 1
r = np.array(rows)
for s in range(int(r[:, 0].max()) + 1):
    seg = r[(r[:, 0] >= s) & (r[:, 0] < s + 1)]
    if len(seg):
        print(f"{s}-{s+1}s flow_med {seg[:,1].mean():.3f}px/frame  scale/frame {(seg[:,2].mean()-1)*1000:+.3f}e-3  tx {seg[:,3].mean():+.3f} ty {seg[:,4].mean():+.3f}")
tail = r[r[:, 0] >= r[:, 0].max() - 0.5]
print(f"last 0.5s flow_med {tail[:,1].mean():.3f}px/frame scale/frame {(tail[:,2].mean()-1)*1000:+.3f}e-3")
