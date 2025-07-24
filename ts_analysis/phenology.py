from __future__ import annotations

import numpy as np
from scipy.signal import argrelmax


def clip_years(arr: np.ndarray, start_year: int, end_year: int, offset: int = 0) -> dict[int, np.ndarray]:
    """Return a dictionary of years to daily pixel arrays."""
    pixel = {}
    step = 365
    for i in range(end_year - start_year):
        start = step * i + 1 + offset
        stop = step * (i + 1) + offset
        pixel[start_year + i] = np.array(arr[start:stop])
    return pixel


def get_pheno_sos(pixel: dict[int, np.ndarray], year: int):
    """Return the start-of-season index and the index of the seasonal maximum."""
    if not pixel[year].any():
        return -1, -1, 0

    try:
        idxs_max = argrelmax(pixel[year])[0]
        nr_max = idxs_max.size
        if nr_max == 0:
            idx_max = int(np.argmax(pixel[year]))
            if idx_max < 10:
                return -1, -1, 0
            nr_max = 1
        elif nr_max == 1:
            idx_max = int(idxs_max[0])
        else:
            idx_max = next(
                (m for m in idxs_max if abs(pixel[year][m]) >= abs(np.max(pixel[year]) * 0.4)),
                -1,
            )
            if idx_max == -1:
                return -1, -1, 0

        maximum = pixel[year][idx_max]
        idx_min = int(np.argmin(pixel[year][:idx_max]))
        minimum = pixel[year][idx_min]
        pix_20 = (maximum - minimum) * 0.2 + minimum
        idx_20 = int(np.abs(pixel[year][idx_min:idx_max] - pix_20).argmin() + idx_min)
        return idx_20, idx_max, nr_max
    except Exception:
        return -2, -2, 0


def get_pheno_eos(pixel: dict[int, np.ndarray], year: int, idx_max: int, offset: int = 0):
    """Return the end-of-season index."""
    if not pixel[year].any() or idx_max == -1:
        return -1

    try:
        idx_max -= offset
        idx_min = int(np.argmin(pixel[year][idx_max:]) + idx_max)
        minimum = pixel[year][idx_min]
        maximum = pixel[year][idx_max]
        pix_20 = (maximum - minimum) * 0.2 + minimum
        idx_20 = int(np.abs(pixel[year][idx_max:idx_min] - pix_20).argmin() + idx_max)
        return idx_20 + offset
    except Exception:
        return -1
