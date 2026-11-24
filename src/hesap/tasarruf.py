"""Mevcut ve önerilen peyzajın karşılaştırması: m³, %, TL, hane eşdeğeri."""

# Konca vd. 2026, Bölüm 3.2: Ankara'da hane başına ortalama 15 m³/ay (TÜİK ve ABB verisi) → 180 m³/yıl
HANE_M3_YIL = 15 * 12


def tasarruf(mevcut_m3_yil, oneri_m3_yil, tarife_tl_m3=None, hane_m3_yil=HANE_M3_YIL):
    if mevcut_m3_yil < 0 or oneri_m3_yil < 0:
        raise ValueError("Su miktarı negatif olamaz")
    fark = mevcut_m3_yil - oneri_m3_yil
    return {
        "mevcut_m3": mevcut_m3_yil,
        "oneri_m3": oneri_m3_yil,
        "tasarruf_m3": fark,
        "tasarruf_yuzde": 100 * fark / mevcut_m3_yil if mevcut_m3_yil else 0.0,
        "tasarruf_tl": fark * tarife_tl_m3 if tarife_tl_m3 is not None else None,
        "hane_esdegeri": fark / hane_m3_yil,
    }


def geri_odeme(donusen_alan_m2, birim_maliyet_tl_m2, yillik_tasarruf_tl):
    """Tahmini kurulum maliyeti ve basit geri ödeme süresi (yıl).

    Not: Birim maliyet kullanıcı varsayımıdır; bakım/enerji tasarrufu dahil değildir (yalnız su faturası).
    """
    if donusen_alan_m2 < 0 or birim_maliyet_tl_m2 < 0:
        raise ValueError("Alan veya birim maliyet negatif olamaz")
    yatirim = float(donusen_alan_m2) * float(birim_maliyet_tl_m2)
    yil = (yatirim / yillik_tasarruf_tl) if (yatirim > 0 and yillik_tasarruf_tl and yillik_tasarruf_tl > 0) else None
    return {
        "donusen_alan_m2": float(donusen_alan_m2),
        "birim_maliyet_tl_m2": float(birim_maliyet_tl_m2),
        "yatirim_tl": round(yatirim, 2),
        "geri_odeme_yil": round(yil, 1) if yil is not None else None,
    }
