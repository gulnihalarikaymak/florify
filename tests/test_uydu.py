"""Uydu modülü birim testleri (src/uydu/analiz.py)."""
from src.uydu import izmir_ilce_haritasi, utm_epsg, worldcover_karolari


def test_utm_epsg_turkiye_bolgeleri():
    assert utm_epsg(38.41, 27.14) == 32635  # İzmir (35N)
    assert utm_epsg(39.92, 32.85) == 32636  # Ankara (36N)
    assert utm_epsg(37.91, 40.22) == 32637  # Diyarbakır (37N)
    assert utm_epsg(39.91, 43.05) == 32638  # Doğu ucu (38N)


def test_worldcover_karolari_3_derece():
    assert worldcover_karolari(26.80, 38.27, 27.33, 38.60) == ["N36E024", "N36E027"]
    assert worldcover_karolari(32.80, 39.88, 32.90, 39.96) == ["N39E030"]
    assert worldcover_karolari(28.90, 40.98, 29.02, 41.05) == ["N39E027"]


def test_izmir_ilce_haritasi_uretilir():
    yol = izmir_ilce_haritasi("Konak")
    assert yol.exists()
    assert yol.stat().st_size > 10_000
