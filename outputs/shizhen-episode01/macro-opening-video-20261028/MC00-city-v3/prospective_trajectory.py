"""Prospective authored geometry only; no rendered-motion or source-survey claim."""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODES = [
    (0, (-10.5, -41, 18)), (2.5, (-10.5, -37, 18)),
    (5, (-7, -31, 17)), (11, (6, -8, 8)),
    (16, (20, 11, 2.5)), (19.5, (25, 14, 1.7)), (20, (25, 14, 1.7)),
]
AIMS = [(-12, -31, 16.8), (-12, -27, 16.8), (3, 25, 5),
        (18, 25, 2.3), (20, 27, 1.5), (18.8, 26, 1.4), (18.8, 26, 1.4)]


def direction_at(t):
    directions = []
    for (_, pos), aim in zip(NODES, AIMS):
        v = [aim[k]-pos[k] for k in range(3)]; norm = math.sqrt(sum(x*x for x in v))
        directions.append([x/norm for x in v])
    i = next((i for i in range(len(NODES)-1) if t <= NODES[i+1][0]), len(NODES)-2)
    u = max(0.0, min(1.0, (t-NODES[i][0])/(NODES[i+1][0]-NODES[i][0])))
    u = u*u*(3-2*u)
    v = [(1-u)*directions[i][k]+u*directions[i+1][k] for k in range(3)]
    norm = math.sqrt(sum(x*x for x in v))
    return [x/norm for x in v]


def point_at(t):
    i = next((i for i in range(len(NODES) - 1) if t <= NODES[i + 1][0]), len(NODES) - 2)
    t0, p0 = NODES[i]; t1, p1 = NODES[i + 1]
    if p0 == p1:
        return p0
    ta, pa = NODES[max(0, i - 1)]; tb, pb = NODES[min(len(NODES) - 1, i + 2)]
    dt = t1 - t0; u = max(0.0, min(1.0, (t - t0) / dt))
    m0 = [(p1[k] - pa[k]) / (t1 - ta) for k in range(3)]
    m1 = [(pb[k] - p0[k]) / (tb - t0) for k in range(3)]
    if pa == p0: m0 = [0.0] * 3
    if pb == p1: m1 = [0.0] * 3
    return tuple((2*u**3-3*u*u+1)*p0[k]+(u**3-2*u*u+u)*dt*m0[k]
                 +(-2*u**3+3*u*u)*p1[k]+(u**3-u*u)*dt*m1[k] for k in range(3))


def main():
    samples = [point_at(i / 24) for i in range(481)]
    directions = [direction_at(i / 24) for i in range(481)]
    rotation_speeds = [math.degrees(math.acos(max(-1, min(1, sum(a[k]*b[k] for k in range(3))))))*24
                       for a,b in zip(directions,directions[1:])]
    speeds = [math.dist(a, b)*24 for a, b in zip(samples, samples[1:])]
    # Design volumes, not measured building bounds in generated photos.
    volumes = {
        'eave_building': (-25, -11, -53, -37, 18),
        'residence': (15, 27, -21, -9, 12),
        'shelter': (9.5, 12.5, -2, 4, 2.7),
    }
    collisions = []
    for index, (x, y, z) in enumerate(samples):
        for name, (xmin, xmax, ymin, ymax, top) in volumes.items():
            if xmin < x < xmax and ymin < y < ymax and 0 < z < top + .2:
                collisions.append({'frame': index, 'volume': name})
    # Both traction segments lie north of y=18; the camera stays south.
    assert not collisions
    assert max(p[1] for p in samples) < 18
    assert max(speeds[-12:]) < 1e-7
    result = {
        'scope': 'PRE_GENERATION_AUTHORED_FEASIBILITY_ONLY',
        'units': 'metres in proposed city; uncalibrated authored dimensions',
        'coordinate_frame': 'x east, y north, z up; not source-survey coordinates',
        'duration_seconds': 20, 'fps_sampling': 24, 'nodes': NODES,
        'design_volumes': volumes, 'fixed_prospective_lens_full_frame_mm': 28,
        'authored_path_length_m': sum(speeds)/24,
        'authored_max_speed_mps': max(speeds),
        'authored_max_vertical_speed_mps': max(abs(a[2]-b[2])*24 for a,b in zip(samples,samples[1:])),
        'authored_max_rotation_degps': max(rotation_speeds),
        'last_half_second_max_speed_mps': max(speeds[-12:]),
        'authored_volume_collisions': collisions,
        'traction_line_side': 'south throughout; y < 18',
        'source_photo_calibration': 'NOT_MEASURED; perspective correspondence reviewed separately',
        'actual_generated_motion': 'NOT_EVALUATED',
        'samples': [{'seconds': i/24, 'position_m': list(p), 'look_direction': directions[i]} for i,p in enumerate(samples)],
    }
    (HERE/'prospective-trajectory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'nodes','samples','design_volumes'}}))


if __name__ == '__main__':
    main()
