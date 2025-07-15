import numpy as np
from osgeo import gdal, osr


def tif2array(file_path: str, dtype=np.uint8):
    """Load a GeoTIFF into a NumPy array."""
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
    if dataset is None:
        raise FileNotFoundError(file_path)

    image = np.zeros(
        (dataset.RasterYSize, dataset.RasterXSize, dataset.RasterCount),
        dtype=dtype,
    )
    for b in range(dataset.RasterCount):
        band = dataset.GetRasterBand(b + 1)
        image[:, :, b] = band.ReadAsArray()

    return image, dataset


def array2raster(
    path: str,
    dataset,
    array: np.ndarray,
    dtype: str,
    offset_x: int = 0,
    offset_y: int = 0,
):
    """Save a NumPy array as a GeoTIFF using metadata from *dataset*."""
    cols, rows = array.shape[1], array.shape[0]
    origin_x, pixel_width, _, origin_y, _, pixel_height = dataset.GetGeoTransform()
    origin_x += offset_x
    origin_y += offset_y

    driver = gdal.GetDriverByName("GTiff")

    gdt = {
        "Byte": gdal.GDT_Byte,
        "Int16": gdal.GDT_Int16,
        "Float32": gdal.GDT_Float32,
    }.get(dtype, gdal.GDT_Unknown)
    if gdt == gdal.GDT_Unknown:
        raise ValueError(f"Unsupported dtype: {dtype}")

    band_num = 1 if array.ndim == 2 else array.shape[2]
    out_raster = driver.Create(path, cols, rows, band_num, gdt)
    out_raster.SetGeoTransform((origin_x, pixel_width, 0, origin_y, 0, pixel_height))

    for b in range(band_num):
        out_band = out_raster.GetRasterBand(b + 1)
        if band_num == 1:
            out_band.WriteArray(array)
        else:
            out_band.WriteArray(array[:, :, b])

    proj = dataset.GetProjection()
    out_raster_srs = osr.SpatialReference(wkt=proj)
    out_raster.SetProjection(out_raster_srs.ExportToWkt())
    out_band.FlushCache()
