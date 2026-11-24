"""Prototip: Ankara için bitki bazında aylık sulama ihtiyacı (FAO-56 yaklaşımı).

Akış:
  1. Open-Meteo arşivinden (ERA5) günlük ET0 (FAO Penman-Monteith) ve yağış çekilir.
     ET0 zaten sıcaklık, nem, rüzgar ve radyasyonu içerir.
  2. Aylık ortalama alınır (varsayılan 2020-2024).
  3. ETc = ET0 x Kc (sulama sezonu Mart-Kasım, Konca vd. 2026 ile aynı).
  4. Efektif yağış: USDA-SCS aylık formülü (CROPWAT seçeneği).
  5. Net ihtiyaç = max(0, ETc - Peff); brüt = net / sulama randımanı.

Kc ve randıman değerleri: Konca, Ahmad & Apaydın (2026), Water 18(11):1362, Ek Tablolar.
Not: Kc her ay için sabit (tablodaki en yüksek değer) alınmıştır; bu ihtiyacı biraz
fazla gösterir. Sonraki adımda aylık Kc eğrisi eklenecek.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

KOK = Path(__file__).parent
CIKTI = KOK / "cikti"
CIKTI.mkdir(exist_ok=True)

KONUM = {"ad": "Ankara (Kızılay)", "lat": 39.92, "lon": 32.85}
BASLANGIC, BITIS = "2020-01-01", "2024-12-31"
SEZON = range(3, 12)  # Mart-Kasım
TARIFE_TL_M3 = 85.78   # İSKİ 2025 yeşil alan sulama (KDV hariç)

# ad, Kc, sulama randımanı, renk (dataviz referans paleti, kategorik sıra)
BITKILER = [
    ("Çim karışımı (Lolium/Poa/Festuca)", 0.95, 0.70, "#2a78d6"),
    ("Biberiye (Rosmarinus officinalis)", 0.60, 0.90, "#eb6834"),
    ("Lavanta (Lavandula angustifolia)", 0.50, 0.90, "#1baf7a"),
    ("Civanperçemi (Achillea millefolium)", 0.40, 0.70, "#eda100"),
]
AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


def iklim_verisi():
    onbellek = CIKTI / "ankara_gunluk_2020_2024.json"
    if onbellek.exists():
        return json.loads(onbellek.read_text(encoding="utf-8"))
    r = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": KONUM["lat"], "longitude": KONUM["lon"],
            "start_date": BASLANGIC, "end_date": BITIS,
            "daily": "et0_fao_evapotranspiration,precipitation_sum,temperature_2m_mean,relative_humidity_2m_mean",
            "timezone": "Europe/Istanbul",
        },
        timeout=60,
    )
    r.raise_for_status()
    veri = r.json()["daily"]
    onbellek.write_text(json.dumps(veri), encoding="utf-8")
    return veri


def aylik_ortalama(veri):
    toplam = defaultdict(lambda: defaultdict(float))  # (yil, ay) -> degisken -> toplam/ortalama
    say = defaultdict(int)
    for i, t in enumerate(veri["time"]):
        anahtar = (int(t[:4]), int(t[5:7]))
        say[anahtar] += 1
        toplam[anahtar]["et0"] += veri["et0_fao_evapotranspiration"][i] or 0
        toplam[anahtar]["yagis"] += veri["precipitation_sum"][i] or 0
        toplam[anahtar]["sicaklik"] += veri["temperature_2m_mean"][i] or 0
        toplam[anahtar]["nem"] += veri["relative_humidity_2m_mean"][i] or 0
    yillar = sorted({y for y, _ in toplam})
    sonuc = {}
    for ay in range(1, 13):
        kayit = [(toplam[(y, ay)], say[(y, ay)]) for y in yillar if (y, ay) in toplam]
        n = len(kayit)
        sonuc[ay] = {
            "et0": sum(k["et0"] for k, _ in kayit) / n,
            "yagis": sum(k["yagis"] for k, _ in kayit) / n,
            "sicaklik": sum(k["sicaklik"] / c for k, c in kayit) / n,
            "nem": sum(k["nem"] / c for k, c in kayit) / n,
        }
    return sonuc, yillar


sys.path.insert(0, str(KOK.parent))
from src.hesap import efektif_yagis  # noqa: E402  (tek kaynak: src/hesap/fao56.py)


def hesapla(aylik):
    satirlar = []
    for ay in range(1, 13):
        a = aylik[ay]
        peff = efektif_yagis(a["yagis"])
        satir = {"ay": AYLAR[ay - 1], "et0_mm": a["et0"], "yagis_mm": a["yagis"],
                 "efektif_yagis_mm": peff, "sicaklik_C": a["sicaklik"], "nem_%": a["nem"]}
        for ad, kc, rand, _ in BITKILER:
            if ay in SEZON:
                net = max(0.0, a["et0"] * kc - peff)
                satir[ad] = net / rand
            else:
                satir[ad] = 0.0
        satirlar.append(satir)
    return satirlar


def ciz(satirlar, yillar):
    plt.rcParams.update({"font.family": "Segoe UI", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#3d3d3a",
                         "xtick.color": "#5f5e5a", "ytick.color": "#5f5e5a"})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9), height_ratios=[1, 1.4],
                                   facecolor="#ffffff")
    x = range(12)

    # Panel 1: iklim (ET0 ve yağış aynı birimde, mm/ay)
    w = 0.38
    ax1.bar([i - w / 2 - 0.01 for i in x], [s["et0_mm"] for s in satirlar], w,
            color="#2a78d6", label="Buharlaşma ihtiyacı ET₀")
    ax1.bar([i + w / 2 + 0.01 for i in x], [s["efektif_yagis_mm"] for s in satirlar], w,
            color="#1baf7a", label="Efektif yağış")
    ax1.set_xticks(list(x), AYLAR)
    ax1.set_ylabel("mm / ay")
    ax1.set_title(f"İklim: {KONUM['ad']}, {yillar[0]}–{yillar[-1]} ortalaması (Open-Meteo / ERA5)",
                  loc="left", fontsize=11, color="#1f1f1d")
    ax1.grid(axis="y", color="#e8e7e1", linewidth=0.8)
    ax1.set_axisbelow(True)
    ax1.legend(frameon=False, loc="upper left")

    # Panel 2: bitki bazında brüt sulama ihtiyacı
    for ad, kc, rand, renk in BITKILER:
        y = [s[ad] for s in satirlar]
        ax2.plot(list(x), y, color=renk, linewidth=2, marker="o", markersize=5,
                 label=f"{ad} — {sum(y):,.0f}".replace(",", ".")
                       + f" L/m²·yıl  (Kc {kc}, randıman %{int(rand*100)})")
    ax2.set_xticks(list(x), AYLAR)
    ax2.set_ylabel("Brüt sulama ihtiyacı (L/m² = mm / ay)")
    ax2.set_title("Bitkiye göre aylık sulama ihtiyacı (Mart–Kasım sezonu)",
                  loc="left", fontsize=11, color="#1f1f1d")
    ax2.grid(axis="y", color="#e8e7e1", linewidth=0.8)
    ax2.set_axisbelow(True)
    ax2.legend(frameon=False, loc="upper left", fontsize=9)

    fig.text(0.01, 0.005, "Kaynak: Kc ve randıman değerleri Konca vd. (2026) Water 18:1362; "
             "efektif yağış USDA-SCS; prototip hesap, saha ölçümü değildir.",
             fontsize=8, color="#5f5e5a")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    yol = CIKTI / "ankara_sulama_ihtiyaci.png"
    fig.savefig(yol, dpi=150)
    return yol


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    veri = iklim_verisi()
    aylik, yillar = aylik_ortalama(veri)
    satirlar = hesapla(aylik)

    with open(CIKTI / "ankara_aylik_tablo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        for s in satirlar:
            w.writerow({k: (round(v, 1) if isinstance(v, float) else v) for k, v in s.items()})

    cim = sum(s[BITKILER[0][0]] for s in satirlar)
    print(f"Yıllık ET0: {sum(s['et0_mm'] for s in satirlar):.0f} mm | "
          f"yağış: {sum(s['yagis_mm'] for s in satirlar):.0f} mm")
    print(f"{'Bitki':42s} {'L/m²·yıl':>9s} {'çime göre':>10s} {'TL/1000m²·yıl':>14s}")
    for ad, *_ in BITKILER:
        yillik = sum(s[ad] for s in satirlar)
        print(f"{ad:42s} {yillik:9.0f} {100*(1-yillik/cim):9.0f}% {yillik*TARIFE_TL_M3:14,.0f}")
    print("Grafik:", ciz(satirlar, yillar))


if __name__ == "__main__":
    sys.exit(main())
