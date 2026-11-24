from src.veri.konum import ILLER, MERKEZ, _sade, il_sirali


def test_81_il_tekil():
    assert len(ILLER) == 81 == len(set(ILLER))
    assert set(MERKEZ) <= set(ILLER)


def test_turkce_siralama():
    s = il_sirali()
    assert s[:3] == ["Adana", "Adıyaman", "Afyonkarahisar"]
    assert s.index("Çanakkale") > s.index("Bursa")
    assert s.index("Iğdır") < s.index("İstanbul")
    assert s[-1] == "Zonguldak"


def test_ad_sadelestirme():
    assert _sade("Bursa İli") == _sade("Bursa") == "bursa"
    assert _sade("Hakkâri") == _sade("Hakkari")
