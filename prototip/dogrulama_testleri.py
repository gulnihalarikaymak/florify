"""Hesap çekirdeğini iki gerçek ölçüme karşı test eder.

Test 1 – SNWA (Las Vegas, 1995–2001): sayaçla ölçülmüş çim ve kurakçıl alan sulaması
         (Sovocool 2005, Tablo 17–18) ile FAO-56 hesabımız.
Test 2 – İZSU (İzmir, 2014–2024/09): park ve mezarlık abonelerinin faturalanmış aylık
         tüketimi ile aynı ayların hesaplanan çim sulama ihtiyacı.

Çalıştırma:  .venv\\Scripts\\python prototip\\dogrulama_testleri.py
İZSU ham dosyası (76 MB) ilk çalıştırmada veri_onbellek/ klasörüne indirilir (git dışı).
"""
import csv
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sulama_hesabi import efektif_yagis

KOK = Path(__file__).resolve().parent
PROJE = KOK.parent
CIKTI = KOK / "cikti"
ONBELLEK = PROJE / "veri_onbellek"
CIKTI.mkdir(exist_ok=True)
ONBELLEK.mkdir(exist_ok=True)

GAL_FT2_MM = 3.785411784 / 0.09290304  # 1 gal/ft² = 40,75 mm
IZSU_URL = "https://openfiles.izmir.bel.tr/309436/docs/izsu-yillik-ilce-mahalle-su-tuketimi.csv"
AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

# Renkler: dataviz referans paleti (kategorik sıra), metin tonları
MAVI, TURUNCU, YESIL, SARI = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#3d3d3a",
                     "xtick.color": "#5f5e5a", "ytick.color": "#5f5e5a"})


def iklim_aylik(ad, lat, lon, bas, bit):
    """Open-Meteo arşivinden (ERA5) aylık ET0 ve yağış toplamı: {(yıl, ay): (et0, yağış)}."""
    yol = ONBELLEK / f"iklim_{ad}_{bas}_{bit}.json"
    if yol.exists():
        g = json.loads(yol.read_text(encoding="utf-8"))
    else:
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": lat, "longitude": lon, "start_date": bas, "end_date": bit,
            "daily": "et0_fao_evapotranspiration,precipitation_sum", "timezone": "auto"},
            timeout=120)
        r.raise_for_status()
        g = r.json()["daily"]
        yol.write_text(json.dumps(g), encoding="utf-8")
    ay = defaultdict(lambda: [0.0, 0.0])
    for t, e, p in zip(g["time"], g["et0_fao_evapotranspiration"], g["precipitation_sum"]):
        k = (int(t[:4]), int(t[5:7]))
        ay[k][0] += e or 0
        ay[k][1] += p or 0
    return dict(ay)


def ihtiyac(et0, yagis, kc, randiman):
    """Brüt sulama ihtiyacı, mm/ay (= L/m²)."""
    return max(0.0, et0 * kc - efektif_yagis(yagis)) / randiman


def pearson(x, y):
    mx, my = st.mean(x), st.mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5


def klimatoloji(aylik):
    """12 aylık ortalama ET0 ve yağış."""
    s = defaultdict(list)
    for (y, a), v in aylik.items():
        s[a].append(v)
    return {a: (st.mean(v[0] for v in s[a]), st.mean(v[1] for v in s[a])) for a in range(1, 13)}


# ───────────────────────────── Test 1: SNWA ─────────────────────────────
def test_snwa():
    olcum = list(csv.DictReader(open(PROJE / "kaynaklar/veri/snwa_aylik_olcum.csv", encoding="utf-8")))
    cim_olc = [float(r["cim_ortalama_gal_ft2"]) * GAL_FT2_MM for r in olcum]
    xer_olc = [float(r["kurakcil_ortalama_gal_ft2"]) * GAL_FT2_MM for r in olcum]
    cim_yil_olc, xer_yil_olc = 117.2 * 25.4, 27.6 * 25.4  # Tablo 17 (yıllık seri)

    iklim = klimatoloji(iklim_aylik("lasvegas", 36.17, -115.14, "1995-01-01", "2001-12-31"))
    et0 = [iklim[a][0] for a in range(1, 13)]
    yag = [iklim[a][1] for a in range(1, 13)]

    # Senaryolar: çim (yağmurlama), kurakçıl (damla). Las Vegas'ta sulama 12 ay sürer.
    senaryo = {
        "Çim, Kc 0,95 (bizim varsayım)": [ihtiyac(e, p, 0.95, 0.70) for e, p in zip(et0, yag)],
        "Çim, Kc 0,80 (WUCOLS serin iklim çimi)": [ihtiyac(e, p, 0.80, 0.70) for e, p in zip(et0, yag)],
        "Kurakçıl, Kc 0,50 (lavanta)": [ihtiyac(e, p, 0.50, 0.90) for e, p in zip(et0, yag)],
        "Kurakçıl, Kc 0,30 (WUCOLS düşük, seyrek dikim)": [ihtiyac(e, p, 0.30, 0.90) for e, p in zip(et0, yag)],
    }
    sonuc = {
        "et0_yillik_mm": sum(et0), "yagis_yillik_mm": sum(yag),
        "cim_olcum_yillik_mm": cim_yil_olc, "kurakcil_olcum_yillik_mm": xer_yil_olc,
        "olculen_tasarruf_%": 100 * (1 - xer_yil_olc / cim_yil_olc),
        "cim_olcum_ay_toplami_mm": sum(cim_olc), "kurakcil_olcum_ay_toplami_mm": sum(xer_olc),
        "r_cim_mevsimsellik": pearson(senaryo["Çim, Kc 0,95 (bizim varsayım)"], cim_olc),
        "r_kurakcil_mevsimsellik": pearson(senaryo["Kurakçıl, Kc 0,50 (lavanta)"], xer_olc),
        "senaryolar_yillik_mm": {k: sum(v) for k, v in senaryo.items()},
    }
    c95, _, x50, x30 = (sum(v) for v in senaryo.values())
    sonuc["model_tasarruf_%_cim095_lavanta"] = 100 * (1 - x50 / c95)
    sonuc["model_tasarruf_%_cim095_kc030"] = 100 * (1 - x30 / c95)

    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor="#ffffff")
    x = list(range(12))
    ax.plot(x, cim_olc, color=MAVI, lw=2, marker="o", ms=6, label="Çim – SNWA sayaç ölçümü")
    ax.plot(x, senaryo["Çim, Kc 0,95 (bizim varsayım)"], color=MAVI, lw=2, ls="--",
            label="Çim – bizim hesap (Kc 0,95, yağmurlama %70)")
    ax.plot(x, xer_olc, color=TURUNCU, lw=2, marker="o", ms=6, label="Kurakçıl – SNWA sayaç ölçümü")
    ax.plot(x, senaryo["Kurakçıl, Kc 0,50 (lavanta)"], color=TURUNCU, lw=2, ls="--",
            label="Kurakçıl – bizim hesap (Kc 0,50, damla %90)")
    ax.plot(x, et0, color="#8a8984", lw=1.5, ls=":", label="ET₀ (ERA5, 1995–2001 ort.)")
    ax.set_xticks(x, AYLAR)
    ax.set_ylabel("mm / ay (= L/m²)")
    ax.set_title("Test 1 – Las Vegas: ölçülen sulama ve bizim hesap", loc="left", fontsize=11, color="#1f1f1d")
    ax.grid(axis="y", color="#e8e7e1", lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.text(0.01, 0.01, "Ölçüm: Sovocool (2005) SNWA Xeriscape Conversion Study, Tablo 18 (ortalamalar). "
             "İklim: Open-Meteo/ERA5.", fontsize=8, color="#5f5e5a")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(CIKTI / "test1_snwa_lasvegas.png", dpi=150)
    return sonuc


# ───────────────────────────── Test 2: İZSU ─────────────────────────────
def izsu_oku():
    yol = ONBELLEK / "izsu_mahalle_tuketim.csv"
    if not yol.exists():
        print("İZSU dosyası indiriliyor (76 MB)…")
        with requests.get(IZSU_URL, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(yol, "wb") as f:
                for parca in r.iter_content(1 << 20):
                    f.write(parca)
    toplam = defaultdict(float)   # ORTALAMA_TUKETIM satır toplamı
    carpim = defaultdict(float)   # ABONE_ADEDI × ORTALAMA_TUKETIM
    abone = defaultdict(float)
    with open(yol, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["ABONELIK_GRUBU"] != "Sulama":
                continue
            k = (int(r["YIL"]), int(r["AY"]))
            n, o = float(r["ABONE_ADEDI"] or 0), float(r["ORTALAMA_TUKETIM"] or 0)
            toplam[k] += o
            carpim[k] += n * o
            abone[k] += n
    return toplam, carpim, abone


def test_izsu():
    toplam, carpim, abone = izsu_oku()
    iklim = iklim_aylik("izmir", 38.42, 27.14, "2014-01-01", "2024-09-30")
    aylar = sorted(k for k in toplam if k in iklim)
    model = {k: ihtiyac(*iklim[k], 0.95, 0.70) for k in aylar}
    # Abone sayısı 2014→2024 ikiye katlandı, bu yüzden normalize etmek şart. Ama dosyada yalnız o ay
    # faturalanan aboneler var (Ocak ~940, Ağustos ~2.040). Aylık sayıya bölmek mevsimselliği bozar;
    # bu yüzden o yılın ortalama aylık abone sayısına bölüyoruz.
    yil_abone = {y: st.mean(abone[k] for k in aylar if k[0] == y) for y in {k[0] for k in aylar}}
    ab_top = {k: toplam[k] / yil_abone[k[0]] for k in aylar}
    ab_car = {k: carpim[k] / yil_abone[k[0]] for k in aylar}
    # Fatura gecikmesi: t ayında okunan sayaç büyük ölçüde t-1 ayının tüketimidir (hipotez, ayrıca raporlanır)
    onceki = {k: (k[0] - 1, 12) if k[1] == 1 else (k[0], k[1] - 1) for k in aylar}
    model_g1 = {k: model[onceki[k]] for k in aylar if onceki[k] in model}

    def profil(d):
        return [st.mean(d[k] for k in aylar if k[1] == a) for a in range(1, 13)]

    p_model, p_top, p_car = profil(model), profil(ab_top), profil(ab_car)

    # Aylık anomali: her değerden o ayın uzun dönem ortalamasını çıkar → mevsimsellik ayıklanır
    def anomali(d, p):
        return [d[k] - p[k[1] - 1] for k in aylar]

    # Yaz (Haz–Eyl) toplamları, yıl bazında
    yillar = sorted({y for y, a in aylar if all((y, m) in model for m in range(6, 10))})
    yaz_model = [sum(model[(y, m)] for m in range(6, 10)) for y in yillar]
    yaz_top = [sum(ab_top[(y, m)] for m in range(6, 10)) for y in yillar]

    def trendsiz(v):
        n = len(v)
        xs = list(range(n))
        mx, my = st.mean(xs), st.mean(v)
        b = sum((a - mx) * (c - my) for a, c in zip(xs, v)) / sum((a - mx) ** 2 for a in xs)
        return [c - (my + b * (a - mx)) for a, c in zip(xs, v)]

    k1 = [k for k in aylar if k in model_g1]
    p_model_g1 = [st.mean(model_g1[k] for k in k1 if k[1] == a) for a in range(1, 13)]
    yaz_top_g1 = [sum(ab_top[(y, m)] for m in range(7, 11) if (y, m) in ab_top) for y in yillar]
    tam = [i for i, y in enumerate(yillar) if all((y, m) in ab_top for m in range(7, 11))]
    sonuc = {
        "ay_sayisi": len(aylar), "donem": f"{aylar[0][0]}/{aylar[0][1]:02d}–{aylar[-1][0]}/{aylar[-1][1]:02d}",
        "r_mevsim_profili_satir_toplami": pearson(p_model, p_top),
        "r_mevsim_profili_adet_carpimi": pearson(p_model, p_car),
        "r_mevsim_profili_1ay_gecikme": pearson(p_model_g1, p_top),
        "r_tum_aylar": pearson([model[k] for k in aylar], [ab_top[k] for k in aylar]),
        "r_tum_aylar_1ay_gecikme": pearson([model_g1[k] for k in k1], [ab_top[k] for k in k1]),
        "r_aylik_anomali": pearson(anomali(model, p_model), anomali(ab_top, p_top)),
        "r_yaz_toplami_yillar_arasi_trendsiz": pearson(trendsiz(yaz_model), trendsiz(yaz_top)),
        "r_yaz_yillar_arasi_1ay_gecikme_trendsiz": pearson(trendsiz([yaz_model[i] for i in tam]),
                                                           trendsiz([yaz_top_g1[i] for i in tam])),
        "yaz_yillar": yillar,
        "kis_tuketim_orani_%": 100 * sum(p_top[i] for i in (0, 1, 11)) / sum(p_top),
        "kis_model_orani_%": 100 * sum(p_model[i] for i in (0, 1, 11)) / sum(p_model),
    }
    # Kaba ölçek: abone başına yıllık tüketim / m² başına yıllık ihtiyaç → abone başına eşdeğer çim m²
    yil_ihtiyac = sum(p_model)  # L/m²·yıl = mm
    sonuc["abone_basina_esdeger_cim_m2_satir_toplami"] = 1000 * sum(p_top) / yil_ihtiyac
    sonuc["abone_basina_esdeger_cim_m2_adet_carpimi"] = 1000 * sum(p_car) / yil_ihtiyac

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 8.5), height_ratios=[1, 1.1], facecolor="#ffffff")
    x = list(range(12))
    # Ortak taban: her seri kendi yıllık ortalamasına göre endeks (=100); tek eksen
    def endeks(v):
        m = st.mean(v)
        return [100 * a / m for a in v]
    a1.plot(x, endeks(p_top), color=MAVI, lw=2, marker="o", ms=6,
            label="İZSU park ve mezarlık tüketimi (abone başına)")
    a1.plot(x, endeks(p_model), color=TURUNCU, lw=2, marker="o", ms=6,
            label="Bizim hesap: çim sulama ihtiyacı (aynı ay)")
    a1.plot(x, endeks(p_model_g1), color=YESIL, lw=2, ls="--", marker="o", ms=5,
            label=f"Bizim hesap, 1 ay fatura gecikmesiyle (r = {sonuc['r_mevsim_profili_1ay_gecikme']:.2f})")
    a1.axhline(100, color="#c3c2b7", lw=0.8)
    a1.set_xticks(x, AYLAR)
    a1.set_ylabel("Endeks (yıllık ortalama = 100)")
    a1.set_title(f"Test 2a – İzmir: aylık profil, {sonuc['donem']} ortalaması  "
                 f"(r = {sonuc['r_mevsim_profili_satir_toplami']:.2f})",
                 loc="left", fontsize=11, color="#1f1f1d")
    a1.grid(axis="y", color="#e8e7e1", lw=0.8)
    a1.set_axisbelow(True)
    a1.legend(frameon=False, fontsize=9, loc="upper left")

    xs = list(range(len(yillar)))
    a2.plot(xs, endeks(yaz_top), color=MAVI, lw=2, marker="o", ms=6, label="İZSU yaz tüketimi (abone başına)")
    a2.plot(xs, endeks(yaz_model), color=TURUNCU, lw=2, marker="o", ms=6, label="Bizim hesap: yaz ihtiyacı")
    a2.axhline(100, color="#c3c2b7", lw=0.8)
    a2.set_xticks(xs, [str(y) for y in yillar])
    a2.set_ylabel("Endeks (dönem ortalaması = 100)")
    a2.set_title(f"Test 2b – Haziran–Eylül toplamı, yıllar arası  "
                 f"(trendsiz r = {sonuc['r_yaz_toplami_yillar_arasi_trendsiz']:.2f})",
                 loc="left", fontsize=11, color="#1f1f1d")
    a2.grid(axis="y", color="#e8e7e1", lw=0.8)
    a2.set_axisbelow(True)
    a2.legend(frameon=False, fontsize=9, loc="upper left")
    fig.text(0.01, 0.01, "Tüketim: İZSU / İzmir BB Açık Veri Portalı (CC BY 4.0), 'Sulama' grubu, "
             "tarafımızca toplanıp normalize edildi. "
             "İklim: Open-Meteo/ERA5, İzmir merkez (38,42; 27,14).", fontsize=8, color="#5f5e5a")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(CIKTI / "test2_izsu_izmir.png", dpi=150)

    with open(CIKTI / "test2_izsu_aylik.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["yil", "ay", "abone_adedi", "tuketim_satir_toplami_m3", "model_cim_ihtiyaci_mm",
                    "et0_mm", "yagis_mm"])
        for k in aylar:
            w.writerow([k[0], k[1], int(abone[k]), round(toplam[k]), round(model[k], 1),
                        round(iklim[k][0], 1), round(iklim[k][1], 1)])
    return sonuc


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    def yuvarla(v):
        if isinstance(v, float):
            return round(v, 3)
        if isinstance(v, dict):
            return {k: yuvarla(a) for k, a in v.items()}
        return v
    sonuclar = yuvarla({"snwa": test_snwa(), "izsu": test_izsu()})
    metin = json.dumps(sonuclar, ensure_ascii=False, indent=2)
    (CIKTI / "dogrulama_sonuclari.json").write_text(metin, encoding="utf-8")
    print(metin)


if __name__ == "__main__":
    main()
