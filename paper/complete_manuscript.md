# Satellite evidence for progressive weakening of condensation-driven moisture transport along tropical forest corridors

Ali Bin Shahid

Independent Scientist, Islamabad, Pakistan

---

## Abstract

The biotic pump hypothesis proposes that forest evapotranspiration drives condensation-generated low pressure that sustains inland moisture transport. We test this mechanism using 25 years of satellite data along two tropical moisture corridors: Belém–Manaus (Amazon) and Gulf of Guinea–Kisangani (Congo). Comparing 2019 with the 2023 drought, we find that outgoing longwave radiation (OLR) increased (+2.9 W/m² over the Eastern Amazon, +1.3 W/m² over the Congo), cloud fraction decreased (−2.3% Amazon, −0.5% Congo), evapotranspiration declined (−16 mm/yr Amazon), and column water vapour accumulated at the coast rather than penetrating inland — all signatures of weakened condensation-driven transport. These signals amplify with distance from the coast: interior OLR increased +4.3 W/m² versus +2.7 W/m² at the coast, and the coast-to-interior water vapour gradient steepened by −1.2 kg/m². The signal concentrates in the September–November dry-to-wet transition, when forest transpiration should initiate the wet season ahead of the Intertropical Convergence Zone; interior OLR during SON increased by +24.5 W/m². Over 2001–2025, the Amazon coast-to-interior cloud fraction gradient declined at −0.17%/yr (p = 0.001 after removing the ENSO signal using the Oceanic Niño Index, which explains less than 1% of gradient variance). NDVI analysis confirms that 88% of intact forest cells (NDVI > 0.6) experienced greenness decline (t = −15.4, p < 10⁻⁶), establishing that the evapotranspiration reduction reflects drought stress in standing forest, not land-cover change. The Congo corridor shows the same trends at weaker magnitudes, consistent with an earlier stage of degradation. These results provide spatially resolved satellite evidence for the biotic pump mechanism and document its progressive failure in the two largest tropical forests.

---

## 1. Introduction

Tropical forests cycle enormous quantities of water between the land surface and the atmosphere. In the Amazon basin, approximately half of the precipitation that falls on the forest is returned to the atmosphere through evapotranspiration, where it is available to generate precipitation further downwind (Salati et al., 1979; Eltahir and Bras, 1996). This moisture recycling sustains precipitation deep into the continental interior, far beyond the reach of oceanic moisture alone.

The mechanism by which this inland moisture transport is maintained remains debated. The prevailing view attributes it to large-scale pressure gradients driven by differential heating between the ocean and the continent (e.g., the South American monsoon system). However, Makarieva and Gorshkov (2007) proposed an alternative mechanism — the biotic pump — in which the condensation of water vapour itself generates the low-pressure anomaly that draws moist air inland. In this framework, forest evapotranspiration is not merely a consequence of available moisture but an active driver of the atmospheric circulation that delivers it.

The biotic pump hypothesis has been refined in subsequent theoretical work (Makarieva et al., 2013; Makarieva and Gorshkov, 2015) and finds indirect support from several lines of evidence. The Amazon wet season initiates before the southward migration of the Intertropical Convergence Zone (ITCZ), suggesting that vegetation-atmosphere interactions drive early convective onset (Li and Fu, 2004; Wright et al., 2017). The Eurasian boreal forest sustains inland moisture transport during the growing season that collapses during dormancy (Makarieva et al., 2009). Deforestation experiments in climate models consistently reduce precipitation in deforested regions and downwind (Spracklen et al., 2012; Staal et al., 2018; Nobre et al., 2016).

Despite this theoretical and modelling evidence, direct observational testing of the biotic pump at the corridor scale has been limited. If the biotic pump operates, its weakening should produce specific, observable satellite signatures: (1) reduced evapotranspiration, (2) decreased cloud cover, (3) increased outgoing longwave radiation, and (4) steepening of the coast-to-interior moisture gradient as oceanic moisture fails to penetrate inland. These signals should amplify with distance from the coast and concentrate in the seasonal transition periods when forest-driven convection, rather than the ITCZ, is the primary moisture driver.

The years 2019 and 2023 provide an opportunity for such a test. The Amazon and Congo basins experienced record or near-record drought in 2023 (Espinoza et al., 2024; Wongchuig et al., 2025), offering a natural experiment in which the biotic pump was stressed. By comparing satellite-derived atmospheric and surface variables between 2019 (a relatively normal year) and 2023 (drought), and placing this comparison within a 25-year satellite record, we can assess whether the predicted signatures appear, whether they follow the spatial and seasonal patterns the biotic pump framework predicts, and whether they constitute a trend or an isolated anomaly.

We focus on two corridors: the Belém–Manaus corridor in the Amazon, connecting the Atlantic coast to the western interior; and the Gulf of Guinea–Kisangani corridor in the Congo, connecting the oceanic moisture source to the interior of Africa's largest remaining rainforest. These corridors were selected because they run perpendicular to the coast and parallel to the prevailing low-level moisture transport, making them natural transects for testing coast-to-interior moisture relay.

Here we show that the predicted signatures of biotic pump weakening are present in satellite data from four independent instruments (CERES, MODIS, AIRS), that they amplify with distance from the coast, that they concentrate in the dry-to-wet transition season, and that they represent a progressive 25-year trend independent of ENSO variability. We further demonstrate that the ET decline reflects drought stress in intact forest rather than deforestation.

---

## 2. Data and Methods

### 2.1 Study regions and corridor definition

We define two tropical moisture corridors based on the biotic pump framework (Makarieva and Gorshkov, 2007), each connecting an oceanic moisture source to a continental forest interior.

The **Amazon corridor** runs from Belém on the Atlantic coast (1.4°S, 48.5°W) westward through Marabá, Altamira, and Itaituba to Manaus (3.1°S, 60.0°W), a distance of approximately 1,300 km. We average variables over a latitude band of 6°S to 0°N to capture the full width of the moisture transport path. For spatial correlation analysis, we use a wider Eastern Amazon domain (10°S–2°N, 65°W–45°W), encompassing approximately 240 grid cells at 1-degree resolution.

The **Congo corridor** extends from the Gulf of Guinea coast near Douala (4.0°N, 9.7°E) eastward through Yaoundé, Ouesso, and Mbandaka to Kisangani (0.5°N, 25.2°E), covering approximately 1,700 km. We average over a latitude band of 3°S to 5°N.

Along each corridor, we define three segments for gradient analysis:

| Segment | Amazon (longitude) | Congo (longitude) |
|---------|-------------------|-------------------|
| Coast | 50°W–47°W | 8°E–12°E |
| Mid-corridor | 53°W–49°W | 15°E–20°E |
| Interior | 62°W–58°W | 22°E–27°E |

The coast-to-interior gradient is computed as the area-weighted mean of the interior segment minus the coast segment. A weakening of this gradient over time indicates reduced inland moisture transport.

### 2.2 Satellite data

**CERES EBAF-TOA Edition 4.2.1** (Loeb et al., 2018) provides monthly gridded (1° × 1°) top-of-atmosphere radiative fluxes from March 2000 through January 2026. We use all-sky OLR, clear-sky OLR, and cloud area fraction. The longwave cloud radiative effect (CRE_LW) is derived as OLR_clear minus OLR_all; positive CRE indicates that clouds reduce OLR by trapping longwave radiation.

**MODIS MOD16A3GF Version 061** (Running et al., 2019) provides gap-filled annual evapotranspiration at 500 m in the MODIS sinusoidal projection. Tiles covering both corridors are downloaded for 2019 and 2023, reprojected to geographic coordinates, and aggregated to 1-degree resolution using 2D binned statistics. Fill values (65535) and unrealistic values (>3,000 mm/yr raw) are masked; raw values are scaled by 0.1 to mm/yr.

**MODIS MOD13C2 Version 061** provides monthly NDVI at 0.05-degree global resolution. All monthly composites for 2019 (12 files) and 2023 (11 files) are averaged annually. Grid cells with NDVI > 0.6 in 2019 are classified as dense forest. For comparison with 1-degree data, NDVI is block-averaged (20 × 20 pixels).

**AIRS L3 Version 7.0** (AIRS3STM; Tian et al., 2020) provides total column water vapour (ascending orbit, TotH2OVap_A) at 1° × 1° monthly resolution. All months for 2019 and 2023 are averaged annually.

**NOAA ONI** (Oceanic Niño Index) provides 3-month running mean SST anomalies in the Niño 3.4 region. We compute annual mean ONI for regression analysis and classify years by peak absolute ONI: El Niño (≥0.5), La Niña (≤−0.5), or neutral.

### 2.3 Analysis methods

**Corridor transects** are computed by selecting data within the corridor latitude band and calculating the cosine-latitude-weighted mean across latitudes at each longitude.

**Seasonal decomposition** uses four periods: DJF (wet season), MAM (wet-to-dry transition), JJA (dry season), and SON (dry-to-wet transition). SON is the critical period when forest transpiration should initiate inland moisture convergence ahead of the ITCZ (Wright et al., 2017).

**Multi-year trends** are computed from annual corridor gradient metrics over 2001–2025 using ordinary least squares.

**ENSO control** regresses each corridor metric on annual mean ONI and analyses residual trends. If the ENSO-adjusted trend remains significant, the corridor degradation cannot be attributed to ENSO.

**Spatial correlation** between ET change and OLR change is computed across all 1° × 1° cells in the wider Eastern Amazon, with MODIS ET aggregated to match CERES resolution.

**Forest integrity assessment** classifies cells by 2019 NDVI (>0.6 = dense forest), computes NDVI change distributions by class, and tests whether forest NDVI change differs from zero (one-sample t-test).

---

## 3. Results

### 3.1 Regional overview: 2019 versus 2023

Global mean OLR increased by 0.16 W/m² between 2019 and 2023. Against this background, the Eastern Amazon showed an OLR increase of +2.9 W/m² — 18 times the global mean — while the Congo Basin increased by +1.3 W/m² (Table 1). Cloud area fraction declined by 2.3% over the Eastern Amazon and 0.5% over the Congo. The longwave cloud radiative effect decreased by 1.5 W/m² (Amazon) and 0.7 W/m² (Congo), indicating reduced cloud trapping of longwave radiation.

MODIS evapotranspiration declined by 16 mm/yr (−1.1%) across the wider Eastern Amazon and by 66 mm/yr (−4.5%) in the Marabá subregion. In the Congo Basin, ET increased slightly (+13 mm/yr, +1.0%). The Eastern Amazon OLR difference map shows a spatially coherent pattern of increased OLR across nearly the entire domain, with the strongest signals in the arc from Marabá southwestward toward the interior (Figure 2).

**Table 1. Regional means and changes, 2019 vs 2023.**

| Variable | Amazon 2019 | Amazon 2023 | Change | Congo 2019 | Congo 2023 | Change |
|----------|------------|------------|--------|-----------|------------|--------|
| OLR (W/m²) | 236.6 | 239.5 | +2.9 | 220.6 | 221.9 | +1.3 |
| Cloud fraction (%) | 72.5 | 70.3 | −2.3 | 79.1 | 78.6 | −0.5 |
| CRE_LW (W/m²) | 44.6 | 43.0 | −1.5 | 55.4 | 54.6 | −0.7 |
| ET (mm/yr) | 1419 | 1403 | −16 | 1298 | 1310 | +13 |

Amazon ET values are for the wider Eastern Amazon domain (10°S–2°N, 65°W–45°W). In the Marabá subregion (7°S–3°S, 52°W–47°W), ET declined from 1459 to 1392 mm/yr (−66 mm/yr, −4.5%). Congo ET is for 5°S–5°N, 15°E–30°E.

### 3.2 Corridor transect analysis

Along the Belém–Manaus corridor, OLR increased at every longitude, but the increase was substantially larger in the interior (+4.3 W/m² near Manaus) than at the coast (+2.7 W/m² near Belém). The coast-to-interior OLR gradient weakened by +1.6 W/m², meaning the interior lost part of its convective advantage over the coast.

Cloud fraction decreased by 3.6% in the mid-corridor (Marabá–Altamira) — the largest decline along the corridor — while the interior showed a smaller decrease of 1.1%. The longwave CRE declined uniformly along the corridor, with the largest decreases at the interior (−2.4 W/m²).

AIRS column water vapour revealed a striking asymmetry: the coast gained moisture (+0.8 kg/m²) while the interior lost moisture (−0.4 kg/m²). The coast-to-interior water vapour gradient steepened by −1.2 kg/m², from −2.5 kg/m² in 2019 to −3.7 kg/m² in 2023 (Figure 3b). Moisture accumulated near the coast but failed to penetrate inland — the signature of weakened inland moisture transport.

Along the Congo corridor, OLR increased by +1.3 to +1.6 W/m² with a more uniform distribution (Figure 3c). Cloud fraction and CRE declined modestly. Water vapour changes were small and lacked the strong coast-interior asymmetry observed in the Amazon.

**Table 2. Corridor segment values for the Amazon, 2019 vs 2023.**

| Variable | Coast (Belém) | Change | Mid (Marabá) | Change | Interior (Manaus) | Change |
|----------|-------------|--------|-------------|--------|-----------------|--------|
| OLR (W/m²) | 241.5 → 244.2 | +2.70 | 240.5 → 243.2 | +2.76 | 225.9 → 230.2 | +4.26 |
| Cloud (%) | 70.9 → 68.3 | −2.55 | 74.7 → 71.0 | −3.64 | 78.4 → 77.2 | −1.14 |
| CRE (W/m²) | 42.2 → 40.3 | −1.94 | 41.3 → 39.0 | −2.39 | 52.7 → 50.3 | −2.43 |
| WV (kg/m²) | 48.9 → 49.7 | +0.82 | 49.1 → 49.3 | +0.21 | 46.4 → 46.0 | −0.41 |

### 3.3 Seasonal decomposition

The seasonal decomposition reveals that the dry-to-wet transition season (SON) dominates the annual signal (Figure 4). Interior OLR increased by +24.5 W/m² during SON, compared to +10.6 W/m² during JJA and −8.5 W/m² during DJF. Cloud fraction during SON declined by 9.0% at the interior, compared to 6.1% at the coast. AIRS water vapour during SON declined by 2.4 kg/m² at the interior with negligible change at the coast.

**Table 3. Seasonal OLR change (W/m²) along the Amazon corridor, 2023 minus 2019.**

| Season | Coast | Mid | Interior |
|--------|-------|-----|----------|
| DJF (wet) | +0.3 | −4.5 | −8.5 |
| MAM | −0.7 | −2.1 | −9.7 |
| JJA (dry) | +7.5 | +7.6 | +10.6 |
| SON (dry-to-wet) | +10.5 | +14.5 | +24.5 |

SON is the period when forest evapotranspiration should initiate inland moisture convergence ahead of the ITCZ (Wright et al., 2017; Fu et al., 2013). The concentration of the signal in this season implicates the forest-driven component of moisture convergence. During DJF, when the ITCZ provides geophysical forcing, the corridor partially recovered — interior OLR declined and water vapour increased. This seasonal contrast is difficult to explain by any mechanism other than reduced vegetation-driven moisture convergence.

The Congo showed a similar but weaker seasonal pattern, with JJA showing the largest OLR increase rather than SON, consistent with different monsoon dynamics over Central Africa.

### 3.4 Multi-year trends (2001–2025)

Over the 25-year CERES record, the Amazon corridor shows progressive gradient weakening (Figure 5). The cloud fraction gradient declined at −0.17%/yr, and the CRE gradient declined at −0.12 W/m²/yr. The OLR gradient increased at +0.07 W/m²/yr.

The year-by-year data show a ratchet pattern: drought years (2005, 2010, 2015, 2023) produce sharp gradient reductions, and recovery between events is incomplete. Interior cloud fraction was 82.7% in 2005 and had fallen to 77.2% by 2023, while the coast remained relatively stable (69–71%).

The Congo corridor shows trends in the same direction but smaller: OLR gradient +0.01 W/m²/yr, cloud fraction gradient −0.004%/yr, CRE gradient −0.07 W/m²/yr. None reach statistical significance individually.

### 3.5 ENSO independence

The correlation between annual mean ONI and the Amazon cloud fraction gradient is r = 0.015 (p = 0.94), explaining less than 1% of variance. After regressing out the ONI signal, the ENSO-adjusted trends are virtually unchanged from the raw trends (Table 4).

**Table 4. Amazon corridor gradient trends, raw and ENSO-adjusted.**

| Metric | Raw trend | ENSO-adjusted | p-value |
|--------|-----------|--------------|---------|
| Cloud fraction gradient | −0.170%/yr | −0.170%/yr | 0.001 |
| CRE gradient | −0.116 W/m²/yr | −0.117 W/m²/yr | 0.033 |
| OLR gradient | +0.074 W/m²/yr | +0.075 W/m²/yr | 0.201 |

Comparison of 2023 with other El Niño years shows that the 2023 corridor metrics are close to the El Niño ensemble mean rather than being anomalous outliers. The corridor degradation in 2023 reflects the continuation of a long-term trend, not an exceptional ENSO response.

### 3.6 Forest integrity: drought stress, not deforestation

Among 225 grid cells classified as dense forest (NDVI > 0.6 in 2019) in the wider Eastern Amazon, 88.4% showed NDVI decline between 2019 and 2023 (Figure 6). The mean NDVI change in forest cells was −0.009 (t = −15.4, p < 10⁻⁶). The six non-forest cells (NDVI 0.2–0.6) showed slight NDVI increase (+0.004).

The Congo Basin showed the opposite: NDVI in forest cells increased by +0.008 (t = +9.4, p < 10⁻⁶), with 78.5% of cells greening. This is consistent with the Congo maintaining its biotic pump function while the atmospheric response begins to weaken.

NDVI change and ET change are positively correlated across the Eastern Amazon (r = 0.29, p = 0.0006, n = 135), confirming that greenness decline predicts ET decline. The ET reduction reflects drought-driven transpiration suppression in standing forest, not land-cover change.

### 3.7 Spatial correlation between ET and OLR

Across 159 grid cells in the wider Eastern Amazon, ET change and OLR change are positively correlated (r = 0.32, p < 0.0001; Figure 7). Cells where ET declined more experienced larger OLR increases. Forty-seven percent of cells fall in the "pump failure" quadrant (ET < 0, OLR > 0).

The explained variance (r² = 0.10) is modest, reflecting that OLR responds to the entire atmospheric column and moisture transported from upwind cells, not solely to local ET. The biotic pump operates at circulation scale; the corridor-scale analyses in Sections 3.2–3.4 provide a more appropriate spatial framework for the mechanism.

---

## 4. Discussion

### 4.1 Satellite signatures of the biotic pump

The biotic pump hypothesis predicts that weakening of forest evapotranspiration should produce four observable consequences: reduced ET, thinning clouds, increased OLR, and steepened coast-to-interior moisture gradients. Our results show all four along the Belém–Manaus corridor, and critically, the signals amplify with distance from the coast. Interior OLR increased +4.3 W/m² versus +2.7 W/m² at the coast; interior water vapour declined −0.4 kg/m² while the coast gained +0.8 kg/m².

This spatial pattern — signal amplification with distance from the moisture source — is the distinctive signature of a transport failure mechanism. A spatially uniform forcing (increased CO₂, SST changes) would produce more uniform changes along the corridor. The steepening water vapour gradient is particularly diagnostic: oceanic evaporation continues, but the atmospheric circulation that transports this moisture inland is diminished.

### 4.2 The SON transition: where the biotic pump operates

The seasonal decomposition strengthens the case for biotic pump involvement. The corridor signal concentrates in SON — when interior OLR increased +24.5 W/m², an order of magnitude larger than the annual mean. Multiple studies document that the Amazon wet season begins before the ITCZ arrives (Li and Fu, 2004; Wright et al., 2017), driven by transpiration-induced boundary-layer moistening. Our data show that in 2023 this initiation mechanism failed at the interior end of the corridor.

During DJF, when the ITCZ provides geophysical forcing, the corridor partially recovered. This seasonal contrast — biotic pump failure in SON, geophysical compensation in DJF — is difficult to explain by any mechanism other than reduced vegetation-driven moisture convergence.

### 4.3 A progressive trend, not a single event

The 25-year record reveals that 2023 is not isolated but part of a multi-decadal degradation. The Amazon cloud fraction gradient declined at −0.17%/yr (p = 0.001 ENSO-adjusted). The year-by-year data show a ratchet: drought events produce sharp gradient reductions from which the corridor only partially recovers. Between 2005 and 2023, interior cloud fraction fell from 82.7% to 77.2%.

This pattern is consistent with a positive feedback: drought reduces transpiration, weakening the condensation-driven pressure gradient, reducing inland moisture transport, and exacerbating drought. Such feedbacks have been proposed in tipping point studies (Lenton et al., 2008; Staal et al., 2020; Zemp et al., 2017) but have not previously been documented in satellite observations of the specific atmospheric variables predicted by the biotic pump framework.

### 4.4 Amazon and Congo: different stages of degradation

The two corridors show degradation in the same direction but at different magnitudes. The Amazon exhibits strong inland amplification, significant long-term trends, and declining ET and NDVI. The Congo shows uniform modest changes, stable ET, and increased NDVI.

We interpret the Congo as occupying an earlier position on the same degradation trajectory. The Amazon has experienced greater deforestation and more frequent severe droughts, placing it further along the feedback loop. The Congo's declining CRE gradient (−0.07 W/m²/yr, not individually significant) suggests the atmospheric response is beginning to decouple from the still-active forest, as occurred earlier in the Amazon.

### 4.5 Moisture displacement and extreme weather

During September 2023, OLR showed positive anomalies of +12.5 W/m² over the Amazon and +5.0 W/m² over the Congo (relative to 2001–2018), while the eastern Mediterranean showed negative anomalies (−4.6 W/m²) coinciding with Storm Daniel. A similar dipole appeared in September 2024 with Storm Boris over Central Europe. We note this spatial coincidence as a hypothesis for future investigation requiring moisture trajectory analysis (e.g., HYSPLIT) rather than a claim of causation.

### 4.6 Limitations

The 2019–2023 comparison captures the drought signal but does not characterise full interannual variability; the 25-year trend analysis partially addresses this for CERES variables. CERES at 1-degree resolution cannot resolve sub-grid processes. The MODIS ET product (MOD16A3GF) has known biases in tropical forests (Mu et al., 2011). While we control for ENSO, other climate modes (AMO, IOD) could contribute. Satellite observations alone cannot establish causality; confirming the direction of causation requires Earth system model experiments.

---

## 5. Conclusions

1. Four independent satellite instruments show a spatially coherent weakening of moisture transport along the Belém–Manaus and Gulf of Guinea–Kisangani corridors between 2019 and 2023, consistent with biotic pump predictions.

2. Signals amplify with distance from the coast: interior OLR increased +4.3 W/m² versus +2.7 W/m² at the coast; the AIRS water vapour gradient steepened by −1.2 kg/m².

3. The breakdown concentrates in September–November, when forest transpiration should initiate the wet season. Interior OLR during SON increased +24.5 W/m²; the wet season (DJF) showed partial recovery from geophysical forcing.

4. The Amazon corridor has undergone progressive weakening over 25 years. The cloud fraction gradient trend (−0.17%/yr, p = 0.001) and CRE gradient trend (−0.12 W/m²/yr, p = 0.033) are statistically significant after ENSO removal.

5. NDVI confirms that 88% of intact forest cells experienced greenness decline (t = −15.4, p < 10⁻⁶), establishing drought stress in standing forest, not deforestation.

6. The Congo corridor shows the same trends at weaker magnitudes, consistent with an earlier degradation stage.

7. A spatial dipole during September 2023 — OLR surplus over tropical forests, deficit over the Mediterranean — coincides with Storm Daniel and warrants investigation through moisture trajectory analysis.

These findings constitute the first spatially resolved, multi-instrument satellite documentation of biotic pump weakening along defined moisture corridors, and indicate that condensation-driven circulation in the two largest tropical forests is progressively deteriorating.

---

## Data availability

CERES EBAF-TOA Ed4.2.1 is available from the NASA Langley Research Center Atmospheric Science Data Center (https://ceres.larc.nasa.gov/). MODIS MOD16A3GF and MOD13C2 are available from the NASA Land Processes DAAC (https://lpdaac.usgs.gov/). AIRS L3 data are available from the NASA GES DISC (https://disc.gsfc.nasa.gov/). ONI data are available from the NOAA Climate Prediction Center (https://www.cpc.ncep.noaa.gov/). All data were accessed through NASA Earthdata (https://earthdata.nasa.gov/). Analysis code is available at [repository to be created].

---

## References

Espinoza, J. C., Jimenez, J. C., Marengo, J. A., Schongart, J., Ronchail, J., Lavado-Casimiro, W., and Ribeiro, J. V. M. (2024). The new record of drought and warmth in the Amazon in 2023 related to regional and global climatic features. Scientific Reports, 14, 8107. https://doi.org/10.1038/s41598-024-58782-5

Eltahir, E. A. B. and Bras, R. L. (1996). Precipitation recycling in the Amazon basin. Quarterly Journal of the Royal Meteorological Society, 122, 539–555.

Fu, R., Yin, L., Li, W., et al. (2013). Increased dry-season length over southern Amazonia in recent decades and its implication for future climate projection. Proceedings of the National Academy of Sciences, 110, 18110–18115.

Lenton, T. M., Held, H., Kriegler, E., et al. (2008). Tipping elements in the Earth's climate system. Proceedings of the National Academy of Sciences, 105, 1786–1793.

Li, W. and Fu, R. (2004). Transition of the large-scale atmospheric and land surface conditions from the dry to the wet season over Amazonia as diagnosed by the ECMWF re-analysis. Journal of Climate, 17, 2637–2651.

Loeb, N. G., Doelling, D. R., Wang, H., et al. (2018). Clouds and the Earth's Radiant Energy System (CERES) Energy Balanced and Filled (EBAF) Top-of-Atmosphere (TOA) Edition-4.0 Data Product. Journal of Climate, 31, 895–918.

Makarieva, A. M. and Gorshkov, V. G. (2007). Biotic pump of atmospheric moisture as driver of the hydrological cycle on land. Hydrology and Earth System Sciences, 11, 1013–1033.

Makarieva, A. M. and Gorshkov, V. G. (2015). Meridional distribution of zonal winds and the biotic pump concept. In: The Role of Forests in Climate and Precipitation.

Makarieva, A. M., Gorshkov, V. G., and Li, B.-L. (2009). Precipitation on land versus distance from the ocean: evidence for a forest pump of atmospheric moisture. Ecological Complexity, 6, 302–307.

Makarieva, A. M., Gorshkov, V. G., Sheil, D., Nobre, A. D., and Li, B.-L. (2013). Where do winds come from? A new theory on how water vapor condensation influences atmospheric pressure and dynamics. Atmospheric Chemistry and Physics, 13, 1039–1056.

Mu, Q., Zhao, M., and Running, S. W. (2011). Improvements to a MODIS global terrestrial evapotranspiration algorithm. Remote Sensing of Environment, 115, 1781–1800.

Nobre, C. A., Sampaio, G., Borma, L. S., et al. (2016). Land-use and climate change risks in the Amazon and the need of a novel sustainable development paradigm. Proceedings of the National Academy of Sciences, 113, 10759–10768.

Running, S. W., Mu, Q., Zhao, M., and Moreno, A. (2019). MODIS Global Terrestrial Evapotranspiration (ET) Product (MOD16A2/A3) NASA Earth Observing System MODIS Land Algorithm. User's Guide, Collection 6.1.

Salati, E., Dall'Olio, A., Matsui, E., and Gat, J. R. (1979). Recycling of water in the Amazon basin: an isotopic study. Water Resources Research, 15, 1250–1258.

Spracklen, D. V., Arnold, S. R., and Taylor, C. M. (2012). Observations of increased tropical rainfall preceded by air passage over forests. Nature, 489, 282–285.

Staal, A., Tuinenburg, O. A., Bosmans, J. H. C., et al. (2018). Forest-rainfall cascades buffer against drought across the Amazon. Nature Climate Change, 8, 539–543.

Staal, A., Fetzer, I., Wang-Erlandsson, L., et al. (2020). Hysteresis of tropical forests in the 21st century. Nature Communications, 11, 4978.

Stein, A. F., Draxler, R. R., Rolph, G. D., Stunder, B. J. B., Cohen, M. D., and Ngan, F. (2015). NOAA's HYSPLIT atmospheric transport and dispersion modeling system. Bulletin of the American Meteorological Society, 96, 2059–2077.

Tian, B., Manning, E., Fetzer, E., Olsen, E., Blaisdell, J., and the AIRS Science Team (2020). AIRS/Aqua L3 Monthly Standard Physical Retrieval (AIRS-only) V7.0. NASA Goddard Earth Science Data and Information Services Center.

Wongchuig, S., Papa, F., Fleischmann, A. S., Sierra, J. P., Boucharel, J., Espinoza, J. C., Kitambo, B., Oliveira, R. J., Paris, A., Paiva, R., Casas, P., and Tshimanga, R. (2025). Recent significant drying in Central Congo Basin linked to weakened Walker circulation and warmer Atlantic. npj Climate and Atmospheric Science, 8, 331. https://doi.org/10.1038/s41612-025-01225-3

Wright, J. S., Fu, R., Worden, J. R., et al. (2017). Rainforest-initiated wet season onset over the southern Amazon. Proceedings of the National Academy of Sciences, 114, 8481–8486.

Zemp, D. C., Schleussner, C. F., Barbosa, H. M. J., et al. (2017). Self-amplified Amazon forest loss due to vegetation-atmosphere feedbacks. Nature Communications, 8, 14681.
