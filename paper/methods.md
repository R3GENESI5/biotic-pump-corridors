# 2. Data and Methods

## 2.1 Study regions and corridor definition

We define two tropical moisture corridors based on the biotic pump framework (Makarieva and Gorshkov, 2007), each connecting an oceanic moisture source to a continental forest interior.

The **Amazon corridor** runs from Belém on the Atlantic coast (1.4°S, 48.5°W) westward through Marabá, Altamira, and Itaituba to Manaus (3.1°S, 60.0°W), a distance of approximately 1,300 km. We average variables over a latitude band of 6°S to 0°N to capture the full width of the moisture transport path. For spatial correlation analysis, we use a wider Eastern Amazon domain (10°S–2°N, 65°W–45°W), encompassing approximately 240 grid cells at 1-degree resolution.

The **Congo corridor** extends from the Gulf of Guinea coast near Douala (4.0°N, 9.7°E) eastward through Yaoundé, Ouesso, and Mbandaka to Kisangani (0.5°N, 25.2°E), covering approximately 1,700 km. We average over a latitude band of 3°S to 5°N.

Along each corridor, we define three segments for gradient analysis:

| Segment | Amazon (longitude) | Congo (longitude) |
|---------|-------------------|-------------------|
| Coast | 50°W–47°W | 8°E–12°E |
| Mid-corridor | 53°W–49°W | 15°E–20°E |
| Interior | 62°W–58°W | 22°E–27°E |

The coast-to-interior gradient is computed as the area-weighted mean of the interior segment minus the coast segment. A weakening of this gradient over time indicates reduced inland moisture transport, consistent with biotic pump degradation.

## 2.2 Satellite data

### 2.2.1 CERES EBAF-TOA

We use the Clouds and the Earth's Radiant Energy System (CERES) Energy Balanced and Filled (EBAF) Top-of-Atmosphere Edition 4.2.1 dataset (Loeb et al., 2018), which provides monthly gridded (1° × 1°) radiative fluxes from March 2000 through January 2026. Three variables are used:

- **All-sky outgoing longwave radiation (OLR)**: total longwave flux leaving the top of atmosphere. Increases in OLR indicate reduced cloud cover, reduced atmospheric moisture, or increased surface temperature — all signatures of weakened convection.
- **Clear-sky OLR**: the longwave flux that would exist in the absence of clouds, derived from cloud-free scenes.
- **Cloud area fraction**: the fraction of each grid cell covered by cloud, retrieved from day and night observations.

We derive the **longwave cloud radiative effect (CRE_LW)** as the difference between clear-sky and all-sky OLR:

CRE_LW = OLR_clear − OLR_all

Positive CRE values indicate that clouds reduce OLR by trapping longwave radiation. A decrease in CRE implies thinning or reduction of clouds.

### 2.2.2 MODIS evapotranspiration

Evapotranspiration (ET) is obtained from the Moderate Resolution Imaging Spectroradiometer (MODIS) Terra MOD16A3GF Version 061 product (Running et al., 2019), which provides gap-filled annual ET at 500 m spatial resolution in the MODIS sinusoidal tile projection. We download tiles covering the Amazon corridor (h12v09, h13v09) and the Congo corridor (h19v08, h19v09, h20v08, h20v09, h21v08, h21v09) for the years 2019 and 2023.

Tiles are reprojected from the sinusoidal grid to geographic coordinates (WGS84) by computing latitude and longitude for each pixel centre using the standard MODIS sinusoidal parameters (Earth radius 6,371,007.181 m, tile size 1,111,950.52 m). Fill values (65535) and unrealistic values (>3,000 mm/yr raw) are masked. Raw values are scaled by 0.1 to convert to mm/yr. For comparison with CERES, the 500 m data are aggregated to 1-degree resolution using 2D binned statistics (mean of all valid pixels within each 1° × 1° cell).

### 2.2.3 MODIS NDVI

Vegetation greenness is assessed using the MODIS Terra MOD13C2 Version 061 Climate Modeling Grid (CMG) product, which provides monthly Normalized Difference Vegetation Index (NDVI) at 0.05-degree global resolution. We download all monthly composites for 2019 (12 files) and 2023 (11 files) and compute annual means.

NDVI is used to distinguish drought-driven transpiration suppression from deforestation. Grid cells with NDVI > 0.6 in 2019 are classified as dense forest. NDVI change is then analysed separately for forest and non-forest cells. For comparison with ET and CERES variables, NDVI is spatially aggregated to 1-degree resolution by block-averaging (20 × 20 pixel blocks).

### 2.2.4 AIRS column water vapor

Atmospheric moisture is measured using the Atmospheric Infrared Sounder (AIRS) Level 3 Standard Monthly Retrieval product (AIRS3STM, Version 7.0; Tian et al., 2020), which provides total column water vapour at 1° × 1° resolution. We use the ascending orbit retrieval (TotH2OVap_A), which corresponds to daytime observations (~1:30 PM local time). Monthly files for all months of 2019 and 2023 are downloaded and averaged to produce annual means.

### 2.2.5 ENSO classification

The Oceanic Niño Index (ONI) is obtained from the NOAA Climate Prediction Center. ONI provides 3-month running mean SST anomalies in the Niño 3.4 region (5°N–5°S, 120°W–170°W). We compute the annual mean ONI for each year from 2001 to 2025 for use in regression analysis. Years are classified by the peak absolute ONI within the calendar year: El Niño (peak ONI ≥ 0.5), La Niña (peak ONI ≤ −0.5), or neutral.

## 2.3 Analysis methods

### 2.3.1 Corridor transects

For each variable, the corridor transect is computed by:
1. Selecting data within the corridor latitude band
2. Computing the cosine-latitude-weighted mean across all latitudes at each longitude
3. Plotting the resulting 1D profile as a function of longitude

This produces a single curve showing how each variable changes from coast to interior.

### 2.3.2 Seasonal decomposition

We compute seasonal means for four periods: DJF (wet season), MAM (wet-to-dry transition), JJA (dry season), and SON (dry-to-wet transition). For the Amazon, SON is the critical period when forest transpiration should initiate inland moisture convergence ahead of the ITCZ arrival (Wright et al., 2017). Seasonal changes (2023 minus 2019) are computed for each corridor transect.

### 2.3.3 Multi-year trends

Annual means of corridor metrics (coast-to-interior gradient for OLR, cloud fraction, and CRE) are computed for each year from 2001 to 2025. Linear trends are fitted using ordinary least squares.

### 2.3.4 ENSO control

To assess whether corridor trends are driven by ENSO rather than structural changes, we:
1. Compute the correlation between annual mean ONI and each corridor gradient metric
2. Regress each metric on ONI and analyse the residual time series
3. Fit linear trends to the ENSO-adjusted residuals
4. Report p-values for the residual trends

If the ENSO-adjusted trend remains significant, the corridor degradation cannot be attributed to ENSO variability.

### 2.3.5 Spatial correlation

To test the mechanistic link between ET decline and OLR increase at the grid-cell level, we compute the Pearson correlation between ET change and OLR change across all 1° × 1° cells in the wider Eastern Amazon domain. MODIS ET is aggregated to 1-degree resolution to match CERES. We report the correlation coefficient, p-value, and the fraction of cells in the "pump failure" quadrant (ET < 0 and OLR > 0).

### 2.3.6 Forest integrity assessment

To determine whether ET decline reflects drought stress in intact forest or land-cover change, we:
1. Classify cells as dense forest (2019 NDVI > 0.6) or non-forest (NDVI 0.2–0.6)
2. Compute NDVI change distributions separately for each class
3. Test whether forest NDVI change differs significantly from zero (one-sample t-test)
4. Report the fraction of forest cells showing NDVI decline
