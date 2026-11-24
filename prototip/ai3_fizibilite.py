"""AI-3 fizibilite: açık Sentinel-2 ile bir parkta sulanan yeşil alan görünüyor mu?

Veri (hepsi hesapsız, açık):
  - Sentinel-2 L2A COG: Element84 Earth Search STAC (AWS Open Data), Copernicus lisansı
  - Park sınırı: OpenStreetMap / Overpass (ODbL)
Bu henüz model değil: yaz ve ilkbahar NDVI'ı ile basit bir kural. Sonraki adım etiketli veriyle sınıflandırıcı.

Çalıştırma: .venv\\Scripts\\python prototip\\ai3_fizibilite.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from pyproj import Transformer
from pystac_client import Client
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as shp_transform

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "prototip" / "cikti"
ONBELLEK = KOK / "veri_onbellek"
STAC = "https://earth-search.aws.element84.com/v1"
OVERPASS = "https://overpass-api.de/api/interpreter"
PARKLAR = [642980967, 504133285, 669375070]  # Batıkent Spor ve Dinlenme Parkı, Millî İrade Parkı (2 parça)
YIL = 2024
YAZ_ESIK, BAHAR_ESIK = 0.5, 0.5


def park_poligonlari():
    """Birkaç way için OSM ana API'si (Overpass meşgulken de çalışır)."""
    yol = ONBELLEK / "osm_batikent.json"
    if not yol.exists():
        elemanlar = []
        for wid in PARKLAR:
            r = requests.get(f"https://api.openstreetmap.org/api/0.6/way/{wid}/full.json",
                             headers={"User-Agent": "su-tasarrufu-prototip/0.1"}, timeout=60)
            r.raise_for_status()
            el = r.json()["elements"]
            dugum = {e["id"]: (e["lon"], e["lat"]) for e in el if e["type"] == "node"}
            way = next(e for e in el if e["type"] == "way")
            elemanlar.append({"id": wid, "tags": way.get("tags", {}),
                              "geometry": [{"lon": dugum[n][0], "lat": dugum[n][1]} for n in way["nodes"]]})
        yol.write_text(json.dumps({"elements": elemanlar}, ensure_ascii=False), encoding="utf-8")
    d = json.loads(yol.read_text(encoding="utf-8"))
    return [(e["tags"].get("name", str(e["id"])), Polygon([(p["lon"], p["lat"]) for p in e["geometry"]]))
            for e in d["elements"]]


def sahneler(bbox, tarih, bulut, n):
    s = Client.open(STAC).search(collections=["sentinel-2-l2a"], bbox=bbox, datetime=tarih,
                                 query={"eo:cloud_cover": {"lt": bulut}}, max_items=30)
    return sorted(s.items(), key=lambda i: i.properties["eo:cloud_cover"])[:n]


def oku(href, sinir_utm):
    with rasterio.open(href) as src:
        w = from_bounds(*sinir_utm, transform=src.transform)
        return src.read(1, window=w, boundless=True).astype("float32"), src.window_transform(w)


def ndvi_medyan(items, sinir_utm):
    katmanlar, tr = [], None
    for it in items:
        red, tr = oku(it.assets["red"].href, sinir_utm)
        nir, _ = oku(it.assets["nir"].href, sinir_utm)
        scl, _ = oku(it.assets["scl"].href, sinir_utm) if "scl" in it.assets else (None, None)
        nd = (nir - red) / np.maximum(nir + red, 1)
        if scl is not None and scl.shape != nd.shape:  # SCL 20 m; 10 m'ye kaba büyütme
            scl = np.kron(scl, np.ones((2, 2)))[: nd.shape[0], : nd.shape[1]]
        if scl is not None:
            nd[np.isin(scl, [3, 8, 9, 10])] = np.nan  # bulut gölgesi, bulut
        katmanlar.append(nd)
    return np.nanmedian(np.stack(katmanlar), axis=0), tr


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parklar = park_poligonlari()
    birlesik = parklar[0][1]
    for _, p in parklar[1:]:
        birlesik = birlesik.union(p)
    lon0, lat0, lon1, lat1 = birlesik.bounds
    bbox = [lon0 - 0.004, lat0 - 0.003, lon1 + 0.004, lat1 + 0.003]

    yaz = sahneler(bbox, f"{YIL}-07-15/{YIL}-08-31", 5, 3)
    p = yaz[0].properties
    epsg = p.get("proj:epsg") or int(p["proj:code"].split(":")[1])
    # İlkbahar: Nisan ortası–Haziran başı; bulutlar SCL ile maskeleniyor. Aynı UTM diliminde kalsın.
    bahar = [i for i in sahneler(bbox, f"{YIL}-04-15/{YIL}-06-10", 40, 10)
             if i.properties.get("proj:code", f"EPSG:{i.properties.get('proj:epsg')}") == f"EPSG:{epsg}"][:3]
    yaz = [i for i in yaz
           if i.properties.get("proj:code", f"EPSG:{i.properties.get('proj:epsg')}") == f"EPSG:{epsg}"]
    if not bahar:
        raise SystemExit("İlkbahar için uygun sahne bulunamadı")
    tf = Transformer.from_crs(4326, epsg, always_xy=True)
    x0, y0 = tf.transform(bbox[0], bbox[1])
    x1, y1 = tf.transform(bbox[2], bbox[3])
    sinir = (x0, y0, x1, y1)

    nd_yaz, trf = ndvi_medyan(yaz, sinir)
    nd_bahar, _ = ndvi_medyan(bahar, sinir)
    with rasterio.open(yaz[0].assets["visual"].href) as src:
        w = from_bounds(*sinir, transform=src.transform)
        rgb = np.moveaxis(src.read([1, 2, 3], window=w, boundless=True), 0, -1)

    park_utm = shp_transform(lambda x, y, z=None: tf.transform(x, y), birlesik)
    icerde = ~geometry_mask([mapping(park_utm)], out_shape=nd_yaz.shape, transform=trf)
    piksel_m2 = abs(trf.a * trf.e)
    yesil_yaz = (nd_yaz > YAZ_ESIK) & icerde
    kuruyan = (nd_bahar > BAHAR_ESIK) & (nd_yaz <= YAZ_ESIK - 0.15) & icerde

    sonuc = {
        "parklar": [ad for ad, _ in parklar],
        "osm_alan_m2": round(park_utm.area),
        "konca_batikent_alan_m2": 431_600,
        "yaz_sahneleri": [i.id for i in yaz], "bahar_sahneleri": [i.id for i in bahar],
        "yazin_yesil_kalan_m2": int(yesil_yaz.sum() * piksel_m2),
        "yazin_yesil_orani_%": round(100 * yesil_yaz.sum() / icerde.sum(), 1),
        "baharda_yesil_yazin_kuruyan_m2": int(kuruyan.sum() * piksel_m2),
        "ndvi_medyan_park_bahar": round(float(np.nanmedian(nd_bahar[icerde])), 3),
        "ndvi_medyan_park_yaz": round(float(np.nanmedian(nd_yaz[icerde])), 3),
    }
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    (CIKTI / "ai3_fizibilite_batikent.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                                        encoding="utf-8")

    # Görsel: gerçek renk, bahar NDVI, yaz NDVI, basit sınıf
    sinif = np.full(nd_yaz.shape, np.nan)
    sinif[icerde] = 0
    sinif[kuruyan] = 1
    sinif[yesil_yaz] = 2
    from matplotlib.colors import ListedColormap
    plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9})
    fig, ax = plt.subplots(1, 4, figsize=(16, 4.6), facecolor="#ffffff")
    kapsam = (0, nd_yaz.shape[1], nd_yaz.shape[0], 0)
    xs, ys = park_utm.exterior.xy if park_utm.geom_type == "Polygon" else \
        max(park_utm.geoms, key=lambda g: g.area).exterior.xy
    inv = ~trf
    px = [inv * (x, y) for x, y in zip(xs, ys)]
    ax[0].imshow(rgb, extent=kapsam)
    ax[0].set_title(f"Gerçek renk, {yaz[0].datetime:%d.%m.%Y}", loc="left")
    for i, (veri, bas) in enumerate([(nd_bahar, "NDVI, Mayıs (medyan)"), (nd_yaz, "NDVI, Temmuz–Ağustos (medyan)")]):
        im = ax[i + 1].imshow(veri, cmap="Greens", vmin=0, vmax=0.9, extent=kapsam)
        ax[i + 1].set_title(bas, loc="left")
    fig.colorbar(im, ax=ax[1:3], fraction=0.025, pad=0.01, label="NDVI")
    cm = ListedColormap(["#d9d7cf", "#eda100", "#1baf7a"])
    ax[3].imshow(sinif, cmap=cm, vmin=0, vmax=2, extent=kapsam, interpolation="nearest")
    ax[3].set_title("Basit kural (model değil)", loc="left")
    from matplotlib.patches import Patch
    ax[3].legend(handles=[Patch(color="#1baf7a", label="Yazın yeşil (sulanıyor / ağaç)"),
                          Patch(color="#eda100", label="Baharda yeşil, yazın kurumuş"),
                          Patch(color="#d9d7cf", label="Diğer (sert zemin, çıplak)")],
                 loc="lower left", fontsize=7.5, frameon=True)
    for a in ax:
        a.plot([p[0] for p in px], [p[1] for p in px], color="#e0245e", lw=1.2)
        a.set_xticks([])
        a.set_yticks([])
    fig.suptitle("Batıkent (Ankara) – Sentinel-2, 2024", x=0.01, ha="left", fontsize=11)
    fig.text(0.01, 0.01, "Sentinel-2 L2A: Copernicus / Earth Search (AWS). Park sınırı: © OpenStreetMap katkıcıları (ODbL). "
             "Pembe çizgi: en büyük park poligonu.", fontsize=7.5, color="#5f5e5a")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(CIKTI / "ai3_fizibilite_batikent.png", dpi=140)
    print("Görsel:", CIKTI / "ai3_fizibilite_batikent.png")


if __name__ == "__main__":
    main()
