"""Öneri motoru testleri (ağ gerektirmez; sabit iklim)."""
import pytest

from src.model import OneriHatasi, cali_cicek, golge_agaci, oner, tur_tablosu

DUZ = [{"et0": 120.0, "yagis": 10.0} for _ in range(12)]


def test_alan_tam_dolar_ve_kisitlar_saglanir():
    r = oner(DUZ, 10_000, zorunlu_cim_m2=1500, min_agac_pay=0.2, max_tur_pay=0.25, min_tur_sayisi=5)
    assert sum(s["alan_m2"] for s in r["secim"]) == pytest.approx(10_000, rel=1e-6)
    zorunlu = [s for s in r["secim"] if s["tur"].startswith("Çim (zorunlu")]
    assert zorunlu and zorunlu[0]["alan_m2"] == pytest.approx(1500)
    golge = sum(s["alan_m2"] for s in r["secim"] if s["golge"])
    assert golge >= 0.2 * 10_000 - 1e-6
    assert not any(s["golge"] and s["tur"].startswith("Juniperus") for s in r["secim"])
    serbest = [s for s in r["secim"] if not s["tur"].startswith("Çim (zorunlu")]
    assert len(serbest) >= 5
    assert all(s["alan_m2"] <= 0.25 * 10_000 + 1e-6 for s in serbest)
    assert all(s["alan_m2"] >= 0.03 * 10_000 - 1e-6 for s in serbest)


def test_tamami_cimden_az_su():
    r = oner(DUZ, 5000)
    cim = oner(DUZ, 5000, zorunlu_cim_m2=5000, min_agac_pay=0, min_tur_sayisi=0)
    assert r["m3_yil"] < 0.5 * cim["m3_yil"]


def test_en_dusuk_kc_turleri_secilir():
    r = oner(DUZ, 1000, min_agac_pay=0, max_tur_pay=0.5, min_tur_sayisi=2)
    min_kc = min(t.kc for t in tur_tablosu() if t.yontem == "damla")
    assert all(s["kc"] == pytest.approx(min_kc) for s in r["secim"])


def test_haric_tutulan_tur_secilmez():
    ilk = oner(DUZ, 1000, min_agac_pay=0, max_tur_pay=0.5, min_tur_sayisi=2)
    cikar = [s["tur"] for s in ilk["secim"]]
    r = oner(DUZ, 1000, min_agac_pay=0, max_tur_pay=0.5, min_tur_sayisi=2, haric=cikar)
    assert not set(cikar) & {s["tur"] for s in r["secim"]}
    assert r["m3_yil"] >= ilk["m3_yil"]


def test_kurallar_yonca_ve_yapay_cim_yok():
    havuz = tur_tablosu()
    assert not any(t.grup == "cayir_yonca" and t.kc >= 0.9 for t in havuz)
    assert not any("yapay" in t.ad.lower() for t in havuz)


def test_saglanamayan_kisitlar_hata_verir():
    with pytest.raises(OneriHatasi):
        oner(DUZ, 1000, max_tur_pay=0.1, min_tur_sayisi=2, min_tur_pay=0.6)   # 2×0,6 > 1
    with pytest.raises(OneriHatasi):
        oner(DUZ, 1000, zorunlu_cim_m2=2000)
    with pytest.raises(OneriHatasi):
        oner(DUZ, 0)


def test_ayni_tur_iki_kez_secilmez():
    r = oner(DUZ, 10_000, zorunlu_cim_m2=1000, min_agac_pay=0.1, max_tur_pay=0.10, min_tur_sayisi=15)
    turler = [s["tur"] for s in r["secim"]]
    assert len(turler) == len(set(turler))
    assert len([t for t in turler if not t.startswith("Çim (zorunlu")]) >= 15


def test_calilar_golge_agaci_sayilmaz():
    havuz = {t.ad: t for t in tur_tablosu()}
    for cali in ("Cotinus coggygria", "Robinia hispida", "Hibiscus syriacus",
                 "Photinia fraseri", "Pinus mugo", "Juniperus horizontalis"):
        assert not golge_agaci(havuz[cali]), f"{cali} gölge ağacı sayılmamalı"
    for agac in ("Elaeagnus angustifolia", "Acer campestre", "Pinus nigra", "Quercus pubescens"):
        assert golge_agaci(havuz[agac]), f"{agac} gölge ağacı olmalı"


def test_cali_katmani_kisiti_saglanir():
    r = oner(DUZ, 10_000, zorunlu_cim_m2=2000, min_agac_pay=0.25, min_cali_pay=0.25,
             max_tur_pay=0.20, min_tur_sayisi=6)
    havuz = {t.ad: t for t in tur_tablosu()}
    cali_alan = sum(s["alan_m2"] for s in r["secim"] if s["tur"] in havuz and cali_cicek(havuz[s["tur"]]))
    assert cali_alan >= 0.25 * 10_000 - 1e-6
