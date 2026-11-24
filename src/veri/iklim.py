"""Open-Meteo arşiv istemcisi (ERA5) ve aylık özetler.

Cevaplar veri_onbellek/ klasörüne yazılır (git dışı); aynı sorgu ikinci kez ağa gitmez.
"""
import json
import statistics as st
import time
from collections import defaultdict
from pathlib import Path

import requests

ONBELLEK = Path(__file__).resolve().parents[2] / "veri_onbellek"
ARSIV_URL = "https://archive-api.open-meteo.com/v1/archive"
GUNLUK = ("et0_fao_evapotranspiration", "precipitation_sum", "temperature_2m_mean",
          "relative_humidity_2m_mean")


def iklim_gunluk(lat, lon, baslangic, bitis, onbellek=ONBELLEK):
    """Günlük ET0 (FAO P-M, mm), yağış (mm), sıcaklık (°C), nem (%)."""
    onbellek.mkdir(exist_ok=True)
    yol = onbellek / f"era5_{lat:.2f}_{lon:.2f}_{baslangic}_{bitis}.json"
    if yol.exists():
        return json.loads(yol.read_text(encoding="utf-8"))
    for deneme in range(6):
        r = requests.get(ARSIV_URL, params={
            "latitude": lat, "longitude": lon, "start_date": baslangic, "end_date": bitis,
            "daily": ",".join(GUNLUK), "timezone": "auto"}, timeout=180)
        if r.status_code != 429:  # ücretsiz kullanım sınırı: dakikalık/saatlik; bekleyip yeniden dene
            break
        time.sleep(65 * (deneme + 1))
    r.raise_for_status()
    veri = r.json()["daily"]
    yol.write_text(json.dumps(veri), encoding="utf-8")
    return veri


def aylik_seri(gunluk):
    """{(yıl, ay): {"et0": mm, "yagis": mm, "sicaklik": °C, "nem": %}}"""
    top = defaultdict(lambda: defaultdict(float))
    say = defaultdict(int)
    for i, t in enumerate(gunluk["time"]):
        k = (int(t[:4]), int(t[5:7]))
        say[k] += 1
        top[k]["et0"] += gunluk["et0_fao_evapotranspiration"][i] or 0
        top[k]["yagis"] += gunluk["precipitation_sum"][i] or 0
        if "temperature_2m_mean" in gunluk:
            top[k]["sicaklik"] += gunluk["temperature_2m_mean"][i] or 0
            top[k]["nem"] += gunluk["relative_humidity_2m_mean"][i] or 0
    sonuc = {}
    for k, d in top.items():
        sonuc[k] = {"et0": d["et0"], "yagis": d["yagis"],
                    "sicaklik": d["sicaklik"] / say[k], "nem": d["nem"] / say[k]}
    return sonuc


def klimatoloji(aylik):
    """12 elemanlı liste (Ocak=0): her ayın yıllar ortalaması. Yarım ay/yıl dahil edilmez."""
    gruplar = defaultdict(list)
    for (_, ay), d in aylik.items():
        gruplar[ay].append(d)
    return [{a: st.mean(d[a] for d in gruplar[ay]) for a in ("et0", "yagis", "sicaklik", "nem")}
            for ay in range(1, 13)]


def iklim_al(lat, lon, yil_bas, yil_bit):
    """Kısayol: bir nokta için yıl aralığının aylık klimatolojisi."""
    return klimatoloji(aylik_seri(iklim_gunluk(lat, lon, f"{yil_bas}-01-01", f"{yil_bit}-12-31")))
