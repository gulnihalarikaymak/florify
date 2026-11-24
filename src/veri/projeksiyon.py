"""2040'lar iklimi: Open-Meteo Climate API (CMIP6 HighResMIP, 7 model) + delta yöntemi.

Kaynak: https://open-meteo.com/en/docs/climate-api
  - Senaryo: "CMIP6 içinde RCP8.5'e mümkün olduğunca yakın" (yüksek emisyon, kötümser uç)
  - Varsayılan olarak ERA5-Land'e göre doğrusal bias düzeltmeli, ~10 km'ye indirgenmiş
  - Veri 2050 sonunda bitiyor. Lisans CC BY 4.0 (CMIP6 ve Open-Meteo'ya atıf)

Delta yöntemi: Her model için aylık değişim oranı = model(gelecek) / model(taban). Bu oran gözlenen
(ERA5) aylık klimatolojiye uygulanır. Böylece modelin kendi mutlak hatası büyük ölçüde silinir.
Kurak aylarda yağış oranı patlamasın diye yağış oranı [0,5; 1,5] aralığında sınırlanır.
"""
import json
import time
from collections import defaultdict

import numpy as np
import requests

from .iklim import ONBELLEK

URL = "https://climate-api.open-meteo.com/v1/climate"
MODELLER = ["CMCC_CM2_VHR4", "FGOALS_f3_H", "HiRAM_SIT_HR", "MRI_AGCM3_2_S", "EC_Earth3P_HR",
            "MPI_ESM1_2_XR", "NICAM16_8S"]
TABAN = (1991, 2020)
GELECEK = (2041, 2050)  # API 2050'de bitiyor; "2040'lar"
YAGIS_ORAN_SINIR = (0.5, 1.5)


def model_gunluk(lat, lon, onbellek=ONBELLEK):
    onbellek.mkdir(exist_ok=True)
    yol = onbellek / f"cmip6_{lat:.2f}_{lon:.2f}_{TABAN[0]}_{GELECEK[1]}.json"
    if yol.exists():
        return json.loads(yol.read_text(encoding="utf-8"))
    for deneme in range(6):
        r = requests.get(URL, params={
            "latitude": lat, "longitude": lon, "start_date": f"{TABAN[0]}-01-01",
            "end_date": f"{GELECEK[1]}-12-31", "models": ",".join(MODELLER),
            "daily": "et0_fao_evapotranspiration_sum,precipitation_sum"}, timeout=300)
        if r.status_code != 429:
            break
        time.sleep(65 * (deneme + 1))
    r.raise_for_status()
    veri = r.json()["daily"]
    yol.write_text(json.dumps(veri), encoding="utf-8")
    return veri


def _aylik_ort(zaman, deger, yillar):
    """Yıl aralığında her ayın GÜNLÜK ortalaması (12 eleman). Günlük ortalama kullanılır ki
    artık yıl sayısı farkı (Şubat 28/29 gün) oranları bozmasın."""
    top, say = defaultdict(float), defaultdict(int)
    for t, v in zip(zaman, deger):
        y = int(t[:4])
        if yillar[0] <= y <= yillar[1] and v is not None:
            top[int(t[5:7])] += v
            say[int(t[5:7])] += 1
    return np.array([top[a] / say[a] if say[a] else 0.0 for a in range(1, 13)])


def degisim_oranlari(gunluk):
    """{model: {"et0": 12 oran, "yagis": 12 oran, "et0_yil_%": float, "yagis_yil_%": float}}"""
    sonuc = {}
    for m in MODELLER:
        e_k, p_k = f"et0_fao_evapotranspiration_sum_{m}", f"precipitation_sum_{m}"
        if e_k not in gunluk:
            continue
        eb, ef = (_aylik_ort(gunluk["time"], gunluk[e_k], d) for d in (TABAN, GELECEK))
        pb, pf = (_aylik_ort(gunluk["time"], gunluk[p_k], d) for d in (TABAN, GELECEK))
        if eb.sum() <= 0:
            continue
        sonuc[m] = {
            "et0": np.where(eb > 0, ef / np.maximum(eb, 1e-9), 1.0),
            "yagis": np.clip(np.where(pb > 0, pf / np.maximum(pb, 1e-9), 1.0), *YAGIS_ORAN_SINIR),
            "et0_yil_%": 100 * (ef.sum() / eb.sum() - 1),
            "yagis_yil_%": 100 * (pf.sum() / pb.sum() - 1),
        }
    return sonuc


def gelecek_iklimi(gozlem12, oranlar):
    """Gözlenen 12 aylık klimatolojiye (ERA5) her modelin oranlarını uygula → {model: iklim12}"""
    return {m: [{**d, "et0": d["et0"] * o["et0"][i], "yagis": d["yagis"] * o["yagis"][i]}
                for i, d in enumerate(gozlem12)] for m, o in oranlar.items()}
