"""Web API uç nokta testleri (web/sunucu.py)."""
import pytest

from web.sunucu import api_ek1_html, api_meta, api_oneri, api_park, api_senaryo2040, api_uydu


def test_api_meta_tam():
    m = api_meta()
    assert len(m["iller"]) == 81
    assert len(m["bitkiler"]) == 137  # 2 çim karışımı + 135 tekil tür
    assert len(m["tarifeler"]) >= 5


def test_api_park_alan_asimi_hata_verir():
    with pytest.raises(ValueError, match="aşıyor"):
        api_park({
            "il": "Ankara",
            "toplam_alan": 1000,
            "mevcut": [{"tur": "çim", "grup": "cim", "kc_max": 0.95, "alan_m2": 1500, "yontem": "yagmurlama"}],
            "oneri": [{"tur": "lavanta", "grup": "cali_otsu", "kc_max": 0.50, "alan_m2": 500, "yontem": "damla"}],
        })


@pytest.mark.ag
def test_api_park_ve_oneri_ankara():
    govde = {
        "il": "Ankara",
        "idare_adi": "Çankaya Belediyesi",
        "donem": "10y",
        "toplam_alan": 10_000,
        "birim_maliyet_tl_m2": 500,
        "mevcut": [{"tur": "çim", "grup": "cim", "kc_max": 0.95, "alan_m2": 6000, "yontem": "yagmurlama"}],
        "oneri": [{"tur": "Lavandula angustifolia", "grup": "cali_otsu", "kc_max": 0.50, "alan_m2": 6000, "yontem": "damla"}],
    }
    p = api_park(govde)
    assert p["ozet"]["tasarruf_m3"] > 0
    assert len(p["aylik"]["mevcut_m3"]) == 12
    assert p["belirsizlik"]["tasarruf_m3"]["p10"] < p["belirsizlik"]["tasarruf_m3"]["p90"]
    assert p["roi"]["geri_odeme_yil"] > 0

    html = api_ek1_html(govde)
    assert "PEYZAJ İZLEME FORMU" in html
    assert "Çankaya Belediyesi" in html
    assert "Lavandula angustifolia" in html

    o = api_oneri({"il": "Ankara", "alan_m2": 10_000, "zorunlu_cim_m2": 2000})
    assert o["ozet"]["tasarruf_m3"] > 0
    assert len(o["secim"]) >= 6


@pytest.mark.ag
def test_api_uydu_ve_2040():
    import json

    u = api_uydu()
    assert len(u["ilceler"]) == 11
    assert u["ozet"]["spearman_rho"] > 0.8
    assert json.dumps(u)

    s = api_senaryo2040("Ankara")
    assert len(s["aylik"]) == 9
    assert s["ozet"]["toplam_model"] >= 5
    assert json.dumps(s)


@pytest.mark.ag
def test_api_ek1_tarifesiz_il_varsayilanini_kullanir_ve_yonca_donusur():
    govde = {
        "il": "Ankara",
        "birim_maliyet_tl_m2": 500,
        "mevcut": [{"tur": "Medicago sativa", "grup": "cayir_yonca", "kc_max": 1.0, "alan_m2": 1000, "yontem": "yagmurlama"}],
        "oneri": [{"tur": "Lavandula angustifolia", "grup": "cali_otsu", "kc_max": 0.50, "alan_m2": 1000, "yontem": "damla"}],
    }
    p = api_park(govde)  # tarife yok → ASKİ varsayılanı
    assert p["tarife_tl_m3"] > 0
    assert p["ozet"]["tasarruf_tl"] > 0
    assert p["roi"]["donusen_alan_m2"] == 1000  # yonca dönüşümü de sayılır
    html = api_ek1_html(govde)
    import re
    m17 = re.search(r'>17\.</td>.*?<td class="hesap">([\d.]+) TL/yıl.*?\(([\d.,]+) TL/m³', html, re.S)
    assert m17 and m17.group(1) != "0" and m17.group(2) != "0,00"
    assert "Çayır/yonca" in html
