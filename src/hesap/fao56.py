"""FAO-56 tabanlı peyzaj sulama ihtiyacı çekirdeği.

Aylık hesap, her ay için:
    KL     = Kc_max(tür) × profil(grup, ay) × kd × kmc      (WUCOLS: yoğunluk ve mikroiklim)
    ETc    = ET0 × KL
    net    = max(0, ETc − Peff)                               (Peff: USDA-SCS)
    brüt   = net / randıman
    m³     = brüt (mm) × sulanan alan (m²) / 1000

Kaynaklar: Allen vd. 1998 (FAO-56); Costello vd. WUCOLS/LCM (kd, kmc);
Konca, Ahmad & Apaydın 2026 (Kc_max tablosu, randımanlar %70/%90).
"""
import csv
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

VERI = Path(__file__).resolve().parents[2] / "kaynaklar" / "veri"
AYLAR = ("oca", "sub", "mar", "nis", "may", "haz", "tem", "agu", "eyl", "eki", "kas", "ara")
RANDIMAN = {"yagmurlama": 0.70, "damla": 0.90}  # Konca vd. 2026
GRUPLAR = ("cim", "agac_cali", "cali_otsu", "yer_ortucu", "cayir_yonca")


def efektif_yagis(p_mm):
    """USDA-SCS aylık efektif yağış (mm/ay); CROPWAT seçeneklerinden biri."""
    if p_mm <= 0:
        return 0.0
    return p_mm * (125 - 0.2 * p_mm) / 125 if p_mm <= 250 else 125 + 0.1 * p_mm


@lru_cache(maxsize=None)
def _profiller():
    with open(VERI / "kc_aylik_profil.csv", encoding="utf-8") as f:
        return {r["grup"]: tuple(float(r[a]) for a in AYLAR) for r in csv.DictReader(f)}


@lru_cache(maxsize=None)
def _bitki_ozellikleri():
    with open(VERI / "bitki_ozellikleri.csv", encoding="utf-8") as f:
        return {
            r["tur"].lower(): {
                "tur": r["tur"],
                "turkce_ad": r["turkce_ad"],
                "birincil_grup": r["birincil_grup"],
                "golge_agaci": r["golge_agaci"] == "1",
                "ek1_kategori": r["ek1_kategori"],
                "bakanlik_rehberi": r["bakanlik_rehberi"],
            }
            for r in csv.DictReader(f)
        }


@lru_cache(maxsize=None)
def _kc_ciftleri():
    with open(VERI / "konca2026_ankara_kc_tablosu.csv", encoding="utf-8") as f:
        return {(r["tur"].lower(), r["grup"]): float(r["kc_max"]) for r in csv.DictReader(f)}


@lru_cache(maxsize=None)
def _kc_tablosu():
    """Tür adına göre tekil (birincil_grup, Kc_max).

    Konca vd. (2026) Ek Tablolarında 7 tür iki grupta birden yer alır; burada
    bitki_ozellikleri.csv içindeki birincil_grup belirleyicidir (sessiz ezme yok).
    """
    ozellik = _bitki_ozellikleri()
    ciftler = _kc_ciftleri()
    sonuc = {}
    for (tur_k, grup), kc in ciftler.items():
        birincil = ozellik.get(tur_k, {}).get("birincil_grup")
        if birincil is None or grup == birincil:
            sonuc[tur_k] = (grup, kc)
    return sonuc


def bitki_kc(tur, grup=None):
    """Tür adından (grup, Kc_max). grup verilirse doğrudan o (tür, grup) çiftini döner."""
    tur_k = tur.lower()
    if grup is not None:
        return (grup, _kc_ciftleri()[(tur_k, grup)])
    return _kc_tablosu()[tur_k]


def bitki_bilgi(tur):
    """Türün Türkçe adı, gölge ağacı durumu, EK-1 kategorisi ve Bakanlık Rehberi eşleşmesi."""
    return _bitki_ozellikleri()[tur.lower()]


def bitki_katalogu():
    """Tüm tekil türlerin Kc + botanik özellik listesi (Türkçe ad, grup, kc_max, ek1_kategori...)."""
    ozellik = _bitki_ozellikleri()
    kc_tab = _kc_tablosu()
    katalog = []
    for tur_k, (grup, kc) in kc_tab.items():
        o = ozellik[tur_k]
        katalog.append({**o, "grup": grup, "kc_max": kc})
    return sorted(katalog, key=lambda r: (r["grup"], r["tur"]))


def kc_aylik(grup, kc_max, profil=True):
    """12 aylık Kc listesi. profil=False ise her ay Kc_max (eski prototip davranışı)."""
    if grup not in GRUPLAR:
        raise ValueError(f"Bilinmeyen grup: {grup}. Geçerli: {GRUPLAR}")
    if not profil:
        return [kc_max] * 12
    return [kc_max * c for c in _profiller()[grup]]


def net_ihtiyac_mm(et0, yagis, kl):
    return max(0.0, et0 * kl - efektif_yagis(yagis))


@dataclass
class Bolge:
    """Bir parkın tek sulama bölgesi (aynı bitki grubu, aynı yöntem)."""
    ad: str
    grup: str
    kc_max: float
    alan_m2: float
    yontem: str = "yagmurlama"
    kd: float = 1.0     # dikim yoğunluğu çarpanı (WUCOLS: seyrek 0,5–0,9, normal 1, sık 1,1–1,3)
    kmc: float = 1.0    # mikroiklim çarpanı (gölge 0,5–0,9, normal 1, sıcak/rüzgarlı 1,1–1,4)
    randiman: float | None = None  # verilmezse yönteme göre RANDIMAN

    def __post_init__(self):
        if self.yontem not in RANDIMAN:
            raise ValueError(f"Bilinmeyen sulama yöntemi: {self.yontem}")
        if self.alan_m2 < 0:
            raise ValueError("Alan negatif olamaz")

    @property
    def etkin_randiman(self):
        return self.randiman if self.randiman is not None else RANDIMAN[self.yontem]

    @classmethod
    def turden(cls, ad, tur, alan_m2, **kw):
        grup, kc = bitki_kc(tur)
        return cls(ad=ad, grup=grup, kc_max=kc, alan_m2=alan_m2, **kw)


def bolge_ihtiyaci(iklim12, bolge, sezon=None, profil=True):
    """Bir bölgenin aylık brüt ihtiyacı.

    iklim12: 12 elemanlı [{"et0": mm/ay, "yagis": mm/ay}, ...] (Ocak=0)
    sezon:   sulanan aylar (1–12); None ise 12 ay (ihtiyaç kışın zaten çoğunlukla 0'dır)
    Dönüş:   {"mm": [12], "m3": [12], "mm_yil": float, "m3_yil": float}
    """
    kcs = kc_aylik(bolge.grup, bolge.kc_max, profil)
    aylar = set(sezon) if sezon else set(range(1, 13))
    mm = []
    for i, (d, kc) in enumerate(zip(iklim12, kcs)):
        if i + 1 not in aylar:
            mm.append(0.0)
            continue
        kl = kc * bolge.kd * bolge.kmc
        mm.append(net_ihtiyac_mm(d["et0"], d["yagis"], kl) / bolge.etkin_randiman)
    m3 = [v * bolge.alan_m2 / 1000 for v in mm]
    return {"mm": mm, "m3": m3, "mm_yil": sum(mm), "m3_yil": sum(m3)}


def alan_ihtiyaci(iklim12, bolgeler, sezon=None, profil=True):
    """Birden çok bölge: bölge bazında sonuç + toplam (m³/ay ve m³/yıl).
    Sert zemin, havuz vb. sulanmayan alanlar bölge olarak verilmez."""
    sonuc = {b.ad: bolge_ihtiyaci(iklim12, b, sezon, profil) for b in bolgeler}
    toplam_ay = [sum(s["m3"][i] for s in sonuc.values()) for i in range(12)]
    return {"bolgeler": sonuc, "m3_ay": toplam_ay, "m3_yil": sum(toplam_ay),
            "alan_m2": sum(b.alan_m2 for b in bolgeler)}
