"""Genelleştirilmiş uydu analizi (AI-3): Türkiye'nin herhangi bir il/ilçesi için sulanan kentsel yeşil.

Yöntem (prototip/uydu_izmir.py ile birebir aynı kural):
    1. Kentsel alan: 250 m çevresinin %40'ından fazlası ESA WorldCover "yapı" (sınıf 50)
    2. WorldCover ağaç (10) ya da su (80) değil
    3. Temmuz–Ağustos Sentinel-2 L2A NDVI medyanı > 0,5

Açık veri kaynakları (kayıtsız):
    - ESA WorldCover 2021 v200 (CC BY 4.0)
    - Sentinel-2 L2A, Earth Search / AWS (Copernicus)
    - İzmir ilçe sınırları: OpenStreetMap (ODbL)
"""
from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from scipy.ndimage import uniform_filter
from shapely.geometry import LineString
from shapely.ops import polygonize, transform as shp_transform, unary_union

from src.veri.iklim import ONBELLEK

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

KOK = Path(__file__).resolve().parents[2]
WC_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{}_Map.tif"
STAC_URL = "https://earth-search.aws.element84.com/v1"
NDVI_ESIK = 0.5
CIM_SINIF = 30
CS = 10.0

# prototip/uydu_izmir.py ile aynı İzmir ızgarası
IZMIR_BBOX = (26.80, 38.27, 27.33, 38.60)
IZMIR_EPSG = 32635


def utm_epsg(lat: float, lon: float) -> int:
    """Koordinat için uygun WGS84 UTM EPSG kodu (Türkiye: 32635–32638)."""
    zone = int((lon + 180.0) // 6.0) + 1
    return (32600 if lat >= 0 else 32700) + zone


def worldcover_karolari(lon0: float, lat0: float, lon1: float, lat1: float) -> list[str]:
    """Bbox ile kesişen 3°×3° ESA WorldCover karo adları (ör. ['N39E030', 'N39E033'])."""
    lat_bas = (math.floor(lat0) // 3) * 3
    lat_bit = (math.floor(lat1) // 3) * 3
    lon_bas = (math.floor(lon0) // 3) * 3
    lon_bit = (math.floor(lon1) // 3) * 3
    karolar = []
    for la in range(lat_bas, lat_bit + 1, 3):
        for lo in range(lon_bas, lon_bit + 1, 3):
            ns = f"N{la:02d}" if la >= 0 else f"S{abs(la):02d}"
            ew = f"E{lo:03d}" if lo >= 0 else f"W{abs(lo):03d}"
            karolar.append(f"{ns}{ew}")
    return karolar


def _oku_izgaraya(href: str, epsg: int, trf: Affine, w: int, h: int,
                  yontem=Resampling.nearest, nodata=None) -> np.ndarray:
    with rasterio.open(href) as src:
        with WarpedVRT(
            src,
            crs=f"EPSG:{epsg}",
            transform=trf,
            width=w,
            height=h,
            resampling=yontem,
            src_nodata=nodata if nodata is not None else src.nodata,
        ) as vrt:
            return vrt.read(1)


def _harita_ciz(yol: Path, wc: np.ndarray, sulanan: np.ndarray, kuru_cim: np.ndarray,
                baslik: str, alt_not: str, sinir_xy=None, k: int = 1):
    h, w = wc.shape
    if k > 1:
        def alt(a):
            return a[: h // k * k, : w // k * k].reshape(h // k, k, w // k, k).mean(axis=(1, 3))
        rgb = np.full((h // k, w // k, 3), 1.0)
        rgb[alt((wc == 50).astype(float)) > 0.5] = (0.85, 0.84, 0.81)
        rgb[alt((wc == 10).astype(float)) > 0.5] = (0.55, 0.70, 0.55)
        rgb[alt(kuru_cim.astype(float)) > 0.3] = (0.93, 0.63, 0.0)
        rgb[alt(sulanan.astype(float)) > 0] = (0.10, 0.69, 0.48)
        rgb[alt((wc == 80).astype(float)) > 0.5] = (0.80, 0.88, 0.97)
    else:
        rgb = np.full((h, w, 3), 0.97)
        rgb[wc == 50] = (0.85, 0.84, 0.81)
        rgb[wc == 10] = (0.55, 0.70, 0.55)
        rgb[kuru_cim] = (0.93, 0.63, 0.0)
        rgb[sulanan] = (0.10, 0.69, 0.48)
        rgb[wc == 80] = (0.80, 0.88, 0.97)

    plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9.5})
    fig, ax = plt.subplots(figsize=(7.5, 6.8), facecolor="#ffffff")
    ax.imshow(rgb, interpolation="nearest")
    if sinir_xy:
        for xs, ys in sinir_xy:
            ax.plot(xs, ys, color="#1f2937", lw=1.2)
    ax.set_xlim(0, rgb.shape[1])
    ax.set_ylim(rgb.shape[0], 0)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(
        handles=[
            Patch(color=(0.10, 0.69, 0.48), label="Sulanan kentsel yeşil (NDVI > 0,5)"),
            Patch(color=(0.93, 0.63, 0.0), label="Kuru çim/çayır (kentsel)"),
            Patch(color=(0.55, 0.70, 0.55), label="Ağaç"),
            Patch(color=(0.85, 0.84, 0.81), label="Yapı"),
        ],
        loc="lower left",
        fontsize=8,
        framealpha=0.92,
    )
    ax.set_title(baslik, loc="left", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, alt_not, fontsize=7, color="#5f5e5a")
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    fig.savefig(yol, dpi=140)
    plt.close(fig)


def bolge_uydu_analizi(ad: str, lat: float, lon: float, yaricap_km: float = 4.0,
                       yil: int = 2023, onbellek: Path = ONBELLEK) -> dict:
    """Herhangi bir (lat, lon) noktası çevresinde 2*yaricap_km karelik canlı uydu analizi.

    Sonuç JSON ve PNG olarak veri_onbellek/ altına yazılır; sonraki çağrılar anında döner.
    """
    onbellek.mkdir(exist_ok=True)
    anahtar = f"uydu_bolge_{lat:.2f}_{lon:.2f}_{yaricap_km:.1f}km_{yil}"
    json_yol = onbellek / f"{anahtar}.json"
    png_yol = onbellek / f"{anahtar}.png"
    if json_yol.exists() and png_yol.exists():
        veri = json.loads(json_yol.read_text(encoding="utf-8"))
        veri["ad"] = ad
        return veri

    epsg = utm_epsg(lat, lon)
    to_utm = Transformer.from_crs(4326, epsg, always_xy=True)
    to_wgs = Transformer.from_crs(epsg, 4326, always_xy=True)
    cx, cy = to_utm.transform(lon, lat)
    yaricap_m = float(yaricap_km) * 1000.0
    x0, y1 = cx - yaricap_m, cy + yaricap_m
    x1, y0 = cx + yaricap_m, cy - yaricap_m
    w = max(100, int((x1 - x0) / CS))
    h = max(100, int((y1 - y0) / CS))
    trf = Affine(CS, 0, x0, 0, -CS, y1)

    lon0, lat0 = to_wgs.transform(x0, y0)
    lon1, lat1 = to_wgs.transform(x1, y1)
    bbox = (min(lon0, lon1), min(lat0, lat1), max(lon0, lon1), max(lat0, lat1))

    # 1. ESA WorldCover 2021 (10 m)
    karolar = worldcover_karolari(*bbox)
    wc = np.zeros((h, w), dtype="uint8")
    for k in karolar:
        parca = _oku_izgaraya(WC_URL.format(k), epsg, trf, w, h, Resampling.nearest, 0)
        wc = np.maximum(wc, parca)

    # 2. Sentinel-2 L2A (Temmuz–Ağustos, en bulutsuz 2 sahne / karo)
    client = Client.open(STAC_URL)
    items = []
    for bulut in (10, 35, 60):
        items = list(
            client.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime=f"{yil}-07-15/{yil}-08-31",
                query={"eo:cloud_cover": {"lt": bulut}},
                max_items=30,
            ).items()
        )
        if items:
            break
    if not items:
        raise RuntimeError(f"{ad} için {yil} Temmuz–Ağustos Sentinel-2 görüntüsü bulunamadı.")

    mgrs = defaultdict(list)
    for it in items:
        mgrs[it.properties.get("s2:mgrs_tile") or it.id.split("_")[1]].append(it)
    secili = [i for v in mgrs.values() for i in sorted(v, key=lambda x: x.properties["eo:cloud_cover"])[:2]]

    katman = []
    for it in secili:
        red = _oku_izgaraya(it.assets["red"].href, epsg, trf, w, h, Resampling.bilinear, 0).astype("float32")
        nir = _oku_izgaraya(it.assets["nir"].href, epsg, trf, w, h, Resampling.bilinear, 0).astype("float32")
        nd = np.where((red > 0) & (nir > 0), (nir - red) / np.maximum(nir + red, 1.0), np.nan)
        katman.append(nd.astype("float32"))
    ndvi = np.nanmedian(np.stack(katman), axis=0).astype("float32")

    # 3. Kural
    kentsel = uniform_filter((wc == 50).astype("float32"), size=25) > 0.4
    sulanan = kentsel & (wc != 10) & (wc != 80) & (ndvi > NDVI_ESIK)
    kuru_cim = kentsel & (wc == CIM_SINIF) & (ndvi <= NDVI_ESIK)

    px = CS * CS
    cap_km = round(2 * yaricap_km, 1)
    _harita_ciz(
        png_yol,
        wc,
        sulanan,
        kuru_cim,
        baslik=f"{ad} — sulanan kentsel yeşil ({cap_km:g}×{cap_km:g} km, yaz {yil})",
        alt_not="© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021, 2023). 10×10 m.",
        k=1,
    )

    sonuc = {
        "ad": ad,
        "lat": round(float(lat), 4),
        "lon": round(float(lon), 4),
        "yaricap_km": float(yaricap_km),
        "yil": int(yil),
        "kentsel_m2": int(kentsel.sum() * px),
        "sulanan_yesil_m2": int(sulanan.sum() * px),
        "kuru_cim_m2": int(kuru_cim.sum() * px),
        "agac_m2": int((wc == 10).sum() * px),
        "sahne_sayisi": int(len(secili)),
        "harita_dosya": png_yol.name,
    }
    json_yol.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    return sonuc


def izmir_ilce_haritasi(ilce: str, onbellek: Path = ONBELLEK) -> Path:
    """Önbellekteki İzmir 2023 verisinden seçili ilçeye yakınlaştırılmış harita üretir (< 0,5 sn)."""
    tam_harita = KOK / "prototip" / "cikti" / "uydu_izmir_harita.png"
    guvenli = "".join(c for c in ilce if c.isalnum() or c in ("-", "_", "ç", "ğ", "ı", "ö", "ş", "ü", "Ç", "Ğ", "İ", "Ö", "Ş", "Ü"))
    if not guvenli:
        return tam_harita

    onbellek.mkdir(exist_ok=True)
    hedef = onbellek / f"uydu_izmir_ilce_{guvenli}.png"
    if hedef.exists():
        return hedef

    ndvi_yol = onbellek / "ndvi_izmir_2023.npy"
    wc_yol = onbellek / "wc_izmir.npy"
    osm_yol = onbellek / "osm_izmir_ilceler.json"
    if not (ndvi_yol.exists() and wc_yol.exists() and osm_yol.exists()):
        return tam_harita

    sinir = None
    for rel in json.loads(osm_yol.read_text(encoding="utf-8"))["elements"]:
        if rel.get("tags", {}).get("name") == ilce:
            hatlar = [
                LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                for m in rel["members"]
                if m["type"] == "way" and m.get("role") == "outer" and "geometry" in m
            ]
            sinir = unary_union(list(polygonize(unary_union(hatlar))))
            break
    if sinir is None or sinir.is_empty:
        return tam_harita

    tf = Transformer.from_crs(4326, IZMIR_EPSG, always_xy=True)
    xs, ys = zip(*[tf.transform(x, y) for x in IZMIR_BBOX[::2] for y in IZMIR_BBOX[1::2]])
    x0, y1 = min(xs), max(ys)
    w, h = int((max(xs) - x0) / CS), int((y1 - min(ys)) / CS)
    g = shp_transform(lambda x_, y_, z=None: tf.transform(x_, y_), sinir)
    gx0, gy0, gx1, gy1 = g.bounds

    # 30 piksel (300 m) kenar boşluğu ile kırp
    pad = 30
    c0 = max(0, int((gx0 - x0) / CS) - pad)
    c1 = min(w, int((gx1 - x0) / CS) + pad)
    r0 = max(0, int((y1 - gy1) / CS) - pad)
    r1 = min(h, int((y1 - gy0) / CS) + pad)
    if c1 - c0 < 40 or r1 - r0 < 40:
        return tam_harita

    wc_tam = np.load(wc_yol, mmap_mode="r")
    ndvi_tam = np.load(ndvi_yol, mmap_mode="r")
    wc = np.array(wc_tam[r0:r1, c0:c1])
    ndvi = np.array(ndvi_tam[r0:r1, c0:c1])

    kentsel = uniform_filter((wc == 50).astype("float32"), size=25) > 0.4
    sulanan = kentsel & (wc != 10) & (wc != 80) & (ndvi > NDVI_ESIK)
    kuru_cim = kentsel & (wc == CIM_SINIF) & (ndvi <= NDVI_ESIK)

    k = 2 if max(wc.shape) > 1200 else 1
    sinir_xy = []
    for parca in getattr(g, "geoms", [g]):
        pxs, pys = parca.exterior.xy
        sinir_xy.append((
            [(a - x0) / CS / k - c0 / k for a in pxs],
            [(y1 - b) / CS / k - r0 / k for b in pys],
        ))

    _harita_ciz(
        hedef,
        wc,
        sulanan,
        kuru_cim,
        baslik=f"İzmir / {ilce} — sulanan kentsel yeşil, yaz 2023",
        alt_not="© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021, 2023) · Sınırlar © OpenStreetMap.",
        sinir_xy=sinir_xy,
        k=k,
    )
    return hedef
