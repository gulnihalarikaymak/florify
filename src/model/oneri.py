"""F4 – Bitki karışımı öneri motoru (karma tamsayılı doğrusal programlama).

Soru: Belirli bir alanı, kullanıcının kısıtlarını bozmadan, en az suyla hangi türlerle doldururuz?

Karar değişkenleri:
    x_i ≥ 0      i türüne ayrılan alan (m²)
    y_i ∈ {0,1}  i türü seçildi mi
Amaç:
    min Σ x_i · su_i          su_i = türün m² başına yıllık brüt suyu (m³/m²), F1 çekirdeğinden
Kısıtlar:
    Σ x_i = A                              alanın tamamı dolsun
    x_çim_zorunlu = Z                      oyun/çim alanı (kullanıcının seçtiği çim karışımıyla)
    Σ_{gölge ağacı} x_i ≥ a · A            gölge için en az gerçek ağaç payı (ısı ödünleşimi);
                                           çalılar, ağaççıklar, ardıçlar ve bodur türler sayılmaz
    Σ_{çalı/çiçek} x_i ≥ s · A             katman dengesi için en az çalı/çiçek payı (isteğe bağlı)
    x_i ≤ m · A · y_i                      tek tür en fazla m payı (çeşitlilik)
    x_i ≥ p · A · y_i                      seçilen tür en az p payı (anlamsız kırıntı olmasın)
    Σ y_i ≥ N                              en az N tekil tür
Kurallar: yapay çim yok; Kc ≥ 0,9 olan çayır/yonca türleri önerilmez (Konca vd. 2026: çimden fazla su).
Bu bir optimizasyondur, makine öğrenmesi değildir.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from src.hesap import Bolge, bitki_katalogu, bolge_ihtiyaci

YONTEM = {"cim": "yagmurlama", "cayir_yonca": "yagmurlama",
          "agac_cali": "damla", "cali_otsu": "damla", "yer_ortucu": "damla"}
ZORUNLU = "__zorunlu_cim__"
CALI_KATEGORI = ("Çalılar", "Çiçekler", "Ağaççıklar")


class OneriHatasi(ValueError):
    """Kısıtlar birlikte sağlanamıyor."""


@dataclass(frozen=True)
class Tur:
    ad: str
    grup: str
    kc: float
    yontem: str
    turkce_ad: str = ""
    golge: bool = False
    ek1_kategori: str = ""
    bakanlik_rehberi: str = ""


def tur_tablosu():
    """Öneri havuzu: Konca vd. 2026 tablosu + botanik özellikler, tür adına göre tekil."""
    havuz = []
    for r in bitki_katalogu():
        if r["grup"] == "cayir_yonca" and r["kc_max"] >= 0.9:
            continue
        havuz.append(Tur(
            ad=r["tur"],
            grup=r["grup"],
            kc=r["kc_max"],
            yontem=YONTEM[r["grup"]],
            turkce_ad=r["turkce_ad"],
            golge=r["golge_agaci"],
            ek1_kategori=r["ek1_kategori"],
            bakanlik_rehberi=r["bakanlik_rehberi"],
        ))
    return havuz


def golge_agaci(tur):
    """Gerçek taç gölgesi veren ağaç mı? (Çalılar, ağaççıklar, ardıçlar ve bodur türler False.)"""
    return bool(tur.golge)


def cali_cicek(tur):
    """Katman dengesi için çalı / çiçek / ağaççık katmanı (gölge ağaçları hariç)."""
    return (not tur.golge) and tur.ek1_kategori in CALI_KATEGORI


def _su_m3_m2(iklim12, tur, sezon):
    return bolge_ihtiyaci(iklim12, Bolge(tur.ad, tur.grup, tur.kc, 1, yontem=tur.yontem), sezon)["mm_yil"] / 1000


def oner(iklim12, alan_m2, zorunlu_cim_m2=0.0, cim_kc=0.95, min_agac_pay=0.10, max_tur_pay=0.30,
         min_tur_sayisi=4, min_tur_pay=0.03, min_cali_pay=0.0, haric=(), sezon=range(3, 12), havuz=None):
    """En az su isteyen karışım. Dönüş: {"secim": [...], "m3_yil": float, "alan_m2": float}"""
    if alan_m2 <= 0:
        raise OneriHatasi("Alan sıfırdan büyük olmalı")
    if not 0 <= zorunlu_cim_m2 <= alan_m2:
        raise OneriHatasi("Zorunlu çim alanı, toplam alanı aşamaz")
    uygun_havuz = [t for t in (havuz if havuz is not None else tur_tablosu()) if t.ad not in set(haric)]
    turler = uygun_havuz + ([Tur(ZORUNLU, "cim", cim_kc, "yagmurlama", "Çim (zorunlu alan)", False, "Çim")]
                            if zorunlu_cim_m2 > 0 else [])
    n = len(turler)
    if n == 0:
        raise OneriHatasi("Seçilebilecek tür kalmadı")
    su = np.array([_su_m3_m2(iklim12, t, sezon) for t in turler])
    A = float(alan_m2)

    # değişkenler: [x_0..x_{n-1}, y_0..y_{n-1}]
    c = np.concatenate([su, np.zeros(n)])
    kis = []
    bir = np.zeros(2 * n)
    bir[:n] = 1
    kis.append(LinearConstraint(bir, A, A))                                      # Σx = A
    agac = np.zeros(2 * n)
    agac[[i for i, t in enumerate(turler) if golge_agaci(t)]] = 1
    kis.append(LinearConstraint(agac, min_agac_pay * A, np.inf))                 # gerçek gölge ağacı payı
    if min_cali_pay > 0:
        cali = np.zeros(2 * n)
        cali[[i for i, t in enumerate(turler) if cali_cicek(t)]] = 1
        kis.append(LinearConstraint(cali, min_cali_pay * A, np.inf))             # çalı/çiçek katman payı
    say = np.zeros(2 * n)
    say[n:] = 1
    say[[n + i for i, t in enumerate(turler) if t.ad == ZORUNLU]] = 0            # zorunlu çim sayılmaz
    kis.append(LinearConstraint(say, min_tur_sayisi, np.inf))                    # en az N tekil tür
    ust = np.zeros((n, 2 * n))
    alt = np.zeros((n, 2 * n))
    for i, t in enumerate(turler):
        ust[i, i], alt[i, i] = 1, 1
        if t.ad == ZORUNLU:
            ust[i, n + i], alt[i, n + i] = -A, 0                                  # pay sınırı yok
        else:
            ust[i, n + i], alt[i, n + i] = -max_tur_pay * A, -min_tur_pay * A
    kis.append(LinearConstraint(ust, -np.inf, 0))                                # x ≤ m·A·y
    kis.append(LinearConstraint(alt, 0, np.inf))                                 # x ≥ p·A·y
    lb = np.zeros(2 * n)
    ub = np.concatenate([np.full(n, A), np.ones(n)])
    for i, t in enumerate(turler):
        if t.ad == ZORUNLU:
            lb[i] = ub[i] = zorunlu_cim_m2                                        # x_zorunlu = Z
            lb[n + i] = ub[n + i] = 1
    sonuc = milp(c, constraints=kis, bounds=Bounds(lb, ub),
                 integrality=np.concatenate([np.zeros(n), np.ones(n)]), options={"time_limit": 20})
    if not sonuc.success:
        raise OneriHatasi("Kısıtlar birlikte sağlanamıyor: en az tür sayısı, tür payları, ağaç/çalı payı ve "
                          "zorunlu çim alanını birlikte kontrol edin.")
    x = sonuc.x[:n]
    secim = []
    for i in np.argsort(-x):
        if x[i] < 0.5:
            continue
        t = turler[i]
        secim.append({"tur": "Çim (zorunlu alan)" if t.ad == ZORUNLU else t.ad,
                      "turkce_ad": t.turkce_ad,
                      "grup": t.grup,
                      "ek1_kategori": t.ek1_kategori,
                      "bakanlik_rehberi": t.bakanlik_rehberi,
                      "golge": golge_agaci(t),
                      "kc": t.kc, "yontem": t.yontem, "alan_m2": float(x[i]),
                      "m3_yil": float(x[i] * su[i]), "l_m2": float(su[i] * 1000)})
    return {"secim": secim, "m3_yil": float(x @ su), "alan_m2": A}
