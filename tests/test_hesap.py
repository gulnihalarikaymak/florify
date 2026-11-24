"""Hesap çekirdeği birim testleri (ağ gerektirmez)."""
import pytest

from src.hesap import (Bolge, RANDIMAN, alan_ihtiyaci, belirsizlik_araligi, bitki_bilgi, bitki_katalogu,
                       bitki_kc, bolge_ihtiyaci, efektif_yagis, ek1_html, ek1_verisi, geri_odeme,
                       kc_aylik, tarife_bul, tasarruf)
from src.hesap.fao56 import VERI, _kc_ciftleri

# Sabit, elle hesaplanabilir bir iklim: her ay ET0 100 mm, yağış 0
DUZ = [{"et0": 100.0, "yagis": 0.0} for _ in range(12)]


def test_efektif_yagis_usda_scs():
    assert efektif_yagis(0) == 0
    assert efektif_yagis(100) == pytest.approx(84.0)          # 100·(125−20)/125
    assert efektif_yagis(250) == pytest.approx(150.0)         # eşik
    assert efektif_yagis(300) == pytest.approx(155.0)         # 125 + 0,1·300
    assert efektif_yagis(-5) == 0


def test_ihtiyac_yagis_fazlaysa_sifir_negatif_olmaz():
    yagisli = [{"et0": 20.0, "yagis": 200.0} for _ in range(12)]
    r = bolge_ihtiyaci(yagisli, Bolge("x", "cim", 1.0, 1000), profil=False)
    assert r["mm_yil"] == 0


def test_brut_net_randiman_ve_m3():
    b = Bolge("çim", "cim", 1.0, 2000, yontem="yagmurlama")
    r = bolge_ihtiyaci(DUZ, b, profil=False)
    assert r["mm"][0] == pytest.approx(100 / 0.70)
    assert r["m3"][0] == pytest.approx(100 / 0.70 * 2000 / 1000)
    assert r["mm_yil"] == pytest.approx(12 * 100 / 0.70)


def test_damla_yagmurlamadan_az_ister():
    yag = bolge_ihtiyaci(DUZ, Bolge("a", "cali_otsu", 0.5, 1, yontem="yagmurlama"))
    dam = bolge_ihtiyaci(DUZ, Bolge("a", "cali_otsu", 0.5, 1, yontem="damla"))
    assert dam["mm_yil"] / yag["mm_yil"] == pytest.approx(RANDIMAN["yagmurlama"] / RANDIMAN["damla"])


def test_sezon_disi_aylar_sifir():
    r = bolge_ihtiyaci(DUZ, Bolge("x", "cim", 1.0, 1), sezon=range(3, 12), profil=False)
    assert r["mm"][0] == r["mm"][1] == r["mm"][11] == 0
    assert all(v > 0 for v in r["mm"][2:11])


def test_kd_kmc_carpani():
    tam = bolge_ihtiyaci(DUZ, Bolge("x", "cali_otsu", 0.6, 1, yontem="damla"), profil=False)
    seyrek = bolge_ihtiyaci(DUZ, Bolge("x", "cali_otsu", 0.6, 1, yontem="damla", kd=0.5, kmc=0.8),
                            profil=False)
    assert seyrek["mm_yil"] == pytest.approx(tam["mm_yil"] * 0.4)


def test_aylik_profil_yazin_kc_max_kisin_dusuk():
    kc = kc_aylik("agac_cali", 0.8)
    assert kc[6] == pytest.approx(0.8)          # Temmuz = Kc_max
    assert kc[0] < kc[6] and kc[10] < kc[6]     # Ocak, Kasım düşük
    assert kc_aylik("cim", 0.95, profil=False) == [0.95] * 12
    with pytest.raises(ValueError):
        kc_aylik("kaktus", 0.2)


def test_bitki_kc_tablodan():
    assert bitki_kc("Lavandula angustifolia") == ("cali_otsu", 0.5)
    b = Bolge.turden("lavanta", "lavandula angustifolia", 300, yontem="damla")
    assert (b.grup, b.kc_max, b.alan_m2) == ("cali_otsu", 0.5, 300)
    with pytest.raises(KeyError):
        bitki_kc("Olmayan tür")


def test_alan_toplami_ve_sert_zemin_sulanmaz():
    # 1000 m² park: 600 çim + 200 çalı; 200 m² sert zemin bölge olarak verilmez
    bolgeler = [Bolge("çim", "cim", 0.95, 600), Bolge("çalı", "cali_otsu", 0.5, 200, yontem="damla")]
    r = alan_ihtiyaci(DUZ, bolgeler)
    assert r["alan_m2"] == 800
    assert r["m3_yil"] == pytest.approx(sum(s["m3_yil"] for s in r["bolgeler"].values()))


def test_gecersiz_girdiler():
    with pytest.raises(ValueError):
        Bolge("x", "cim", 1.0, 10, yontem="hortum")
    with pytest.raises(ValueError):
        Bolge("x", "cim", 1.0, -1)


def test_tasarruf_hesabi():
    t = tasarruf(1000, 400, tarife_tl_m3=50, hane_m3_yil=200)
    assert t["tasarruf_m3"] == 600
    assert t["tasarruf_yuzde"] == pytest.approx(60)
    assert t["tasarruf_tl"] == 30000
    assert t["hane_esdegeri"] == 3


def test_tarife_en_guncel_ve_geri_kazanim():
    assert tarife_bul("ASKİ")["tl_m3"] == 197.04
    assert tarife_bul("İZSU", geri_kazanim=True)["tl_m3"] == 8.96
    with pytest.raises(KeyError):
        tarife_bul("BUSKİ")


def test_bitki_ozellikleri_tam_kapsama_ve_tekillik():
    import csv
    with open(VERI / "konca2026_ankara_kc_tablosu.csv", encoding="utf-8") as f:
        turler = {r["tur"] for r in csv.DictReader(f)}
    katalog = bitki_katalogu()
    assert len(katalog) == len(turler)
    assert len({r["tur"].lower() for r in katalog}) == len(katalog)
    ciftler = _kc_ciftleri()
    for tur in turler:
        b = bitki_bilgi(tur)
        assert b["turkce_ad"]
        assert b["ek1_kategori"]
        assert b["bakanlik_rehberi"] in ("", "ulke_geneli", "trakya_akdeniz", "ulke_geneli+trakya_akdeniz")
        assert (tur.lower(), b["birincil_grup"]) in ciftler


def test_tekrarli_tur_birincil_grupla_cozulur():
    assert bitki_kc("Stipa tenuissima") == ("yer_ortucu", 0.4)
    assert bitki_kc("Stipa tenuissima", grup="cali_otsu") == ("cali_otsu", 0.6)
    assert bitki_kc("Juniperus horizontalis") == ("cali_otsu", 0.5)


def test_belirsizlik_p10_p50_p90_sirali():
    m = [Bolge("çim", "cim", 0.95, 6000, yontem="yagmurlama")]
    o = [Bolge("lavanta", "cali_otsu", 0.50, 6000, yontem="damla")]
    b = belirsizlik_araligi(DUZ, m, o, n=500, tohum=7)
    for k in ("mevcut_m3", "oneri_m3", "tasarruf_m3"):
        assert b[k]["p10"] < b[k]["p50"] < b[k]["p90"]
    assert b["tasarruf_m3"]["p10"] > 0


def test_geri_odeme_hesabi():
    r = geri_odeme(4000, 500, 500_000)
    assert r["yatirim_tl"] == 2_000_000
    assert r["geri_odeme_yil"] == pytest.approx(4.0)
    assert geri_odeme(4000, 0, 500_000)["geri_odeme_yil"] is None


def test_ek1_formu_turkce_ve_latince_kategoriler():
    mev = [{"tur": "Çim karışımı, serin iklim", "grup": "cim", "alan_m2": 6000, "yontem": "yagmurlama"}]
    one = [
        {"tur": "Çim karışımı, serin iklim", "grup": "cim", "alan_m2": 2000, "yontem": "yagmurlama"},
        {"tur": "Lavandula angustifolia", "grup": "cali_otsu", "alan_m2": 2500, "yontem": "damla"},
        {"tur": "Elaeagnus angustifolia", "grup": "agac_cali", "alan_m2": 1500, "yontem": "damla"},
    ]
    t = tasarruf(8000, 3500, tarife_tl_m3=197.04)
    v = ek1_verisi("Çankaya Belediyesi", "Ankara", 10_000, mev, one, t, 197.04)
    assert v["donusen_alan_m2"] == 4000
    # 3–17. maddeler mevcut peyzajı anlatır: mevcutta kurakçıl yok, 6000 m² çim
    assert v["kurakcil_alan_m2"] == 0
    assert v["cim_alan_m2"] == 6000
    assert v["yillik_su_bedeli_tl"] == round(8000 * 197.04)
    # Önerilen türler yalnız planlanan (22. madde) dökümünde
    assert v["plan_kurakcil_m2"] == 4000
    assert any("Lavandula angustifolia" in x for x in v["plan_kategoriler"]["Çalılar"])
    assert any("Elaeagnus angustifolia" in x for x in v["plan_kategoriler"]["Ağaçlar"])
    assert not v["kategoriler"]["Çalılar"]
    html = ek1_html(v)
    assert "PEYZAJ İZLEME FORMU" in html
    assert "Çankaya Belediyesi" in html
    assert "Lavandula angustifolia" in html


def test_ek1_tum_katalog_kategorileri_esleniyor():
    """Katalogdaki her tür EK-1'in bir kategorisine (ya da çim/çayır) düşer; sessiz 'Çalılar' yok."""
    from src.hesap.ek1 import EK1_KATEGORILER, satir_sinifi
    for b in bitki_katalogu():
        sinif, _ = satir_sinifi({"tur": b["tur"], "grup": b["grup"], "alan_m2": 1})
        assert sinif in ("cim", "cayir") or sinif in EK1_KATEGORILER, b["tur"]
        if b["ek1_kategori"] == "Çayır":
            assert sinif == "cayir", b["tur"]


def test_ek1_cayir_kurakcil_sayilmaz_ve_donusen_alana_girer():
    mev = [{"tur": "Medicago sativa", "grup": "cayir_yonca", "alan_m2": 5000, "yontem": "yagmurlama"}]
    one = [{"tur": "Lavandula angustifolia", "grup": "cali_otsu", "alan_m2": 5000, "yontem": "damla"}]
    t = tasarruf(6000, 2000, tarife_tl_m3=50)
    v = ek1_verisi("X", "Y", 0, mev, one, t, 50)
    assert v["donusen_alan_m2"] == 5000
    assert v["kurakcil_alan_m2"] == 0
    assert v["cayir_alan_m2"] == 5000
    assert all("Medicago" not in x for liste in v["kategoriler"].values() for x in liste)
    assert any("Medicago sativa" in x for x in v["cayir_turleri"])
    # Yonca önerilirse de kurakçıl sayılmaz, dönüşen alanı azaltır
    one2 = one + [{"tur": "Trifolium repens", "grup": "cayir_yonca", "alan_m2": 1000, "yontem": "yagmurlama"}]
    v2 = ek1_verisi("X", "Y", 0, mev, one2, t, 50)
    assert v2["donusen_alan_m2"] == 4000
    assert not v2["plan_kategoriler"]["Yer örtücüler"]
