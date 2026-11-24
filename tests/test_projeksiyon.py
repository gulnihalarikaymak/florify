"""Delta yöntemi testleri (ağ gerektirmez; yapay günlük seri)."""
from datetime import date, timedelta

import pytest

from src.veri.projeksiyon import GELECEK, TABAN, YAGIS_ORAN_SINIR, degisim_oranlari, gelecek_iklimi


def _yapay(model, et0_taban, et0_gelecek, yagis_taban, yagis_gelecek):
    zaman, e, p = [], [], []
    g = date(TABAN[0], 1, 1)
    while g <= date(GELECEK[1], 12, 31):
        gelecek = GELECEK[0] <= g.year <= GELECEK[1]
        zaman.append(g.isoformat())
        e.append(et0_gelecek if gelecek else et0_taban)
        p.append(yagis_gelecek if gelecek else yagis_taban)
        g += timedelta(days=1)
    return {"time": zaman, f"et0_fao_evapotranspiration_sum_{model}": e, f"precipitation_sum_{model}": p}


def test_oranlar_dogru():
    o = degisim_oranlari(_yapay("MRI_AGCM3_2_S", 4.0, 4.4, 1.0, 0.9))
    assert list(o) == ["MRI_AGCM3_2_S"]
    assert o["MRI_AGCM3_2_S"]["et0"] == pytest.approx([1.1] * 12)
    assert o["MRI_AGCM3_2_S"]["yagis"] == pytest.approx([0.9] * 12)
    assert o["MRI_AGCM3_2_S"]["et0_yil_%"] == pytest.approx(10.0)


def test_yagis_orani_sinirlanir():
    o = degisim_oranlari(_yapay("MRI_AGCM3_2_S", 4.0, 4.0, 0.1, 1.0))  # 10 kat artış
    assert max(o["MRI_AGCM3_2_S"]["yagis"]) == pytest.approx(YAGIS_ORAN_SINIR[1])


def test_gozleme_uygulanir():
    o = degisim_oranlari(_yapay("MRI_AGCM3_2_S", 4.0, 4.2, 1.0, 1.0))
    gozlem = [{"et0": 100.0, "yagis": 20.0, "sicaklik": 10.0, "nem": 50.0} for _ in range(12)]
    f = gelecek_iklimi(gozlem, o)["MRI_AGCM3_2_S"]
    assert f[0]["et0"] == pytest.approx(105.0)
    assert f[0]["yagis"] == pytest.approx(20.0)
    assert f[0]["sicaklik"] == 10.0          # diğer alanlar korunur
    assert gozlem[0]["et0"] == 100.0         # girdi değişmez


def test_eksik_model_atlanir():
    assert degisim_oranlari({"time": []}) == {}


def test_eksik_gunler_orani_bozmaz():
    """EC-Earth3P-HR'de 2050 yılı yok: eksik yıl, sahte azalma üretmemeli."""
    g = _yapay("EC_Earth3P_HR", 4.0, 4.0, 1.0, 1.0)
    k = "et0_fao_evapotranspiration_sum_EC_Earth3P_HR"
    g[k] = [None if t.startswith("2050") else v for t, v in zip(g["time"], g[k])]
    o = degisim_oranlari(g)["EC_Earth3P_HR"]
    assert o["et0_yil_%"] == pytest.approx(0.0, abs=1e-9)
