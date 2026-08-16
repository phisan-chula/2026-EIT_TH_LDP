# LDP Quality Control & Validation Summary

This report provides a comparative analysis of distances calculated across various map projections and surfaces. By establishing the **Ground Distance (L2)** as the true baseline of length 1,000.000 meter, we measure the linear distortion introduced by standard UTM grids against the custom Low Distortion Projections (LDP).

## --- Distance Definitions ---

| Line   | LineDescr                                   |
|:-------|:--------------------------------------------|
| L1     | on ellipsoid surface                        |
| L2     | on ellipsoid surface , HSF applied (Ground) |
| L3     | on UTM grid                                 |
| L4     | on UTM grid , PSF applied                   |
| L5     | on UTM grid , PSF&HSF (CSF) applied         |
| L6     | on LDP grid                                 |

---

### 🧭 Province: Amnat Charoen (TH.AC)

| P1 | (15.908945085, 104.730609023) | P2 | (15.917981953, 104.730609023) |
|:---|:---|:---|:---|
| MSL | 186 | HAE | 163 |
| P1_LDP | (47923.528, 149595.508) | P2_LDP | (47923.621, 150595.524) |
| P1_LDP_CSF | -9.8 ppm | P2_LDP_CSF | -9.4 ppm |
| P1_UTM_CSF | -415.5 ppm | P2_UTM_CSF | -415.2 ppm |

> **LDP Definition:**
> `+proj=tmerc +lat_0=0.0 +lon_0=104.75000000 +k_0=1.000016 +x_0=50000 +y_0=-1610000 +ellps=WGS84 +units=m +no_defs +type=crs`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.026 | *0.000 | -0.415 | -0.026 | -0.000 | -0.010 |

---

### 🧭 Province: Ang Thong (TH.AT)

| P1 | (14.618255615, 100.353729586) | P2 | (14.627293523, 100.353729586) |
|:---|:---|:---|:---|
| MSL | 6 | HAE | -26 |
| P1_LDP | (50401.820, 146745.925) | P2_LDP | (50401.804, 147745.922) |
| P1_LDP_CSF | +1.0 ppm | P2_LDP_CSF | +1.1 ppm |
| P1_UTM_CSF | -133.1 ppm | P2_UTM_CSF | -133.0 ppm |

> **LDP Definition:**
> `+proj=tmerc +lat_0=0.0 +lon_0=100.35000000 +k_0=0.999997 +x_0=50000 +y_0=-1470000 +ellps=WGS84 +units=m +no_defs +type=crs`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.133 | +0.004 | -0.000 | +0.001 |

---

### 🧭 Province: Bueng Kan (TH.BK)

| P1 | (18.107055664, 103.704676551) | P2 | (18.116090584, 103.704676551) |
|:---|:---|:---|:---|
| MSL | 177 | HAE | 147 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -190.3 ppm | P2_UTM_CSF | -191.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.023 | *0.000 | -0.191 | -0.023 | -0.000 | NaN |

---

### 🧭 Province: Buri Ram (TH.BR)

| P1 | (14.961830616, 103.065677419) | P2 | (14.970868255, 103.065677419) |
|:---|:---|:---|:---|
| MSL | 159 | HAE | 133 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +114.0 ppm | P2_UTM_CSF | +114.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.021 | *0.000 | +0.114 | -0.021 | -0.000 | NaN |

---

### 🧭 Province: Chon Buri (TH.CB)

| P1 | (13.096534500, 101.226437609) | P2 | (13.105573529, 101.226437609) |
|:---|:---|:---|:---|
| MSL | 102 | HAE | 74 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +309.2 ppm | P2_UTM_CSF | +309.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.012 | *0.000 | +0.309 | -0.012 | -0.000 | NaN |

---

### 🧭 Province: Chachoengsao (TH.CC)

| P1 | (13.576500894, 101.564268898) | P2 | (13.585539581, 101.564268898) |
|:---|:---|:---|:---|
| MSL | 36 | HAE | 10 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +551.5 ppm | P2_UTM_CSF | +550.8 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.002 | *0.000 | +0.551 | -0.002 | -0.000 | NaN |

---

### 🧭 Province: Chiang Mai Central (TH.CM_C)

| P1 | (18.783956386, 98.996828708) | P2 | (18.792990662, 98.996828708) |
|:---|:---|:---|:---|
| MSL | 307 | HAE | 269 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -442.2 ppm | P2_UTM_CSF | -442.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.042 | *0.000 | -0.442 | -0.042 | -0.000 | NaN |

---

### 🧭 Province: Chiang Mai North (TH.CM_N)

| P1 | (19.571161271, 98.919901123) | P2 | (19.580194773, 98.919901123) |
|:---|:---|:---|:---|
| MSL | 534 | HAE | 496 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -472.2 ppm | P2_UTM_CSF | -481.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.078 | *0.000 | -0.477 | -0.078 | -0.000 | NaN |

---

### 🧭 Province: Chiang Mai South (TH.CM_S)

| P1 | (17.777851105, 98.327666178) | P2 | (17.786886331, 98.327666178) |
|:---|:---|:---|:---|
| MSL | 989 | HAE | 951 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -498.2 ppm | P2_UTM_CSF | -475.1 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.149 | *0.000 | -0.487 | -0.149 | -0.000 | NaN |

---

### 🧭 Province: Chai Nat (TH.CN)

| P1 | (15.159755708, 100.038590182) | P2 | (15.168793189, 100.038590182) |
|:---|:---|:---|:---|
| MSL | 15 | HAE | -18 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -243.2 ppm | P2_UTM_CSF | -243.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.003 | *0.000 | -0.243 | +0.003 | -0.000 | NaN |

---

### 🧭 Province: Chumphon (TH.CP)

| P1 | (10.495293501, 99.182428377) | P2 | (10.504334180, 99.182428377) |
|:---|:---|:---|:---|
| MSL | 5 | HAE | -23 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -391.4 ppm | P2_UTM_CSF | -391.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.391 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Chiang Rai (TH.CR)

| P1 | (19.730527000, 99.884747529) | P2 | (19.739560342, 99.884747529) |
|:---|:---|:---|:---|
| MSL | 449 | HAE | 412 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -354.8 ppm | P2_UTM_CSF | -362.1 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.065 | *0.000 | -0.358 | -0.065 | -0.000 | NaN |

---

### 🧭 Province: Chanthaburi (TH.CT)

| P1 | (12.606762681, 102.109444341) | P2 | (12.615802047, 102.109444341) |
|:---|:---|:---|:---|
| MSL | 9 | HAE | -15 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +823.0 ppm | P2_UTM_CSF | +822.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.002 | *0.000 | +0.823 | +0.002 | -0.000 | NaN |

---

### 🧭 Province: Chaiyaphum (TH.CY)

| P1 | (16.021924973, 101.842337611) | P2 | (16.030961746, 101.842337611) |
|:---|:---|:---|:---|
| MSL | 237 | HAE | 207 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +712.0 ppm | P2_UTM_CSF | +711.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.033 | *0.000 | +0.712 | -0.033 | -0.000 | NaN |

---

### 🧭 Province: GreaterBKK (TH.GBKK)

| P1 | (13.808650971, 100.630963241) | P2 | (13.817689489, 100.630963241) |
|:---|:---|:---|:---|
| MSL | 2 | HAE | -28 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -11.1 ppm | P2_UTM_CSF | -11.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.011 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Khon Kaen (TH.KK)

| P1 | (16.359140397, 102.679125790) | P2 | (16.368176884, 102.679125790) |
|:---|:---|:---|:---|
| MSL | 167 | HAE | 138 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +338.2 ppm | P2_UTM_CSF | +338.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.022 | *0.000 | +0.338 | -0.022 | -0.000 | NaN |

---

### 🧭 Province: Kalasin (TH.KL)

| P1 | (16.639864923, 103.685787417) | P2 | (16.648901168, 103.685787417) |
|:---|:---|:---|:---|
| MSL | 198 | HAE | 171 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -183.1 ppm | P2_UTM_CSF | -184.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.027 | *0.000 | -0.184 | -0.027 | -0.000 | NaN |

---

### 🧭 Province: Kanchanaburi North (TH.KN_N)

| P1 | (14.742796524, 98.631634064) | P2 | (14.751834335, 98.631634064) |
|:---|:---|:---|:---|
| MSL | 90 | HAE | 53 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -390.6 ppm | P2_UTM_CSF | -387.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.008 | *0.000 | -0.389 | -0.008 | -0.000 | NaN |

---

### 🧭 Province: Kanchanaburi South (TH.KN_S)

| P1 | (14.285061837, 99.440797329) | P2 | (14.294100000, 99.440797329) |
|:---|:---|:---|:---|
| MSL | 103 | HAE | 69 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -382.2 ppm | P2_UTM_CSF | -383.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.011 | *0.000 | -0.383 | -0.011 | -0.000 | NaN |

---

### 🧭 Province: Kamphaeng Phet (TH.KP)

| P1 | (16.382061005, 99.511344260) | P2 | (16.391097473, 99.511344260) |
|:---|:---|:---|:---|
| MSL | 83 | HAE | 47 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -371.6 ppm | P2_UTM_CSF | -369.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.007 | *0.000 | -0.371 | -0.007 | -0.000 | NaN |

---

### 🧭 Province: Krabi (TH.KR)

| P1 | (8.166850764, 99.021201992) | P2 | (8.175892624, 99.021201992) |
|:---|:---|:---|:---|
| MSL | 77 | HAE | 55 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -404.7 ppm | P2_UTM_CSF | -412.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.009 | *0.000 | -0.409 | -0.009 | -0.000 | NaN |

---

### 🧭 Province: Lop Buri (TH.LB)

| P1 | (14.814306985, 100.646482240) | P2 | (14.823344740, 100.646482240) |
|:---|:---|:---|:---|
| MSL | 18 | HAE | -13 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -9.6 ppm | P2_UTM_CSF | -9.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.002 | *0.000 | -0.010 | +0.002 | -0.000 | NaN |

---

### 🧭 Province: Loei (TH.LE)

| P1 | (17.484251500, 101.644848339) | P2 | (17.493286995, 101.644848339) |
|:---|:---|:---|:---|
| MSL | 281 | HAE | 250 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +535.6 ppm | P2_UTM_CSF | +536.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.039 | *0.000 | +0.536 | -0.039 | -0.000 | NaN |

---

### 🧭 Province: Lampang North (TH.LG_N)

| P1 | (18.950120867, 99.664755489) | P2 | (18.959154982, 99.664755489) |
|:---|:---|:---|:---|
| MSL | 387 | HAE | 350 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -395.9 ppm | P2_UTM_CSF | -393.1 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.055 | *0.000 | -0.395 | -0.055 | -0.000 | NaN |

---

### 🧭 Province: Lampang South (TH.LG_S)

| P1 | (17.940085501, 99.312005600) | P2 | (17.949120576, 99.312005600) |
|:---|:---|:---|:---|
| MSL | 253 | HAE | 215 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -417.2 ppm | P2_UTM_CSF | -423.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.034 | *0.000 | -0.420 | -0.034 | -0.000 | NaN |

---

### 🧭 Province: Lamphun (TH.LN)

| P1 | (18.572154410, 99.016480438) | P2 | (18.581188890, 99.016480438) |
|:---|:---|:---|:---|
| MSL | 293 | HAE | 255 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -440.1 ppm | P2_UTM_CSF | -439.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.040 | *0.000 | -0.440 | -0.040 | -0.000 | NaN |

---

### 🧭 Province: Mukdahan North (TH.MD_N)

| P1 | (16.586237947, 104.414155530) | P2 | (16.595274239, 104.414155530) |
|:---|:---|:---|:---|
| MSL | 176 | HAE | 152 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -375.1 ppm | P2_UTM_CSF | -375.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.024 | *0.000 | -0.376 | -0.024 | -0.000 | NaN |

---

### 🧭 Province: Mukdahan South (TH.MD_S)

| P1 | (16.505025864, 104.602207551) | P2 | (16.514062226, 104.602207551) |
|:---|:---|:---|:---|
| MSL | 176 | HAE | 152 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -402.4 ppm | P2_UTM_CSF | -400.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.024 | *0.000 | -0.402 | -0.024 | -0.000 | NaN |

---

### 🧭 Province: Mae Hong Son North (TH.MH_N)

| P1 | (19.299814291, 97.967296424) | P2 | (19.308848063, 97.967296424) |
|:---|:---|:---|:---|
| MSL | 254 | HAE | 213 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -288.1 ppm | P2_UTM_CSF | -288.0 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.034 | *0.000 | -0.288 | -0.034 | -0.000 | NaN |

---

### 🧭 Province: Mae Hong Son South (TH.MH_S)

| P1 | (18.153975488, 97.919078600) | P2 | (18.163010364, 97.919078600) |
|:---|:---|:---|:---|
| MSL | 208 | HAE | 167 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -263.9 ppm | P2_UTM_CSF | -265.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.026 | *0.000 | -0.265 | -0.026 | -0.000 | NaN |

---

### 🧭 Province: Maha Sarakham (TH.MS)

| P1 | (16.023321152, 103.180173421) | P2 | (16.032357924, 103.180173421) |
|:---|:---|:---|:---|
| MSL | 175 | HAE | 147 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +45.3 ppm | P2_UTM_CSF | +46.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.023 | *0.000 | +0.046 | -0.023 | -0.000 | NaN |

---

### 🧭 Province: Nan (TH.NA)

| P1 | (18.821559906, 100.795544322) | P2 | (18.830594146, 100.795544322) |
|:---|:---|:---|:---|
| MSL | 226 | HAE | 191 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +11.9 ppm | P2_UTM_CSF | +13.1 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.030 | *0.000 | +0.013 | -0.030 | -0.000 | NaN |

---

### 🧭 Province: Nong Bua Lam Phu (TH.NB)

| P1 | (17.221394540, 102.308051529) | P2 | (17.230430271, 102.308051529) |
|:---|:---|:---|:---|
| MSL | 226 | HAE | 195 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +582.7 ppm | P2_UTM_CSF | +582.8 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.031 | *0.000 | +0.583 | -0.031 | -0.000 | NaN |

---

### 🧭 Province: Nakhon Phanom (TH.NF)

| P1 | (17.404781457, 104.601900645) | P2 | (17.413817024, 104.601900645) |
|:---|:---|:---|:---|
| MSL | 181 | HAE | 155 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -401.9 ppm | P2_UTM_CSF | -402.8 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.024 | *0.000 | -0.402 | -0.024 | -0.000 | NaN |

---

### 🧭 Province: Nong Khai (TH.NK)

| P1 | (17.946799278, 103.121630574) | P2 | (17.955834348, 103.121630574) |
|:---|:---|:---|:---|
| MSL | 171 | HAE | 140 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +68.0 ppm | P2_UTM_CSF | +66.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.022 | *0.000 | +0.067 | -0.022 | -0.000 | NaN |

---

### 🧭 Province: Nakhon Nayok (TH.NN)

| P1 | (14.235105515, 101.163736727) | P2 | (14.244143715, 101.163736727) |
|:---|:---|:---|:---|
| MSL | 7 | HAE | -22 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +277.9 ppm | P2_UTM_CSF | +277.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.003 | *0.000 | +0.278 | +0.003 | -0.000 | NaN |

---

### 🧭 Province: Nakhon Pathom (TH.NP)

| P1 | (13.927530290, 100.097617915) | P2 | (13.936568720, 100.097617915) |
|:---|:---|:---|:---|
| MSL | 4 | HAE | -28 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -221.7 ppm | P2_UTM_CSF | -221.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.222 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Nakhon Ratchasima North (TH.NR_N)

| P1 | (15.303785324, 102.544819760) | P2 | (15.312822689, 102.544819760) |
|:---|:---|:---|:---|
| MSL | 151 | HAE | 123 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +440.4 ppm | P2_UTM_CSF | +440.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.019 | *0.000 | +0.440 | -0.019 | -0.000 | NaN |

---

### 🧭 Province: Nakhon Ratchasima South (TH.NR_S)

| P1 | (14.791004659, 101.897458214) | P2 | (14.800042432, 101.897458214) |
|:---|:---|:---|:---|
| MSL | 236 | HAE | 208 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +770.5 ppm | P2_UTM_CSF | +770.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.033 | *0.000 | +0.771 | -0.033 | -0.000 | NaN |

---

### 🧭 Province: Nakhon Sawan (TH.NS)

| P1 | (15.625284519, 100.382240797) | P2 | (15.634321622, 100.382240797) |
|:---|:---|:---|:---|
| MSL | 27 | HAE | -6 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -127.6 ppm | P2_UTM_CSF | -127.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.001 | *0.000 | -0.128 | +0.001 | -0.000 | NaN |

---

### 🧭 Province: Nakhon Si Thammarat (TH.NT)

| P1 | (8.435683051, 99.965222277) | P2 | (8.444724790, 99.965222277) |
|:---|:---|:---|:---|
| MSL | 4 | HAE | -15 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -257.9 ppm | P2_UTM_CSF | -257.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.002 | *0.000 | -0.258 | +0.002 | -0.000 | NaN |

---

### 🧭 Province: Narathiwat (TH.NW)

| P1 | (6.186444998, 101.731835753) | P2 | (6.195487637, 101.731835753) |
|:---|:---|:---|:---|
| MSL | 33 | HAE | 25 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +727.2 ppm | P2_UTM_CSF | +728.0 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.004 | *0.000 | +0.728 | -0.004 | -0.000 | NaN |

---

### 🧭 Province: Phra Nakhon Si Ayutthaya (TH.PA)

| P1 | (14.391656398, 100.537043980) | P2 | (14.400694480, 100.537043980) |
|:---|:---|:---|:---|
| MSL | 5 | HAE | -27 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -56.1 ppm | P2_UTM_CSF | -56.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.056 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Prachin Buri (TH.PB)

| P1 | (14.021255970, 101.574246969) | P2 | (14.030294331, 101.574246969) |
|:---|:---|:---|:---|
| MSL | 16 | HAE | -11 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +558.0 ppm | P2_UTM_CSF | +558.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.002 | *0.000 | +0.558 | +0.002 | -0.000 | NaN |

---

### 🧭 Province: Phichit (TH.PC)

| P1 | (16.278190613, 100.346709714) | P2 | (16.287227170, 100.346709714) |
|:---|:---|:---|:---|
| MSL | 34 | HAE | 0 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -143.9 ppm | P2_UTM_CSF | -144.0 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.000 | *0.000 | -0.144 | +0.000 | -0.000 | NaN |

---

### 🧭 Province: Phetchaburi (TH.PE)

| P1 | (12.941589833, 99.602542845) | P2 | (12.950628970, 99.602542845) |
|:---|:---|:---|:---|
| MSL | 95 | HAE | 64 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -357.2 ppm | P2_UTM_CSF | -357.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.010 | *0.000 | -0.357 | -0.010 | -0.000 | NaN |

---

### 🧭 Province: Phangnga (TH.PG)

| P1 | (8.739158500, 98.418793197) | P2 | (8.748200096, 98.418793197) |
|:---|:---|:---|:---|
| MSL | 12 | HAE | -15 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -347.4 ppm | P2_UTM_CSF | -346.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.002 | *0.000 | -0.347 | +0.002 | -0.000 | NaN |

---

### 🧭 Province: Phetchabun (TH.PH)

| P1 | (16.415922956, 101.154151924) | P2 | (16.424959395, 101.154151924) |
|:---|:---|:---|:---|
| MSL | 118 | HAE | 87 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +240.9 ppm | P2_UTM_CSF | +240.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.014 | *0.000 | +0.241 | -0.014 | -0.000 | NaN |

---

### 🧭 Province: Pattani (TH.PI)

| P1 | (6.750622035, 101.321823708) | P2 | (6.759664473, 101.321823708) |
|:---|:---|:---|:---|
| MSL | 9 | HAE | -2 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +415.7 ppm | P2_UTM_CSF | +415.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.000 | *0.000 | +0.416 | +0.000 | -0.000 | NaN |

---

### 🧭 Province: Prachuap Khiri Khan (TH.PK)

| P1 | (11.803724729, 99.724467640) | P2 | (11.812764621, 99.724467640) |
|:---|:---|:---|:---|
| MSL | 59 | HAE | 31 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -327.4 ppm | P2_UTM_CSF | -328.1 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.005 | *0.000 | -0.328 | -0.005 | -0.000 | NaN |

---

### 🧭 Province: Phatthalung (TH.PL)

| P1 | (7.491511107, 100.051674890) | P2 | (7.500553256, 100.051674890) |
|:---|:---|:---|:---|
| MSL | 20 | HAE | 2 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -234.1 ppm | P2_UTM_CSF | -233.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.000 | *0.000 | -0.234 | -0.000 | -0.000 | NaN |

---

### 🧭 Province: Phrae (TH.PR)

| P1 | (18.268705369, 100.171446005) | P2 | (18.277740137, 100.171446005) |
|:---|:---|:---|:---|
| MSL | 164 | HAE | 128 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -230.6 ppm | P2_UTM_CSF | -230.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.020 | *0.000 | -0.231 | -0.020 | -0.000 | NaN |

---

### 🧭 Province: Phitsanulok East (TH.PS_E)

| P1 | (17.107554666, 100.837540724) | P2 | (17.116590499, 100.837540724) |
|:---|:---|:---|:---|
| MSL | 204 | HAE | 171 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +46.3 ppm | P2_UTM_CSF | +45.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.027 | *0.000 | +0.046 | -0.027 | -0.000 | NaN |

---

### 🧭 Province: Phitsanulok West (TH.PS_W)

| P1 | (16.848569870, 100.396154288) | P2 | (16.857605932, 100.396154288) |
|:---|:---|:---|:---|
| MSL | 52 | HAE | 18 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -129.7 ppm | P2_UTM_CSF | -128.8 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.003 | *0.000 | -0.129 | -0.003 | -0.000 | NaN |

---

### 🧭 Province: Pathum Thani (TH.PT)

| P1 | (14.093935682, 100.628758039) | P2 | (14.102973989, 100.628758039) |
|:---|:---|:---|:---|
| MSL | 3 | HAE | -28 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -13.3 ppm | P2_UTM_CSF | -13.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.013 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Phuket (TH.PU)

| P1 | (7.978985549, 98.335485439) | P2 | (7.988027492, 98.335485439) |
|:---|:---|:---|:---|
| MSL | 19 | HAE | -7 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -333.2 ppm | P2_UTM_CSF | -332.0 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.001 | *0.000 | -0.333 | +0.001 | -0.000 | NaN |

---

### 🧭 Province: Phayao (TH.PY)

| P1 | (19.268545868, 100.156080284) | P2 | (19.277579670, 100.156080284) |
|:---|:---|:---|:---|
| MSL | 473 | HAE | 437 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -286.5 ppm | P2_UTM_CSF | -286.0 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.069 | *0.000 | -0.286 | -0.069 | -0.000 | NaN |

---

### 🧭 Province: Roi Et (TH.RE)

| P1 | (15.937200922, 103.759346063) | P2 | (15.946237767, 103.759346063) |
|:---|:---|:---|:---|
| MSL | 139 | HAE | 112 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -199.6 ppm | P2_UTM_CSF | -199.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.018 | *0.000 | -0.200 | -0.018 | -0.000 | NaN |

---

### 🧭 Province: Ranong (TH.RN)

| P1 | (9.953233290, 98.624537606) | P2 | (9.962274269, 98.624537606) |
|:---|:---|:---|:---|
| MSL | 3 | HAE | -25 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -375.1 ppm | P2_UTM_CSF | -374.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.375 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Ratchaburi (TH.RT)

| P1 | (13.547914982, 99.616983170) | P2 | (13.556953690, 99.616983170) |
|:---|:---|:---|:---|
| MSL | 79 | HAE | 47 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -351.9 ppm | P2_UTM_CSF | -352.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.007 | *0.000 | -0.352 | -0.007 | -0.000 | NaN |

---

### 🧭 Province: Rayong (TH.RY)

| P1 | (12.872940065, 101.448631025) | P2 | (12.881979249, 101.448631025) |
|:---|:---|:---|:---|
| MSL | 101 | HAE | 75 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +460.1 ppm | P2_UTM_CSF | +463.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.012 | *0.000 | +0.462 | -0.012 | -0.000 | NaN |

---

### 🧭 Province: Satun (TH.SA)

| P1 | (6.767661096, 100.027373959) | P2 | (6.776703527, 100.027373959) |
|:---|:---|:---|:---|
| MSL | 17 | HAE | 1 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -240.4 ppm | P2_UTM_CSF | -240.8 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.000 | *0.000 | -0.241 | -0.000 | -0.000 | NaN |

---

### 🧭 Province: Sing Buri (TH.SB)

| P1 | (14.910660267, 100.309235214) | P2 | (14.919697946, 100.309235214) |
|:---|:---|:---|:---|
| MSL | 11 | HAE | -21 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -151.4 ppm | P2_UTM_CSF | -151.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.003 | *0.000 | -0.151 | +0.003 | -0.000 | NaN |

---

### 🧭 Province: Songkhla (TH.SG)

| P1 | (7.113058567, 100.366106732) | P2 | (7.122100868, 100.366106732) |
|:---|:---|:---|:---|
| MSL | 17 | HAE | 2 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -118.8 ppm | P2_UTM_CSF | -118.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.000 | *0.000 | -0.119 | -0.000 | -0.000 | NaN |

---

### 🧭 Province: Suphan Buri (TH.SH)

| P1 | (14.569625378, 100.013734080) | P2 | (14.578663323, 100.013734080) |
|:---|:---|:---|:---|
| MSL | 8 | HAE | -25 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -248.5 ppm | P2_UTM_CSF | -248.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.249 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Si Sa Ket (TH.SI)

| P1 | (14.954740525, 104.327978702) | P2 | (14.963778169, 104.327978702) |
|:---|:---|:---|:---|
| MSL | 130 | HAE | 107 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -352.3 ppm | P2_UTM_CSF | -352.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.017 | *0.000 | -0.352 | -0.017 | -0.000 | NaN |

---

### 🧭 Province: Sa Kaeo (TH.SK)

| P1 | (13.715636731, 102.277016591) | P2 | (13.724675317, 102.277016591) |
|:---|:---|:---|:---|
| MSL | 83 | HAE | 58 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +663.9 ppm | P2_UTM_CSF | +663.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.009 | *0.000 | +0.664 | -0.009 | -0.000 | NaN |

---

### 🧭 Province: Samut Songkhram (TH.SM)

| P1 | (13.379564762, 99.927180533) | P2 | (13.388603591, 99.927180533) |
|:---|:---|:---|:---|
| MSL | 5 | HAE | -26 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -271.2 ppm | P2_UTM_CSF | -271.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.004 | *0.000 | -0.271 | +0.004 | -0.000 | NaN |

---

### 🧭 Province: Sakon Nakhon (TH.SN)

| P1 | (17.429465294, 103.661092071) | P2 | (17.438500838, 103.661092071) |
|:---|:---|:---|:---|
| MSL | 165 | HAE | 137 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -171.2 ppm | P2_UTM_CSF | -171.8 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.021 | *0.000 | -0.171 | -0.021 | -0.000 | NaN |

---

### 🧭 Province: Sukhothai (TH.SO)

| P1 | (17.250304222, 99.710406054) | P2 | (17.259339928, 99.710406054) |
|:---|:---|:---|:---|
| MSL | 80 | HAE | 44 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -333.4 ppm | P2_UTM_CSF | -339.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.007 | *0.000 | -0.336 | -0.007 | -0.000 | NaN |

---

### 🧭 Province: Saraburi (TH.SR)

| P1 | (14.643711092, 100.901249118) | P2 | (14.652748979, 100.901249118) |
|:---|:---|:---|:---|
| MSL | 43 | HAE | 13 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +117.0 ppm | P2_UTM_CSF | +116.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.002 | *0.000 | +0.117 | -0.002 | -0.000 | NaN |

---

### 🧭 Province: Samut Sakhon (TH.SS)

| P1 | (13.579111100, 100.212851977) | P2 | (13.588149785, 100.212851977) |
|:---|:---|:---|:---|
| MSL | 2 | HAE | -29 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -182.4 ppm | P2_UTM_CSF | -182.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.005 | *0.000 | -0.182 | +0.005 | -0.000 | NaN |

---

### 🧭 Province: Surat Thani North (TH.ST_N)

| P1 | (9.421544825, 99.188978954) | P2 | (9.430586084, 99.188978954) |
|:---|:---|:---|:---|
| MSL | 10 | HAE | -15 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -392.3 ppm | P2_UTM_CSF | -392.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.002 | *0.000 | -0.392 | +0.002 | -0.000 | NaN |

---

### 🧭 Province: Surat Thani South (TH.ST_S)

| P1 | (9.115851252, 99.330908113) | P2 | (9.124892665, 99.330908113) |
|:---|:---|:---|:---|
| MSL | 3 | HAE | -20 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -380.5 ppm | P2_UTM_CSF | -380.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.003 | *0.000 | -0.380 | +0.003 | -0.000 | NaN |

---

### 🧭 Province: Surin (TH.SU)

| P1 | (14.905311584, 103.670337042) | P2 | (14.914349267, 103.670337042) |
|:---|:---|:---|:---|
| MSL | 149 | HAE | 125 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -166.5 ppm | P2_UTM_CSF | -166.9 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.020 | *0.000 | -0.167 | -0.020 | -0.000 | NaN |

---

### 🧭 Province: Trang (TH.TG)

| P1 | (7.541000000, 99.578476235) | P2 | (7.550042129, 99.578476235) |
|:---|:---|:---|:---|
| MSL | 4 | HAE | -15 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -347.2 ppm | P2_UTM_CSF | -347.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +0.002 | *0.000 | -0.347 | +0.002 | -0.000 | NaN |

---

### 🧭 Province: Tak Central (TH.TK_C)

| P1 | (16.720524767, 98.578137689) | P2 | (16.729560942, 98.578137689) |
|:---|:---|:---|:---|
| MSL | 218 | HAE | 180 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -402.5 ppm | P2_UTM_CSF | -404.0 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.028 | *0.000 | -0.403 | -0.028 | -0.000 | NaN |

---

### 🧭 Province: Tak North (TH.TK_N)

| P1 | (17.146814348, 99.084563927) | P2 | (17.155850146, 99.084563927) |
|:---|:---|:---|:---|
| MSL | 130 | HAE | 93 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -413.5 ppm | P2_UTM_CSF | -413.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.015 | *0.000 | -0.414 | -0.015 | -0.000 | NaN |

---

### 🧭 Province: Tak South (TH.TK_S)

| P1 | (16.019067192, 98.863633651) | P2 | (16.028103969, 98.863633651) |
|:---|:---|:---|:---|
| MSL | 482 | HAE | 446 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -464.5 ppm | P2_UTM_CSF | -470.5 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.070 | *0.000 | -0.467 | -0.070 | -0.000 | NaN |

---

### 🧭 Province: Trat (TH.TT)

| P1 | (12.202349092, 102.419377769) | P2 | (12.211388727, 102.419377769) |
|:---|:---|:---|:---|
| MSL | 30 | HAE | 8 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +573.8 ppm | P2_UTM_CSF | +574.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.001 | *0.000 | +0.574 | -0.001 | -0.000 | NaN |

---

### 🧭 Province: Uttaradit Central (TH.UD_C)

| P1 | (17.837711335, 100.589207480) | P2 | (17.846746505, 100.589207480) |
|:---|:---|:---|:---|
| MSL | 149 | HAE | 114 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -68.1 ppm | P2_UTM_CSF | -66.6 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.018 | *0.000 | -0.067 | -0.018 | -0.000 | NaN |

---

### 🧭 Province: Uttaradit East (TH.UD_E)

| P1 | (18.139229775, 101.088126375) | P2 | (18.148264665, 101.088126375) |
|:---|:---|:---|:---|
| MSL | 446 | HAE | 413 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +141.6 ppm | P2_UTM_CSF | +135.2 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.065 | *0.000 | +0.138 | -0.065 | -0.000 | NaN |

---

### 🧭 Province: Uttaradit West (TH.UD_W)

| P1 | (17.510281563, 100.224775705) | P2 | (17.519317034, 100.224775705) |
|:---|:---|:---|:---|
| MSL | 86 | HAE | 51 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -198.6 ppm | P2_UTM_CSF | -199.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.008 | *0.000 | -0.199 | -0.008 | -0.000 | NaN |

---

### 🧭 Province: Udon Thani (TH.UN)

| P1 | (17.441490168, 102.834075366) | P2 | (17.450525701, 102.834075366) |
|:---|:---|:---|:---|
| MSL | 171 | HAE | 141 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +232.1 ppm | P2_UTM_CSF | +232.1 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.022 | *0.000 | +0.232 | -0.022 | -0.000 | NaN |

---

### 🧭 Province: Ubon Ratchathani North (TH.UR_N)

| P1 | (15.611293801, 105.035368542) | P2 | (15.620330916, 105.035368542) |
|:---|:---|:---|:---|
| MSL | 135 | HAE | 113 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -417.9 ppm | P2_UTM_CSF | -417.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.018 | *0.000 | -0.418 | -0.018 | -0.000 | NaN |

---

### 🧭 Province: Ubon Ratchathani South (TH.UR_S)

| P1 | (14.948395253, 105.120822527) | P2 | (14.957432902, 105.120822527) |
|:---|:---|:---|:---|
| MSL | 137 | HAE | 118 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -414.6 ppm | P2_UTM_CSF | -418.3 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.019 | *0.000 | -0.416 | -0.019 | -0.000 | NaN |

---

### 🧭 Province: Uthai Thani (TH.UT)

| P1 | (15.366869450, 99.560988889) | P2 | (15.375906764, 99.560988889) |
|:---|:---|:---|:---|
| MSL | 118 | HAE | 83 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -368.0 ppm | P2_UTM_CSF | -368.4 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.013 | *0.000 | -0.368 | -0.013 | -0.000 | NaN |

---

### 🧭 Province: Yala (TH.YL)

| P1 | (6.478152420, 101.263328201) | P2 | (6.487194957, 101.263328201) |
|:---|:---|:---|:---|
| MSL | 25 | HAE | 15 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | +372.8 ppm | P2_UTM_CSF | +373.7 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.002 | *0.000 | +0.373 | -0.002 | -0.000 | NaN |

---

### 🧭 Province: Yasothon (TH.YS)

| P1 | (15.818015099, 104.275452490) | P2 | (15.827052043, 104.275452490) |
|:---|:---|:---|:---|
| MSL | 145 | HAE | 120 |
| P1_LDP | (NaN, NaN) | P2_LDP | (NaN, NaN) |
| P1_LDP_CSF | +nan ppm | P2_LDP_CSF | +nan ppm |
| P1_UTM_CSF | -344.8 ppm | P2_UTM_CSF | -344.1 ppm |

> **LDP Definition:**
> `Not found`

| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| -0.019 | *0.000 | -0.344 | -0.019 | -0.000 | NaN |

