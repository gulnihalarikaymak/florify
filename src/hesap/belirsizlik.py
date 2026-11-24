"""Parametre belirsizliği (Monte Carlo, P10–P90 aralığı).

Tek nokta tahmin yerine girdi varsayımlarındaki belirsizliği yansıtır
(bkz. docs/dogrulama_ve_sentetik_veri.md §2.3):
    - ET0 çarpanı:           ±%15 (düzgün dağılım: 0,85–1,15)
    - Kc çarpanı (WUCOLS):   ±%10 (düzgün dağılım: 0,90–1,10)
    - Sulama randımanı:      yağmurlama 0,60–0,80 · damla 0,85–0,95

Not: Bu bir parametre duyarlılığı / simülasyon aralığıdır; saha ölçümünden elde edilmiş
istatistiksel güven aralığı değildir.
"""
from __future__ import annotations

import numpy as np

from .fao56 import Bolge, efektif_yagis, kc_aylik

ET0_ARALIK = (0.85, 1.15)
KC_ARALIK = (0.90, 1.10)
RANDIMAN_ARALIK = {"yagmurlama": (0.60, 0.80), "damla": (0.85, 0.95)}


def _toplam_ornek(rng: np.random.Generator, et0_12: np.ndarray, peff_12: np.ndarray,
                  et0_carpan: np.ndarray, bolgeler: list[Bolge], maske_12: np.ndarray,
                  profil: bool) -> np.ndarray:
    """n çekiliş için toplam yıllık su (m³/yıl) dizisi."""
    n = et0_carpan.shape[0]
    toplam = np.zeros(n, dtype=np.float64)
    for b in bolgeler:
        if b.alan_m2 <= 0:
            continue
        kc_12 = np.array(kc_aylik(b.grup, b.kc_max, profil), dtype=np.float64) * b.kd * b.kmc
        kc_carpan = rng.uniform(*KC_ARALIK, size=n)
        if b.randiman is not None:
            lo, hi = max(0.3, b.randiman - 0.05), min(1.0, b.randiman + 0.05)
        else:
            lo, hi = RANDIMAN_ARALIK[b.yontem]
        rand = rng.uniform(lo, hi, size=n)
        # şekil: (n, 12)
        etc = (et0_carpan[:, None] * et0_12[None, :]) * (kc_carpan[:, None] * kc_12[None, :])
        net = np.maximum(0.0, etc - peff_12[None, :]) * maske_12[None, :]
        brut_yil = net.sum(axis=1) / rand
        toplam += brut_yil * (b.alan_m2 / 1000.0)
    return toplam


def belirsizlik_araligi(iklim12: list[dict], mevcut_b: list[Bolge], oneri_b: list[Bolge],
                        sezon=None, profil: bool = True, n: int = 1000, tohum: int = 42) -> dict:
    """Mevcut, önerilen ve tasarruf (m³/yıl) için P10–P50–P90 aralığı."""
    rng = np.random.default_rng(tohum)
    et0_12 = np.array([d["et0"] for d in iklim12], dtype=np.float64)
    peff_12 = np.array([efektif_yagis(d["yagis"]) for d in iklim12], dtype=np.float64)
    aylar = set(sezon) if sezon else set(range(1, 13))
    maske_12 = np.array([1.0 if (i + 1) in aylar else 0.0 for i in range(12)], dtype=np.float64)

    # Aynı çekilişte mevcut ve önerilen aynı iklim sapmasını (et0_carpan) paylaşır
    et0_carpan = rng.uniform(*ET0_ARALIK, size=n)
    m_ornek = _toplam_ornek(rng, et0_12, peff_12, et0_carpan, mevcut_b, maske_12, profil)
    o_ornek = _toplam_ornek(rng, et0_12, peff_12, et0_carpan, oneri_b, maske_12, profil)
    t_ornek = m_ornek - o_ornek

    def ozet(arr):
        p10, p50, p90 = np.percentile(arr, [10, 50, 90])
        return {"p10": round(float(p10), 1), "p50": round(float(p50), 1), "p90": round(float(p90), 1)}

    return {
        "n": int(n),
        "mevcut_m3": ozet(m_ornek),
        "oneri_m3": ozet(o_ornek),
        "tasarruf_m3": ozet(t_ornek),
        "varsayim": "ET0 ±%15, Kc ±%10, randıman yağmurlama %60–80 / damla %85–95 (Monte Carlo, n=1000)",
    }
