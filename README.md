# Time Series Analysis of Satellite Imagery

This project uses the satellite imagery from the two MODIS Satellites to analyze the phenology of Georgia.
period 2010 to 2020

this project employs the Whittaker smoother implemented by Pesendorfer https://github.com/WFP-VAM/modape.

data obtained from

Phenology of Georgia (Caucasus). Phenology is derived from NDVI (Modis satellite).

`smothing` - loading satellite data and applying the Whittaker smoother on it

`calc_phenology` - calculate phenology parameters: SOS, MOS, EOS, LOS

`maps` - create plots
