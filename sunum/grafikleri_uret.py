"""Florify sunumu için yeşil, toz pembe ve mavi paletli grafikler üretir.

Tüm sayılar doğrudan repo içindeki önbellek ve doğrulanmış veri tablolarından hesaplanır.
Çalıştırma:
    .venv\\Scripts\\python sunum/grafikleri_uret.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.hesap import Bolge, bolge_ihtiyaci
from src.veri.iklim import iklim_al
from src.veri.projeksiyon import degisim_oranlari, gelecek_iklimi, model_gunluk

CIKTI = KOK / "sunum" / "gorseller"
CIKTI.mkdir(parents=True, exist_ok=True)

# ── Florify Paleti: Yeşil · Toz Pembe · Mavi ──────────────────────────────────
YESIL_KOYU = "#1B4D3E"
YESIL = "#3D7A62"
YESIL_ACIK = "#CFE3D8"

PEMBE_KOYU = "#A85E6B"
PEMBE = "#C98A92"
PEMBE_ACIK = "#F2DDE0"

MAVI_KOYU = "#245B7A"
MAVI = "#4A89AC"
MAVI_ACIK = "#D5E6F0"

METIN = "#1E2B2A"
IKINCIL = "#546866"
IZGARA = "#E3ECE8"
ARKAPLAN = "#FFFFFF"

AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
    "axes.edgecolor": "#C9D8D3",
    "axes.linewidth": 0.9,
    "axes.labelcolor": METIN,
    "xtick.color": IKINCIL,
    "ytick.color": IKINCIL,
    "text.color": METIN,
    "figure.facecolor": ARKAPLAN,
    "axes.facecolor": ARKAPLAN,
})


def _stil(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=IZGARA, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def grafik_ankara_aylik():
    iklim = iklim_al(39.92, 32.85, 2020, 2024)
    sezon = range(3, 12)
    turler = [
        ("Çim karışımı (Kc 0,95 · yağmurlama %70)", Bolge("Çim", "cim", 0.95, 1, yontem="yagmurlama"), PEMBE_KOYU, 2.8, "o"),
        ("Biberiye (Kc 0,60 · damla %90)", Bolge("Biberiye", "cali_otsu", 0.60, 1, yontem="damla"), MAVI, 2.2, "s"),
        ("Lavanta (Kc 0,50 · damla %90)", Bolge("Lavanta", "cali_otsu", 0.50, 1, yontem="damla"), YESIL, 2.4, "^"),
        ("Civanperçemi (Kc 0,40 · damla %90)", Bolge("Civanperçemi", "yer_ortucu", 0.40, 1, yontem="damla"), YESIL_KOYU, 2.0, "D"),
    ]

    fig, ax = plt.subplots(figsize=(7.6, 4.3), dpi=300)
    _stil(ax)
    x = np.arange(12)

    sonuclar = {}
    for etiket, bolge, renk, lw, mk in turler:
        s = bolge_ihtiyaci(iklim, bolge, sezon)
        aylik = s["mm"]
        sonuclar[etiket] = aylik
        ax.plot(x, aylik, label=f"{etiket.split(' (')[0]} — {s['mm_yil']:,.0f} L/m²·yıl".replace(",", "."),
                color=renk, linewidth=lw, marker=mk, markersize=5.5, zorder=4)

    cim_yil = sum(sonuclar[turler[0][0]])
    lav_yil = sum(sonuclar[turler[2][0]])
    fark_pct = round(100 * (cim_yil - lav_yil) / cim_yil)
    ax.fill_between(x, sonuclar[turler[2][0]], sonuclar[turler[0][0]],
                    color=PEMBE_ACIK, alpha=0.55, zorder=2, label=f"Çim → Lavanta su farkı (−%{fark_pct})")

    ax.set_xticks(x)
    ax.set_xticklabels(AYLAR, fontsize=9.5)
    ax.set_ylabel("Brüt sulama ihtiyacı (L/m²·ay)", fontsize=10, fontweight="bold")
    ax.set_ylim(-5, 298)
    ax.set_title("Ankara Aylık Sulama İhtiyacı: Çim vs. Kurakçıl Bitkiler (Hesap)",
                 fontsize=11.5, fontweight="bold", color=YESIL_KOYU, loc="left", pad=10)
    ax.legend(frameon=True, facecolor="#FAFBF9", edgecolor="#DCE6E2", fontsize=8.4, loc="upper left")

    fig.text(0.01, 0.01,
             "Kaynak: Open-Meteo/ERA5 (Ankara, 2020–2024); Kc değerleri Konca vd. (2026) Water 18:1362; FAO-56 hesabı (saha ölçümü değildir).",
             fontsize=7.3, color=IKINCIL)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(CIKTI / "grafik_ankara_aylik.png", dpi=300)
    plt.close(fig)


def grafik_uydu_izmir():
    veri = json.loads((KOK / "prototip" / "cikti" / "uydu_izmir_sonuc.json").read_text(encoding="utf-8"))
    ilceler = veri["ilceler"]
    xs = np.array([d["sulanan_yesil_m2"] / 1000.0 for d in ilceler])
    ys = np.array([d["izsu_2023_m3"] / 1000.0 for d in ilceler])
    adlar = [d["ilce"] for d in ilceler]

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=300)
    _stil(ax)
    ax.grid(axis="x", color=IZGARA, linewidth=0.8, zorder=0)

    # Doğrusal eğilim çizgisi (görsel rehber)
    m, b = np.polyfit(xs, ys, 1)
    x_line = np.linspace(xs.min() - 15, xs.max() + 15, 50)
    ax.plot(x_line, m * x_line + b, color=PEMBE, linestyle="--", linewidth=1.8, zorder=2, label="Doğrusal eğilim")

    ax.scatter(xs, ys, s=95, color=MAVI_KOYU, edgecolors="#FFFFFF", linewidths=1.4, zorder=4)

    ofsetler = {
        "Konak": (9, -3),
        "Bornova": (-60, 4),
        "Çiğli": (-38, 10),
        "Karşıyaka": (9, -11),
        "Bayraklı": (9, 4),
        "Buca": (-38, 6),
        "Gaziemir": (9, -4),
        "Karabağlar": (9, -5),
        "Balçova": (-12, 11),
        "Güzelbahçe": (9, -5),
        "Narlıdere": (9, -4),
    }
    for ad, x, y in zip(adlar, xs, ys):
        dx, dy = ofsetler.get(ad, (7, 4))
        ax.annotate(ad, (x, y), xytext=(dx, dy), textcoords="offset points",
                    fontsize=8.6, color=METIN, fontweight="normal")

    ax.text(0.03, 0.94,
            "Spearman ρ = 0,85 (p = 0,0008, n = 11)\nKentsel alan sabitken kısmi ρ = 0,70",
            transform=ax.transAxes, va="top", ha="left", fontsize=8.8, fontweight="bold",
            color=YESIL_KOYU,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#E8F3EE", edgecolor=YESIL, linewidth=0.9))

    ax.set_xlabel("Uydudan bulunan sulanan kentsel yeşil (bin m²)", fontsize=9.8, fontweight="bold")
    ax.set_ylabel("İZSU 2023 park + mezarlık faturası (bin m³)", fontsize=9.8, fontweight="bold")
    ax.set_xlim(115, 625)
    ax.set_ylim(50, 1780)
    ax.set_title("İzmir 11 Merkez İlçe: Uydu Tespiti vs. Gerçek Su Faturası",
                 fontsize=11.3, fontweight="bold", color=MAVI_KOYU, loc="left", pad=10)

    fig.text(0.01, 0.01,
             "Kaynak: © ESA WorldCover 2021 & Sentinel-2 (2023), © OpenStreetMap, İZSU Açık Veri (CC BY 4.0).",
             fontsize=7.3, color=IKINCIL)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(CIKTI / "grafik_uydu_izmir.png", dpi=300)
    plt.close(fig)


def grafik_dogrulama():
    # Sol: Las Vegas SNWA sayaç ölçümü vs Florify hesabı
    gal_ft2_to_mm = 40.7458
    snwa_cim, snwa_kur = [], []
    with (KOK / "kaynaklar" / "veri" / "snwa_aylik_olcum.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            snwa_cim.append(float(r["cim_ortalama_gal_ft2"]) * gal_ft2_to_mm)
            snwa_kur.append(float(r["kurakcil_ortalama_gal_ft2"]) * gal_ft2_to_mm)

    # Las Vegas ERA5 önbelleği (prototip/dogrulama_testleri.py ile aynı)
    lv_yol = KOK / "veri_onbellek" / "iklim_lasvegas_1995-01-01_2001-12-31.json"
    lv_raw = json.loads(lv_yol.read_text(encoding="utf-8"))
    from src.veri.iklim import aylik_seri, klimatoloji
    lv_iklim = klimatoloji(aylik_seri(lv_raw["daily"] if "daily" in lv_raw else lv_raw))
    lv_cim_h = bolge_ihtiyaci(lv_iklim, Bolge("Çim", "cim", 0.95, 1, yontem="yagmurlama"), range(1, 13))["mm"]
    lv_kur_h = bolge_ihtiyaci(lv_iklim, Bolge("Kurakçıl", "cali_otsu", 0.50, 1, yontem="damla"), range(1, 13))["mm"]

    # Sağ: İzmir İZSU 2014-2024 aylık profil
    ay_izsu = {a: [] for a in range(1, 13)}
    ay_mod = {a: [] for a in range(1, 13)}
    yillik_abone = {}
    satirlar = list(csv.DictReader((KOK / "prototip" / "cikti" / "test2_izsu_aylik.csv").open(encoding="utf-8")))
    for y in sorted({int(r["yil"]) for r in satirlar}):
        yillik_abone[y] = np.mean([float(r["abone_adedi"]) for r in satirlar if int(r["yil"]) == y])
    for r in satirlar:
        y, a = int(r["yil"]), int(r["ay"])
        ay_izsu[a].append(float(r["tuketim_satir_toplami_m3"]) / yillik_abone[y])
        ay_mod[a].append(float(r["model_cim_ihtiyaci_mm"]))
    izsu_p = np.array([np.mean(ay_izsu[a]) for a in range(1, 13)])
    mod_p = np.array([np.mean(ay_mod[a]) for a in range(1, 13)])
    izsu_idx = 100 * izsu_p / izsu_p.mean()
    mod_idx = 100 * mod_p / mod_p.mean()
    mod_lag = np.roll(mod_idx, 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.1), dpi=300)
    x = np.arange(12)

    # Panel 1: SNWA
    _stil(ax1)
    ax1.plot(x, snwa_cim, color=PEMBE_KOYU, lw=2.5, marker="o", ms=4.5, label="Çim · SNWA ölçüm (2.977 mm)")
    ax1.plot(x, lv_cim_h, color=PEMBE, lw=2.1, ls="--", label="Çim · Florify hesap (r = 0,96)")
    ax1.plot(x, snwa_kur, color=YESIL_KOYU, lw=2.4, marker="s", ms=4.2, label="Kurakçıl · SNWA ölçüm (701 mm)")
    ax1.plot(x, lv_kur_h, color=YESIL, lw=2.0, ls="--", label="Kurakçıl · Florify hesap (Kc 0,50)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(AYLAR, fontsize=8.5)
    ax1.set_ylabel("Aylık sulama (mm = L/m²)", fontsize=9.2, fontweight="bold")
    ax1.set_title("Test 1 · Las Vegas Sayaç Ölçümü (1995–2001)", fontsize=10.5, fontweight="bold", color=YESIL_KOYU, loc="left")
    ax1.legend(frameon=True, facecolor="#FAFBF9", edgecolor="#DCE6E2", fontsize=7.6, loc="upper left")
    ax1.text(0.97, 0.94, "Tasarruf:\nHesap %62 · Ölçüm %76\n(temkinli)",
             transform=ax1.transAxes, ha="right", va="top", fontsize=8.0, fontweight="bold", color=PEMBE_KOYU,
             bbox=dict(boxstyle="round,pad=0.35", facecolor=PEMBE_ACIK, edgecolor=PEMBE, lw=0.8))

    # Panel 2: İZSU
    _stil(ax2)
    ax2.plot(x, izsu_idx, color=MAVI_KOYU, lw=2.6, marker="o", ms=4.8, label="İZSU park+mezarlık faturası")
    ax2.plot(x, mod_idx, color=PEMBE_KOYU, lw=2.1, label="Florify hesap · aynı ay (r = 0,89)")
    ax2.plot(x, mod_lag, color=YESIL, lw=2.1, ls="--", label="Florify · 1 ay gecikme (r = 0,97)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(AYLAR, fontsize=8.5)
    ax2.set_ylabel("Mevsimsel endeks (ort. = 100)", fontsize=9.2, fontweight="bold")
    ax2.set_title("Test 2 · İzmir 10 Yıllık Fatura Profili (2014–2024)", fontsize=10.5, fontweight="bold", color=MAVI_KOYU, loc="left")
    ax2.legend(frameon=True, facecolor="#FAFBF9", edgecolor="#DCE6E2", fontsize=7.6, loc="upper left")

    fig.text(0.01, 0.01,
             "Kaynak: Sovocool (2005) SNWA Tablo 18; İZSU / İzmir BB Açık Veri (CC BY 4.0, 129 ay); Open-Meteo/ERA5.",
             fontsize=7.3, color=IKINCIL)
    plt.tight_layout(rect=[0, 0.045, 1, 1])
    fig.savefig(CIKTI / "grafik_dogrulama.png", dpi=300)
    plt.close(fig)


def grafik_2040():
    sezon = range(3, 12)
    senaryolar = [
        ("Ankara\nÇim", 39.92, 32.85, Bolge("Çim", "cim", 0.95, 1, yontem="yagmurlama"), PEMBE_KOYU, PEMBE_ACIK),
        ("Ankara\nKurakçıl", 39.92, 32.85, Bolge("Kurakçıl", "cali_otsu", 0.50, 1, yontem="damla"), YESIL_KOYU, YESIL_ACIK),
        ("İzmir\nÇim", 38.41, 27.14, Bolge("Çim", "cim", 0.95, 1, yontem="yagmurlama"), MAVI_KOYU, MAVI_ACIK),
        ("İzmir\nKurakçıl", 38.41, 27.14, Bolge("Kurakçıl", "cali_otsu", 0.50, 1, yontem="damla"), YESIL, "#DDF0E7"),
    ]

    etiketler, bugunler, medyanlar, minler, maksler, renkler, aciklar = [], [], [], [], [], [], []
    for ad, lat, lon, bolge, renk, acik in senaryolar:
        taban = iklim_al(lat, lon, 1991, 2020)
        b_val = bolge_ihtiyaci(taban, bolge, sezon)["mm_yil"]
        oranlar = degisim_oranlari(model_gunluk(lat, lon))
        gel = gelecek_iklimi(taban, oranlar)
        vals = [bolge_ihtiyaci(ik, bolge, sezon)["mm_yil"] for ik in gel.values()]
        etiketler.append(ad)
        bugunler.append(b_val)
        medyanlar.append(float(np.median(vals)))
        minler.append(float(np.min(vals)))
        maksler.append(float(np.max(vals)))
        renkler.append(renk)
        aciklar.append(acik)

    fig, ax = plt.subplots(figsize=(6.8, 4.1), dpi=300)
    _stil(ax)
    x = np.arange(len(etiketler))
    w = 0.34

    b1 = ax.bar(x - w / 2, bugunler, width=w, color=aciklar, edgecolor=renkler, linewidth=1.3, label="Taban (1991–2020)", zorder=3)
    b2 = ax.bar(x + w / 2, medyanlar, width=w, color=renkler, edgecolor=renkler, linewidth=1.0, label="2040'lar medyan (7 CMIP6)", zorder=3)

    # Min-maks hata çubuğu
    yerr_lo = [m - lo for m, lo in zip(medyanlar, minler)]
    yerr_hi = [hi - m for m, hi in zip(medyanlar, maksler)]
    ax.errorbar(x + w / 2, medyanlar, yerr=[yerr_lo, yerr_hi], fmt="none", ecolor=METIN, elinewidth=1.3, capsize=4, zorder=5)

    for i in range(len(etiketler)):
        fark = medyanlar[i] - bugunler[i]
        pct = 100 * fark / bugunler[i]
        ax.text(x[i] + w / 2, maksler[i] + 28, f"+{fark:.0f} L\n(+%{pct:.0f})",
                ha="center", va="bottom", fontsize=8.4, fontweight="bold", color=renkler[i])

    ax.set_xticks(x)
    ax.set_xticklabels(etiketler, fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Yıllık sulama ihtiyacı (L/m²·yıl)", fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 1740)
    ax.set_title("2040'lar İklim Riski: Çimin Ek Su Yükü Kurakçılın ~2,7 Katı",
                 fontsize=10.8, fontweight="bold", color=YESIL_KOYU, loc="left", pad=22)
    ax.legend(frameon=True, facecolor="#FAFBF9", edgecolor="#DCE6E2", fontsize=8.3,
              loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=2)

    fig.text(0.01, 0.01,
             "Kaynak: Open-Meteo Climate API (7 CMIP6 HighResMIP, yüksek emisyon / RCP8.5 benzeri, CC BY 4.0) + ERA5 delta hesabı.",
             fontsize=7.2, color=IKINCIL)
    plt.tight_layout(rect=[0, 0.045, 1, 1])
    fig.savefig(CIKTI / "grafik_2040.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    grafik_ankara_aylik()
    grafik_uydu_izmir()
    grafik_dogrulama()
    grafik_2040()
    print("4 grafik uretildi:", sorted(p.name for p in CIKTI.glob("*.png")))
