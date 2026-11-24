"""İl/ilçe adından koordinat: Open-Meteo Geocoding API (GeoNames tabanlı, açık). Önbellekli."""
import json

import requests

from .iklim import ONBELLEK

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Plaka sırasıyla 81 il
ILLER = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın",
    "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı",
    "Çorum", "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir",
    "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir",
    "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya",
    "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya",
    "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak",
    "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak",
    "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce",
]
# İl adıyla aynı adı taşımayan il merkezleri
MERKEZ = {"Kocaeli": "İzmit", "Sakarya": "Adapazarı", "Hatay": "Antakya"}

_TR = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")


def _sade(s):
    """Karşılaştırma için: Türkçe harfleri sadeleştir, sondaki 'İli' ekini at ("Bursa İli" = "Bursa")."""
    s = s.translate(_TR).lower().strip()
    return s[:-4] if s.endswith(" ili") else s


def il_sirali():
    sira = "abcçdefgğhıijklmnoöprsştuüvyz"
    return sorted(ILLER, key=lambda s: [sira.index(c) if c in sira else 99
                                        for c in s.replace("I", "ı").replace("İ", "i").lower()])


def konum_bul(il, ilce=None):
    """(ad, lat, lon). İlçe verilirse önce onu, aynı il içinde arar."""
    ONBELLEK.mkdir(exist_ok=True)
    yol = ONBELLEK / "konumlar.json"
    tablo = json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else {}
    anahtar = f"{il}|{ilce or ''}"
    if anahtar in tablo:
        return tuple(tablo[anahtar])

    aranan = ilce or MERKEZ.get(il, il)
    r = requests.get(GEO_URL, params={"name": aranan, "count": 20, "language": "tr",
                                      "countryCode": "TR"}, timeout=30)
    r.raise_for_status()
    sonuclar = r.json().get("results", [])
    ayni_il = [s for s in sonuclar if _sade(s.get("admin1", "")) == _sade(il)]
    if not ayni_il:
        raise LookupError(f"Bulunamadı: {aranan} ({il})")
    if ilce:
        secim = max(ayni_il, key=lambda s: s.get("population") or 0)
    else:
        merkezler = [s for s in ayni_il if s.get("feature_code") in ("PPLA", "PPLC")]
        secim = (merkezler or sorted(ayni_il, key=lambda s: -(s.get("population") or 0)))[0]
    ad = il if _sade(secim["name"]) == _sade(il) else f"{secim['name']}, {il}"
    sonuc = (ad, round(secim["latitude"], 4), round(secim["longitude"], 4))
    tablo[anahtar] = sonuc
    yol.write_text(json.dumps(tablo, ensure_ascii=False, indent=1), encoding="utf-8")
    return sonuc
