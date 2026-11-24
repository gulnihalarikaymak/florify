"""Doğrulanmış peyzaj suyu tarifeleri (TL/m³, KDV hariç).

Her satır resmi kaynaktan tek tek kontrol edildi (bkz. kaynaklar/arastirma/…2026-11-24.md).
Tarifeler ay ay değişebildiği için 'gecerlilik' alanı tutulur; hesapta tarih seçilmelidir.
"""
TARIFELER = [
    {"kurum": "İSKİ", "kategori": "Yeşil alanları sulama", "tl_m3": 85.78,
     "gecerlilik": "2025", "kaynak": "İSKİ 2025 su satış tarifeleri PDF"},
    {"kurum": "ASKİ", "kategori": "Resmi kurum park ve bahçe", "tl_m3": 165.95,
     "gecerlilik": "2026-03", "kaynak": "ASKİ 2026 tarife PDF"},
    {"kurum": "ASKİ", "kategori": "Resmi kurum park ve bahçe", "tl_m3": 192.95,
     "gecerlilik": "2026-10", "kaynak": "ASKİ 2026 tarife PDF"},
    {"kurum": "ASKİ", "kategori": "Resmi kurum park ve bahçe", "tl_m3": 197.04,
     "gecerlilik": "2026-11", "kaynak": "ASKİ 2026 tarife PDF"},
    {"kurum": "ASKİ", "kategori": "AAT geri kazanım suyu", "tl_m3": 17.72,
     "gecerlilik": "2026-10", "kaynak": "ASKİ 2026 tarife PDF"},
    {"kurum": "İZSU", "kategori": "Park ve mezarlık aboneleri", "tl_m3": 71.83,
     "gecerlilik": "2026-06", "kaynak": "izsu.gov.tr tarife sayfası (01.06.2026'dan itibaren)"},
    {"kurum": "İZSU", "kategori": "Geri kazanım suyu, kamu park ve mezarlık", "tl_m3": 8.96,
     "gecerlilik": "2026-06", "kaynak": "izsu.gov.tr tarife sayfası (01.06.2026'dan itibaren)"},
]


def tarife_bul(kurum, geri_kazanim=False):
    """Kurumun en güncel park suyu (veya geri kazanım suyu) tarifesi."""
    adaylar = [t for t in TARIFELER if t["kurum"] == kurum
               and ("geri kazanım" in t["kategori"].lower()) == geri_kazanim]
    if not adaylar:
        raise KeyError(f"{kurum} için {'geri kazanım ' if geri_kazanim else ''}tarife yok")
    return max(adaylar, key=lambda t: t["gecerlilik"])
