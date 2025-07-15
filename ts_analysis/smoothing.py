import array
import math
from typing import Iterable

import numpy as np
from vam.whittaker import ws2doptv


def create_indices(num_images: int) -> np.ndarray:
    """Return indices to insert 16-day composites into a daily array."""
    idx_list = []
    full_years = math.floor(num_images / 46)
    rest_last_year = (round(num_images / 2) - full_years * 23) * 16

    # Aqua
    temp = 1
    for i in range(1, full_years + 1):
        idx_src = np.arange(temp, 365 * i, 16)
        idx_list.append(idx_src)
        temp += 365
    idx_list.append(np.arange(temp, temp + rest_last_year, 16))

    # Terra
    if num_images % 2:
        rest_last_year = (math.floor(num_images / 2) - full_years * 23) * 16
    temp = 9
    for i in range(1, full_years + 1):
        idx_src = np.arange(temp, 365 * i, 16)
        idx_list.append(idx_src)
        temp += 365
    idx_list.append(np.arange(temp, temp + rest_last_year, 16))

    return np.concatenate(idx_list)


def smooth_whittaker(
    image: Iterable[float],
    idx_src: np.ndarray,
    start_year: int,
    end_year: int,
) -> np.ndarray:
    """Smooth a pixel time series with the Whittaker filter."""
    a = np.asarray(image, dtype=float) / 10000
    a[a < np.quantile(a, 0.1)] = np.quantile(a, 0.1)

    whole_year = np.full(365 * (end_year - start_year + 1), -0.3)
    whole_year[idx_src - 1] = a

    w = (whole_year != -0.3).astype("double")
    lrange = array.array("d", np.linspace(0, 6, 100))

    z, _ = ws2doptv(whole_year, w, lrange)

    z = np.nan_to_num(np.array(z), nan=-0.3)
    z[z < -0.3] = -0.3
    z[z > 1] = 1
    return z
