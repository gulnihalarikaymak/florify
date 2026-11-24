"""Sadeleştirilmiş AI-3: İzmir merkez ilçelerinde sulanan çim alanı ve İZSU faturalarıyla karşılaştırma.

Kural (her 10×10 m kare için):
    kentsel alan (250 m çevresinin %40'ından fazlası WorldCover "yapı")
    VE WorldCover ağaç ya da su değil
    VE Temmuz–Ağustos 2023 NDVI medyanı > 0,5
    → "sulanan kentsel yeşil (çim/çalı)". Ağustos'ta yağış yok; yeşil kalan alan sulanıyordur.

Denenen kurallar (hepsi docs/ai3_uydu_plani.md içinde raporlanır):
    A) WorldCover çim + yaz yeşil: İZSU ile ρ = 0,08 (tarım ve merayı da sayıyor, kent parklarını kaçırıyor)
    B) A + yalnız kentsel: ρ = 0,61
    C) kentsel + ağaç/su değil + yaz yeşil (bu script): ρ = 0,85; kentsel alan sabit tutulunca kısmi ρ = 0,70

Veri (hepsi açık, hesapsız):
    ESA WorldCover 2021 v200 (CC BY 4.0) · Sentinel-2 L2A, Earth Search/AWS (Copernicus)
    İlçe sınırları: OpenStreetMap (ODbL) · İZSU tüketim (CC BY 4.0)

Çalıştırma: .venv\\Scripts\\python prototip\\uydu_izmir.py
"""
import csv
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from affine import Affine
from pyproj import Transformer
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.vrt import WarpedVRT
from scipy.ndimage import uniform_filter
from scipy.stats import pearsonr, rankdata, spearmanr
from shapely.geometry import LineString, mapping
from shapely.ops import polygonize, transform as shp_transform, unary_union

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "prototip" / "cikti"
ONBELLEK = KOK / "veri_onbellek"
YIL = 2023
NDVI_ESIK = 0.5
CIM = 30  # WorldCover: 10 ağaç, 20 çalı, 30 çayır/çim, 40 tarım, 50 yapı, 60 çıplak, 80 su
ILCELER = ["Konak", "Karşıyaka", "Bornova", "Buca", "Çiğli", "Bayraklı", "Karabağlar", "Gaziemir",
           "Narlıdere", "Balçova", "Güzelbahçe"]
BBOX = (26.80, 38.27, 27.33, 38.60)  # lon0, lat0, lon1, lat1 (merkez ilçeleri kapsar)
EPSG = 32635
CS = 10.0
WC_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{}_Map.tif"


def izgara():
    tf = Transformer.from_crs(4326, EPSG, always_xy=True)
    xs, ys = zip(*[tf.transform(x, y) for x in BBOX[::2] for y in BBOX[1::2]])
    x0, y1 = min(xs), max(ys)
    w, h = int((max(xs) - x0) / CS), int((y1 - min(ys)) / CS)
    return Affine(CS, 0, x0, 0, -CS, y1), w, h, tf


def oku_izgaraya(href, trf, w, h, yontem=Resampling.nearest, nodata=None):
    with rasterio.open(href) as src:
        with WarpedVRT(src, crs=f"EPSG:{EPSG}", transform=trf, width=w, height=h,
                       resampling=yontem, src_nodata=nodata if nodata is not None else src.nodata) as vrt:
            return vrt.read(1)


def ilce_sinirlari():
    yol = ONBELLEK / "osm_izmir_ilceler.json"
    if not yol.exists():
        q = ('[out:json][timeout:300];area["boundary"="administrative"]["admin_level"="4"]["name"="İzmir"]->.a;'
             'relation["boundary"="administrative"]["admin_level"="6"](area.a);out geom;')
        for deneme in range(6):
            for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
                r = requests.post(url, data={"data": q}, headers={"User-Agent": "su-tasarrufu-prototip/0.1"},
                                  timeout=400)
                if r.ok:
                    break
            if r.ok:
                break
            time.sleep(30)
        r.raise_for_status()
        yol.write_text(r.text, encoding="utf-8")
    sinir = {}
    for rel in json.loads(yol.read_text(encoding="utf-8"))["elements"]:
        hatlar = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                  for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer" and "geometry" in m]
        sinir[rel["tags"]["name"]] = unary_union(list(polygonize(unary_union(hatlar))))
    return sinir


def yaz_ndvi(trf, w, h):
    yol = ONBELLEK / f"ndvi_izmir_{YIL}.npy"
    if yol.exists():
        return np.load(yol)
    items = list(Client.open("https://earth-search.aws.element84.com/v1").search(
        collections=["sentinel-2-l2a"], bbox=BBOX, datetime=f"{YIL}-07-15/{YIL}-08-31",
        query={"eo:cloud_cover": {"lt": 5}}, max_items=60).items())
    karo = defaultdict(list)
    for it in items:
        karo[it.properties.get("s2:mgrs_tile") or it.id.split("_")[1]].append(it)
    secili = [i for v in karo.values() for i in sorted(v, key=lambda i: i.properties["eo:cloud_cover"])[:3]]
    print(f"Sentinel-2: {len(secili)} sahne, karolar {sorted(karo)}")
    katman = []
    for it in secili:
        red = oku_izgaraya(it.assets["red"].href, trf, w, h, Resampling.bilinear, 0).astype("float32")
        nir = oku_izgaraya(it.assets["nir"].href, trf, w, h, Resampling.bilinear, 0).astype("float32")
        nd = np.where((red > 0) & (nir > 0), (nir - red) / np.maximum(nir + red, 1), np.nan)
        katman.append(nd.astype("float32"))
        print("  okundu:", it.id)
    ndvi = np.nanmedian(np.stack(katman), axis=0).astype("float32")
    np.save(yol, ndvi)
    return ndvi


def worldcover(trf, w, h):
    yol = ONBELLEK / "wc_izmir.npy"
    if yol.exists():
        return np.load(yol)
    parca = [oku_izgaraya(WC_URL.format(k), trf, w, h, Resampling.nearest, 0) for k in ("N36E024", "N36E027")]
    wc = np.maximum(parca[0], parca[1])  # karolar örtüşmez; boş yer 0
    np.save(yol, wc)
    return wc


def izsu_ilce(yil):
    yol = ONBELLEK / "izsu_mahalle_tuketim.csv"
    if not yol.exists():
        raise SystemExit("Önce prototip/dogrulama_testleri.py çalıştırılmalı (İZSU dosyasını indirir).")
    top = defaultdict(float)
    with open(yol, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["ABONELIK_GRUBU"] == "Sulama" and int(r["YIL"]) == yil:
                top[r["ILCE"].strip()] += float(r["ORTALAMA_TUKETIM"] or 0)
    return top


def tr_ust(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    trf, w, h, tf = izgara()
    print(f"Izgara: {w}×{h} piksel ({w * h / 1e6:.1f} M)")
    ndvi = yaz_ndvi(trf, w, h)
    wc = worldcover(trf, w, h)
    kentsel = uniform_filter((wc == 50).astype("float32"), size=25) > 0.4  # 250 m pencere
    sulanan = kentsel & (wc != 10) & (wc != 80) & (ndvi > NDVI_ESIK)
    kuru_cim = kentsel & (wc == CIM) & (ndvi <= NDVI_ESIK)

    sinir = ilce_sinirlari()
    kod = np.zeros((h, w), dtype="int16")
    for i, ad in enumerate(ILCELER, 1):
        g = shp_transform(lambda x, y, z=None: tf.transform(x, y), sinir[ad])
        kod |= rasterize([(mapping(g), i)], out_shape=(h, w), transform=trf, dtype="int16") * (kod == 0)
    izsu = izsu_ilce(YIL)
    px = CS * CS
    satir = []
    for i, ad in enumerate(ILCELER, 1):
        m = kod == i
        alan_kapsanan = m.sum() * px
        alan_ilce = shp_transform(lambda x, y, z=None: tf.transform(x, y), sinir[ad]).area
        satir.append({"ilce": ad, "kapsama_%": round(100 * alan_kapsanan / alan_ilce, 1),
                      "kentsel_m2": int((kentsel & m).sum() * px),
                      "sulanan_yesil_m2": int((sulanan & m).sum() * px),
                      "kuru_cim_m2": int((kuru_cim & m).sum() * px),
                      "agac_m2": int(((wc == 10) & m).sum() * px),
                      "izsu_2023_m3": round(izsu.get(tr_ust(ad), float("nan")))})
    x = [s["sulanan_yesil_m2"] for s in satir]
    y = [s["izsu_2023_m3"] for s in satir]
    rho, p_s = spearmanr(x, y)
    r, p_p = pearsonr(x, y)
    kent = [s["kentsel_m2"] for s in satir]
    rho_kent, _ = spearmanr(kent, y)

    def kalan(a):  # sıra tabanlı; kentsel alanın etkisi çıkarılmış artık
        A = np.c_[np.ones(len(a)), rankdata(kent)]
        return rankdata(a) - A @ np.linalg.lstsq(A, rankdata(a), rcond=None)[0]
    kismi, p_k = pearsonr(kalan(x), kalan(y))
    ozet = {"yil": YIL, "kural": f"kentsel, WorldCover ağaç/su değil, yaz NDVI>{NDVI_ESIK}", "n_ilce": len(satir),
            "spearman_kentsel_alan_ile": round(float(rho_kent), 3),
            "kismi_rho_kentsel_alan_sabit": round(float(kismi), 3), "kismi_p": round(float(p_k), 4),
            "spearman_rho": round(float(rho), 3), "spearman_p": round(float(p_s), 4),
            "pearson_r": round(float(r), 3), "pearson_p": round(float(p_p), 4),
            "toplam_sulanan_yesil_m2": sum(x), "toplam_izsu_m3": sum(y),
            "m3_per_m2": round(sum(y) / max(sum(x), 1), 2), "ilceler": satir}
    metin = json.dumps(ozet, ensure_ascii=False, indent=2)
    (CIKTI / "uydu_izmir_sonuc.json").write_text(metin, encoding="utf-8")
    # Panel için türetilmiş tablo (repoda tutulur; atıf satırı başlıkta değil, dokümanda ve panelde)
    with open(KOK / "kaynaklar" / "veri" / f"uydu_izmir_ilce_{YIL}.csv", "w", newline="", encoding="utf-8") as f:
        yaz = csv.DictWriter(f, fieldnames=list(satir[0].keys()))
        yaz.writeheader()
        yaz.writerows(satir)
    print(metin)

    # Grafik 1: ilçe karşılaştırması
    plt.rcParams.update({"font.family": "Segoe UI", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#ffffff")
    ax.scatter([v / 1e3 for v in x], [v / 1e3 for v in y], s=60, color="#2a78d6", zorder=3)
    for s in satir:
        ax.annotate(s["ilce"], (s["sulanan_yesil_m2"] / 1e3, s["izsu_2023_m3"] / 1e3), xytext=(5, 4),
                    textcoords="offset points", fontsize=8.5, color="#3d3d3a")
    ax.set_xlabel("Uydudan bulunan sulanan kentsel yeşil (bin m²)")
    ax.set_ylabel("İZSU park ve mezarlık sulaması, 2023 (bin m³)")
    ax.set_title(f"İzmir merkez ilçeleri: uydu ve fatura (Spearman ρ = {rho:.2f}, n = {len(satir)}; "
                 f"kentsel alan sabitken ρ = {kismi:.2f})",
                 loc="left", fontsize=11)
    ax.grid(color="#e8e7e1", lw=0.8)
    ax.set_axisbelow(True)
    fig.text(0.01, 0.01, "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021, 2023). "
             "İlçe sınırları © OpenStreetMap. Tüketim: İZSU (CC BY 4.0).", fontsize=7, color="#5f5e5a")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(CIKTI / "uydu_izmir_ilce.png", dpi=150)

    # Grafik 2: harita (4× küçültülmüş)
    k = 4
    rgb = np.full((h // k, w // k, 3), 1.0)
    alt = lambda a: a[: h // k * k, : w // k * k].reshape(h // k, k, w // k, k).mean(axis=(1, 3))
    rgb[alt((wc == 50).astype(float)) > 0.5] = (0.85, 0.84, 0.81)
    rgb[alt((wc == 10).astype(float)) > 0.5] = (0.55, 0.70, 0.55)
    rgb[alt(kuru_cim.astype(float)) > 0.3] = (0.93, 0.63, 0.0)
    rgb[alt(sulanan.astype(float)) > 0] = (0.10, 0.69, 0.48)  # küçük parklar kaybolmasın: blokta 1 piksel yeter
    rgb[alt((wc == 80).astype(float)) > 0.5] = (0.80, 0.88, 0.97)
    fig, ax = plt.subplots(figsize=(10, 8), facecolor="#ffffff")
    ax.imshow(rgb, interpolation="nearest")
    for ad in ILCELER:
        g = shp_transform(lambda x_, y_, z=None: tf.transform(x_, y_), sinir[ad])
        for parca in getattr(g, "geoms", [g]):
            cx, cy = parca.exterior.xy
            ax.plot([(a - trf.c) / CS / k for a in cx], [(trf.f - b) / CS / k for b in cy], color="#5f5e5a", lw=0.6)
    ax.set_xlim(0, w // k)
    ax.set_ylim(h // k, 0)
    ax.set_xticks([])
    ax.set_yticks([])
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=(0.10, 0.69, 0.48), label="Sulanan kentsel yeşil (Ağustos'ta yeşil)"),
                       Patch(color=(0.93, 0.63, 0.0), label="Kuru çim/çayır (kentsel)"),
                       Patch(color=(0.55, 0.70, 0.55), label="Ağaç"),
                       Patch(color=(0.85, 0.84, 0.81), label="Yapı")], loc="lower left", fontsize=8.5)
    ax.set_title(f"İzmir merkez – sulanan kentsel yeşil, yaz {YIL}", loc="left", fontsize=11)
    fig.text(0.01, 0.01, "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021, 2023). "
             "İlçe sınırları © OpenStreetMap.", fontsize=7, color="#5f5e5a")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(CIKTI / "uydu_izmir_harita.png", dpi=140)


if __name__ == "__main__":
    main()
