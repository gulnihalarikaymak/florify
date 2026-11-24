"""Florify – hafif web sunucusu ve JSON API (ek kütüphane gerektirmez).

Çalıştırma:
    .venv\\Scripts\\python web/sunucu.py
Tarayıcı:
    http://localhost:8000
"""
from __future__ import annotations

import csv
import functools
import json
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scipy.stats import spearmanr

KOK = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from src.hesap import (  # noqa: E402
    HANE_M3_YIL,
    TARIFELER,
    Bolge,
    alan_ihtiyaci,
    belirsizlik_araligi,
    bitki_katalogu,
    bolge_ihtiyaci,
    donusen_alan_m2,
    efektif_yagis,
    ek1_html,
    ek1_verisi,
    geri_odeme,
    tarife_bul,
    tasarruf,
)
from src.model import OneriHatasi, oner  # noqa: E402
from src.uydu import bolge_uydu_analizi, izmir_ilce_haritasi  # noqa: E402
from src.veri import iklim_al  # noqa: E402
from src.veri.iklim import ONBELLEK  # noqa: E402
from src.veri.konum import il_sirali, konum_bul  # noqa: E402
from src.veri.projeksiyon import (  # noqa: E402
    GELECEK,
    TABAN,
    degisim_oranlari,
    gelecek_iklimi,
    model_gunluk,
)

IL_KURUM = {"Ankara": "ASKİ", "İzmir": "İZSU", "İstanbul": "İSKİ"}
DONEM_YIL = {"10y": (2015, 2024), "5y": (2020, 2024), "30y": (1991, 2020)}
AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
UYDU_ATIF = (
    "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021, 2023) processed by "
    "ESA WorldCover consortium · İlçe sınırları © OpenStreetMap katkıcıları (ODbL) · "
    "Tüketim: İZSU / İzmir BB Açık Veri Portalı (CC BY 4.0)"
)


@functools.lru_cache(maxsize=128)
def _konum_cache(il: str, ilce: str):
    return konum_bul(il, ilce or None)


@functools.lru_cache(maxsize=128)
def _iklim_cache(lat: float, lon: float, y1: int, y2: int):
    return iklim_al(lat, lon, y1, y2)


@functools.lru_cache(maxsize=32)
def _senaryo_cache(il: str):
    yer_ad, lat, lon = _konum_cache(il, "")
    gozlem = _iklim_cache(lat, lon, *TABAN)
    oranlar = degisim_oranlari(model_gunluk(lat, lon))
    gelecek = gelecek_iklimi(gozlem, oranlar)
    return yer_ad, lat, lon, gozlem, oranlar, gelecek


def _varsayilan_tarife(il: str) -> float:
    kurum = IL_KURUM.get(il)
    return tarife_bul(kurum)["tl_m3"] if kurum else 100.0


def api_meta() -> dict:
    """İller, tarifeler ve 135 tekil tür (+ 2 standart çim karışımı)."""
    cim_karisim = [
        {
            "tur": "Çim karışımı, serin iklim (Lolium/Poa/Festuca)",
            "turkce_ad": "Çim karışımı, serin iklim",
            "grup": "cim",
            "kc_max": 0.95,
            "golge_agaci": False,
            "ek1_kategori": "Çim",
            "bakanlik_rehberi": "",
        },
        {
            "tur": "Çim karışımı, kurağa dayanıklı 5'li (Cynodon/Zoysia katkılı)",
            "turkce_ad": "Çim karışımı, kurağa dayanıklı 5'li",
            "grup": "cim",
            "kc_max": 0.80,
            "golge_agaci": False,
            "ek1_kategori": "Çim",
            "bakanlik_rehberi": "",
        },
    ]
    return {
        "iller": il_sirali(),
        "il_kurum": IL_KURUM,
        "tarifeler": TARIFELER,
        "hane_m3_yil": HANE_M3_YIL,
        "aylar": AYLAR,
        "bitkiler": cim_karisim + bitki_katalogu(),
    }


def _bolge_listesi(satirlar: list[dict], onek: str) -> list[Bolge]:
    bolgeler = []
    for i, s in enumerate(satirlar, 1):
        alan = float(s.get("alan_m2") or 0)
        if alan <= 0:
            continue
        bolgeler.append(
            Bolge(
                ad=f"{onek}{i}. {s.get('ad') or s.get('tur')}",
                grup=s["grup"],
                kc_max=float(s["kc_max"]),
                alan_m2=alan,
                yontem=s.get("yontem", "yagmurlama"),
                kd=float(s.get("kd", 1.0)),
            )
        )
    return bolgeler


def api_park(govde: dict) -> dict:
    """Ana sayfa: mevcut ve önerilen peyzaj su & tasarruf hesabı."""
    il = (govde.get("il") or "Ankara").strip()
    ilce = (govde.get("ilce") or "").strip()
    donem = govde.get("donem") or "5y"
    y1, y2 = DONEM_YIL.get(donem, (2020, 2024))
    sezon = range(3, 12) if govde.get("sezon_mart_kasim", True) else None
    toplam_alan = float(govde.get("toplam_alan") or 0)
    tarife = float(govde.get("tarife") if govde.get("tarife") is not None else _varsayilan_tarife(il))
    hane = float(govde.get("hane") or HANE_M3_YIL)

    mevcut_b = _bolge_listesi(govde.get("mevcut") or [], "M")
    oneri_b = _bolge_listesi(govde.get("oneri") or [], "Ö")
    if not mevcut_b or not oneri_b:
        raise ValueError("Her iki peyzaj tablosunda da en az bir bitki ve pozitif alan olmalı.")

    uyarilar = []
    hatalar = []
    for ad, bl in (("Mevcut", mevcut_b), ("Önerilen", oneri_b)):
        sulanan = sum(b.alan_m2 for b in bl)
        if toplam_alan > 0 and sulanan > toplam_alan:
            hatalar.append(
                f"{ad} peyzajda sulanan alan ({round(sulanan):,} m²) parkın toplam alanını "
                f"({round(toplam_alan):,} m²) aşıyor.".replace(",", ".")
            )
    if hatalar:
        raise ValueError(" ".join(hatalar))

    if any(b.grup == "cayir_yonca" and b.kc_max >= 0.9 for b in oneri_b):
        uyarilar.append(
            "Önerilen peyzajda yonca/çayır türleri var. Konca vd. (2026) bu türlerin çimden "
            "fazla su isteyebildiğini gösteriyor; çim alternatifi olarak önerilmez."
        )

    yer_ad, lat, lon = _konum_cache(il, ilce)
    ik = _iklim_cache(lat, lon, y1, y2)
    m = alan_ihtiyaci(ik, mevcut_b, sezon)
    o = alan_ihtiyaci(ik, oneri_b, sezon)
    t = tasarruf(m["m3_yil"], o["m3_yil"], tarife, hane)
    bel = belirsizlik_araligi(ik, mevcut_b, oneri_b, sezon)

    donusen_alan = donusen_alan_m2(govde.get("mevcut") or [], govde.get("oneri") or [])
    birim_maliyet = float(govde.get("birim_maliyet_tl_m2") or 0)
    roi = geri_odeme(donusen_alan, birim_maliyet, t["tasarruf_tl"] or 0.0) if birim_maliyet > 0 else None

    bolge_tablosu = []
    for ad, sonuc, bl in (("Mevcut", m, mevcut_b), ("Önerilen", o, oneri_b)):
        for b in bl:
            s = sonuc["bolgeler"][b.ad]
            isim = b.ad.split(". ", 1)[1] if ". " in b.ad else b.ad
            bolge_tablosu.append({
                "peyzaj": ad,
                "bolge": isim,
                "grup": b.grup,
                "kc": b.kc_max,
                "yontem": b.yontem,
                "kd": b.kd,
                "alan_m2": round(b.alan_m2),
                "l_m2_yil": round(s["mm_yil"]),
                "m3_yil": round(s["m3_yil"]),
            })

    return {
        "yer": {"ad": yer_ad, "lat": lat, "lon": lon, "y1": y1, "y2": y2},
        "tarife_tl_m3": tarife,
        "ozet": t,
        "belirsizlik": bel,
        "roi": roi,
        "aylik": {
            "aylar": AYLAR,
            "mevcut_m3": [round(v, 1) for v in m["m3_ay"]],
            "oneri_m3": [round(v, 1) for v in o["m3_ay"]],
            "et0_mm": [round(d["et0"], 1) for d in ik],
            "peff_mm": [round(efektif_yagis(d["yagis"]), 1) for d in ik],
        },
        "bolgeler": bolge_tablosu,
        "uyarilar": uyarilar,
    }


def api_ek1_html(govde: dict) -> str:
    """CB Kararı 10502 EK-1 Peyzaj İzleme Formu (yazdırılabilir HTML)."""
    park = api_park(govde)
    idare = (govde.get("idare_adi") or f"{govde.get('il') or 'Belediye'} Park ve Bahçeler Müdürlüğü").strip()
    yer = park["yer"]
    adres = f"{yer['ad']} ({yer['lat']:.2f}, {yer['lon']:.2f})"
    v = ek1_verisi(
        idare_adi=idare,
        adres=adres,
        toplam_alan_m2=float(govde.get("toplam_alan") or 0),
        mevcut_satirlar=govde.get("mevcut") or [],
        oneri_satirlar=govde.get("oneri") or [],
        tasarruf_sonuc=park["ozet"],
        tarife_tl_m3=park["tarife_tl_m3"],  # api_park ile aynı tarife (boşsa il varsayılanı)
        belirsizlik=park["belirsizlik"],
        iklim_notu=f"Open-Meteo/ERA5 {yer['y1']}–{yer['y2']}",
    )
    return ek1_html(v)


def api_oneri(govde: dict) -> dict:
    """Bitki karışımı MILP önerisi."""
    il = (govde.get("il") or "Ankara").strip()
    alan = float(govde.get("alan_m2") or 10_000)
    zorunlu = float(govde.get("zorunlu_cim_m2") or 0)
    cim_kc = float(govde.get("cim_kc") or 0.95)
    min_agac = float(govde.get("min_agac_pay") if govde.get("min_agac_pay") is not None else 0.25)
    min_cali = float(govde.get("min_cali_pay") if govde.get("min_cali_pay") is not None else 0.20)
    max_pay = float(govde.get("max_tur_pay") if govde.get("max_tur_pay") is not None else 0.20)
    min_say = int(govde.get("min_tur_sayisi") if govde.get("min_tur_sayisi") is not None else 6)
    haric = list(govde.get("haric") or [])
    tarife = float(govde.get("tarife") if govde.get("tarife") is not None else _varsayilan_tarife(il))

    yer_ad, lat, lon = _konum_cache(il, "")
    ik = _iklim_cache(lat, lon, 2020, 2024)
    r = oner(
        ik,
        alan,
        zorunlu_cim_m2=zorunlu,
        cim_kc=cim_kc,
        min_agac_pay=min_agac,
        min_cali_pay=min_cali,
        max_tur_pay=max_pay,
        min_tur_sayisi=min_say,
        haric=haric,
    )
    mevcut_m3 = bolge_ihtiyaci(ik, Bolge("çim", "cim", 0.95, alan), sezon=range(3, 12))["m3_yil"]
    t = tasarruf(mevcut_m3, r["m3_yil"], tarife, HANE_M3_YIL)
    return {
        "yer": {"ad": yer_ad, "lat": lat, "lon": lon},
        "ozet": t,
        "secim": r["secim"],
        "alan_m2": r["alan_m2"],
        "tarife": tarife,
        "ankara_uyari": il != "Ankara",
    }


def api_uydu() -> dict:
    """İzmir 11 merkez ilçe uydu sulanan yeşil ve İZSU fatura verisi."""
    yol = KOK / "kaynaklar" / "veri" / "uydu_izmir_ilce_2023.csv"
    ilceler = []
    with open(yol, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ilceler.append({
                "ilce": r["ilce"],
                "kapsama": float(r["kapsama_%"]),
                "kentsel_m2": int(r["kentsel_m2"]),
                "sulanan_yesil_m2": int(r["sulanan_yesil_m2"]),
                "kuru_cim_m2": int(r["kuru_cim_m2"]),
                "agac_m2": int(r["agac_m2"]),
                "izsu_2023_m3": int(r["izsu_2023_m3"]),
            })
    rho, p = spearmanr([x["sulanan_yesil_m2"] for x in ilceler], [x["izsu_2023_m3"] for x in ilceler])
    ik = _iklim_cache(38.41, 27.14, 2020, 2024)
    cim_mm = bolge_ihtiyaci(ik, Bolge("cim", "cim", 0.95, 1, yontem="yagmurlama"), sezon=range(3, 12))["mm_yil"]
    kurak_mm = bolge_ihtiyaci(ik, Bolge("kurak", "cali_otsu", 0.50, 1, yontem="damla"), sezon=range(3, 12))["mm_yil"]
    toplam_m2 = sum(x["sulanan_yesil_m2"] for x in ilceler)
    toplam_izsu = sum(x["izsu_2023_m3"] for x in ilceler)
    return {
        "ilceler": ilceler,
        "ozet": {
            "toplam_yesil_m2": toplam_m2,
            "toplam_izsu_m3": toplam_izsu,
            "hesaplanan_su_m3": round(toplam_m2 * cim_mm / 1000),
            "spearman_rho": round(float(rho), 3),
            "spearman_p": round(float(p), 4),
            "kismi_rho": 0.70,
            "cim_l_m2": round(cim_mm, 1),
            "kurak_l_m2": round(kurak_mm, 1),
            "izsu_tarife": tarife_bul("İZSU")["tl_m3"],
            "hane_m3_yil": HANE_M3_YIL,
        },
        "harita_url": "/assets/uydu_izmir_harita.png",
        "atif": UYDU_ATIF,
    }


def api_uydu_bolge(il: str, ilce: str = "", yaricap_km: float = 4.0) -> dict:
    """Herhangi bir il/ilçe için canlı uydu sulanan yeşil analizi + o ilin ERA5 iklim hesabı."""
    il = (il or "Ankara").strip()
    ilce = (ilce or "").strip()
    yaricap_km = max(2.0, min(6.0, float(yaricap_km)))

    yer_ad, lat, lon = _konum_cache(il, ilce)
    sonuc = bolge_uydu_analizi(yer_ad, lat, lon, yaricap_km=yaricap_km)
    ik = _iklim_cache(lat, lon, 2020, 2024)
    cim_mm = bolge_ihtiyaci(ik, Bolge("cim", "cim", 0.95, 1, yontem="yagmurlama"), sezon=range(3, 12))["mm_yil"]
    kurak_mm = bolge_ihtiyaci(ik, Bolge("kurak", "cali_otsu", 0.50, 1, yontem="damla"), sezon=range(3, 12))["mm_yil"]
    yaz_yagis = float(ik[6]["yagis"] + ik[7]["yagis"])  # Temmuz + Ağustos ort. toplamı

    yaz_uyari = None
    if yaz_yagis >= 60.0:
        yaz_uyari = (
            f"Dikkat: {yer_ad} Temmuz–Ağustos ortalama yağışı {round(yaz_yagis)} mm. "
            "Yazı yağışlı bölgelerde sulanmayan doğal otlar da Ağustos'ta yeşil (NDVI > 0,5) kalabileceğinden "
            "tespit edilen alan gerçek sulanan yeşilin üstünde çıkabilir."
        )

    return {
        "yer": {"ad": yer_ad, "il": il, "ilce": ilce, "lat": float(lat), "lon": float(lon)},
        "analiz": sonuc,
        "ozet": {
            "sulanan_yesil_m2": int(sonuc["sulanan_yesil_m2"]),
            "kentsel_m2": int(sonuc["kentsel_m2"]),
            "kuru_cim_m2": int(sonuc["kuru_cim_m2"]),
            "agac_m2": int(sonuc["agac_m2"]),
            "hesaplanan_su_m3": int(round(sonuc["sulanan_yesil_m2"] * cim_mm / 1000.0)),
            "cim_l_m2": round(float(cim_mm), 1),
            "kurak_l_m2": round(float(kurak_mm), 1),
            "yaz_yagis_mm": round(yaz_yagis, 1),
            "varsayilan_tarife": float(_varsayilan_tarife(il)),
            "hane_m3_yil": HANE_M3_YIL,
        },
        "harita_url": f"/assets/uydu_cache/{sonuc['harita_dosya']}",
        "yaz_yagis_uyari": yaz_uyari,
        "atif": (
            "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021, 2023) processed by "
            "ESA WorldCover consortium · İklim: Open-Meteo / ERA5."
        ),
    }


def api_senaryo2040(il: str) -> dict:
    """7 CMIP6 modeli ile 2041–2050 su ihtiyacı senaryosu."""
    import numpy as np

    yer_ad, lat, lon, gozlem, oranlar, gelecek = _senaryo_cache(il)
    sezon = range(3, 12)
    cim = Bolge("çim", "cim", 0.95, 1)
    kurak = Bolge("kurakçıl", "cali_otsu", 0.50, 1, yontem="damla")
    cim_bugun = bolge_ihtiyaci(gozlem, cim, sezon)
    kur_bugun = bolge_ihtiyaci(gozlem, kurak, sezon)
    cim_m = {m: bolge_ihtiyaci(k, cim, sezon) for m, k in gelecek.items()}
    kur_m = {m: bolge_ihtiyaci(k, kurak, sezon) for m, k in gelecek.items()}

    cim_gel = float(np.median([v["mm_yil"] for v in cim_m.values()]))
    kur_gel = float(np.median([v["mm_yil"] for v in kur_m.values()]))
    artis_cim = cim_gel - cim_bugun["mm_yil"]
    artis_kur = kur_gel - kur_bugun["mm_yil"]

    aylik = []
    for i in range(2, 11):  # Mart–Kasım
        cv = [v["mm"][i] for v in cim_m.values()]
        kv = [v["mm"][i] for v in kur_m.values()]
        aylik.append({
            "ay": AYLAR[i],
            "cim_bugun": round(cim_bugun["mm"][i], 1),
            "cim_medyan": round(float(np.median(cv)), 1),
            "cim_min": round(float(min(cv)), 1),
            "cim_max": round(float(max(cv)), 1),
            "kurak_bugun": round(kur_bugun["mm"][i], 1),
            "kurak_medyan": round(float(np.median(kv)), 1),
            "kurak_min": round(float(min(kv)), 1),
            "kurak_max": round(float(max(kv)), 1),
        })

    modeller = [
        {
            "model": m,
            "et0_degisim_yuzde": round(float(o["et0_yil_%"]), 1),
            "yagis_degisim_yuzde": round(float(o["yagis_yil_%"]), 1),
            "cim_2040": int(round(float(cim_m[m]["mm_yil"]))),
            "kurak_2040": int(round(float(kur_m[m]["mm_yil"]))),
        }
        for m, o in oranlar.items()
    ]
    return {
        "yer": {"ad": yer_ad, "lat": float(lat), "lon": float(lon)},
        "taban": list(TABAN),
        "gelecek": list(GELECEK),
        "varsayilan_tarife": float(_varsayilan_tarife(il)),
        "ozet": {
            "cim_bugun_l": round(float(cim_bugun["mm_yil"]), 1),
            "cim_2040_l": round(float(cim_gel), 1),
            "cim_artis_l": round(float(artis_cim), 1),
            "cim_artis_yuzde": round(float(100 * artis_cim / cim_bugun["mm_yil"]), 1),
            "kurak_bugun_l": round(float(kur_bugun["mm_yil"]), 1),
            "kurak_2040_l": round(float(kur_gel), 1),
            "kurak_artis_l": round(float(artis_kur), 1),
            "kat_fark": round(float(artis_cim / artis_kur), 1) if artis_kur > 0 else None,
            "artis_model_sayisi": int(sum(bool(o["et0_yil_%"] > 0) for o in oranlar.values())),
            "toplam_model": int(len(oranlar)),
        },
        "aylik": aylik,
        "modeller": modeller,
    }


class Isleyici(BaseHTTPRequestHandler):
    def _json(self, veri: dict, durum: int = HTTPStatus.OK):
        ham = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(durum)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(ham)))
        self.end_headers()
        self.wfile.write(ham)

    def _dosya(self, yol: Path):
        if not yol.exists() or not yol.is_file():
            self._json({"hata": "Dosya bulunamadı"}, HTTPStatus.NOT_FOUND)
            return
        tip, _ = mimetypes.guess_type(str(yol))
        ham = yol.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", (tip or "application/octet-stream") + ("; charset=utf-8" if (tip or "").startswith("text/") or tip == "application/javascript" else ""))
        self.send_header("Content-Length", str(len(ham)))
        self.end_headers()
        self.wfile.write(ham)

    def do_GET(self):
        u = urlparse(self.path)
        try:
            if u.path in ("/", "/index.html"):
                self._dosya(WEB / "index.html")
            elif u.path in ("/style.css", "/app.js"):
                self._dosya(WEB / u.path.lstrip("/"))
            elif u.path == "/assets/uydu_izmir_harita.png":
                self._dosya(KOK / "prototip" / "cikti" / "uydu_izmir_harita.png")
            elif u.path == "/assets/uydu_izmir_ilce.png":
                qs = parse_qs(u.query)
                ilce = qs.get("ilce", [""])[0]
                self._dosya(izmir_ilce_haritasi(ilce))
            elif u.path.startswith("/assets/uydu_cache/"):
                dosya = u.path.split("/assets/uydu_cache/", 1)[1]
                if Path(dosya).name != dosya or not (dosya.startswith("uydu_") and dosya.endswith(".png")):
                    self._json({"hata": "Geçersiz dosya adı"}, HTTPStatus.BAD_REQUEST)
                else:
                    self._dosya(ONBELLEK / dosya)
            elif u.path == "/api/meta":
                self._json(api_meta())
            elif u.path == "/api/uydu":
                self._json(api_uydu())
            elif u.path == "/api/uydu_bolge":
                qs = parse_qs(u.query)
                il = qs.get("il", ["Ankara"])[0]
                ilce = qs.get("ilce", [""])[0]
                yaricap = float(qs.get("yaricap", ["4"])[0])
                self._json(api_uydu_bolge(il, ilce, yaricap))
            elif u.path == "/api/senaryo2040":
                qs = parse_qs(u.query)
                il = qs.get("il", ["Ankara"])[0]
                self._json(api_senaryo2040(il))
            else:
                self._json({"hata": "Bilinmeyen yol"}, HTTPStatus.NOT_FOUND)
        except Exception as e:
            self._json({"hata": str(e)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            uzunluk = int(self.headers.get("Content-Length", "0"))
            govde = json.loads(self.rfile.read(uzunluk).decode("utf-8")) if uzunluk else {}
            if u.path == "/api/park":
                self._json(api_park(govde))
            elif u.path == "/api/oneri":
                self._json(api_oneri(govde))
            elif u.path == "/api/ek1_html":
                ham = api_ek1_html(govde).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(ham)))
                self.end_headers()
                self.wfile.write(ham)
            else:
                self._json({"hata": "Bilinmeyen yol"}, HTTPStatus.NOT_FOUND)
        except (ValueError, LookupError, OneriHatasi) as e:
            self._json({"hata": str(e)}, HTTPStatus.BAD_REQUEST)
        except Exception as e:
            self._json({"hata": f"Sunucu hatası: {e}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[web] {self.address_string()} {fmt % args}\n")


def main():
    # Windows konsolu/kanalı cp1252 olabilir; Türkçe karakterler açılışta çökertmesin
    for akis in (sys.stdout, sys.stderr):
        if hasattr(akis, "reconfigure"):
            akis.reconfigure(encoding="utf-8", errors="replace")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    sunucu = ThreadingHTTPServer(("127.0.0.1", port), Isleyici)
    print(f"Florify Web Arayüzü çalışıyor: http://localhost:{port}")
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatıldı.")


if __name__ == "__main__":
    main()
