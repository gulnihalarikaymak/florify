"""Uydu sayfası: İzmir merkez ilçelerinde sulanan kentsel yeşil (2023) ve dönüşüm senaryosu."""
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from scipy.stats import spearmanr

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK))

from src.hesap import HANE_M3_YIL, Bolge, bolge_ihtiyaci, tarife_bul  # noqa: E402
from src.veri import iklim_al  # noqa: E402

MAVI, TURUNCU = "#2a78d6", "#eb6834"
ATIF = ("© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021, 2023) processed by "
        "ESA WorldCover consortium · İlçe sınırları © OpenStreetMap katkıcıları (ODbL) · "
        "Tüketim: İZSU / İzmir BB Açık Veri Portalı (CC BY 4.0)")

st.set_page_config(page_title="Uydu haritası – İzmir", page_icon="🛰️", layout="wide")


def tr(x, ondalik=0):
    return f"{x:,.{ondalik}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data
def veri():
    return pd.read_csv(KOK / "kaynaklar/veri/uydu_izmir_ilce_2023.csv")


@st.cache_data(show_spinner="İklim verisi alınıyor…")
def ihtiyac_mm(kc, yontem):
    """İzmir merkez iklimi (2020–2024), Mart–Kasım: m² başına yıllık brüt ihtiyaç (L)."""
    ik = iklim_al(38.41, 27.14, 2020, 2024)
    return bolge_ihtiyaci(ik, Bolge("x", "cim" if kc >= 0.8 else "cali_otsu", kc, 1, yontem=yontem),
                          sezon=range(3, 12))["mm_yil"]


df = veri()
rho, p = spearmanr(df.sulanan_yesil_m2, df.izsu_2023_m3)

st.title("Uydudan sulanan yeşil – İzmir")
st.caption("Merkez 11 ilçe · Sentinel-2, yaz 2023 · envanter olmadan, açık uydu verisiyle")

with st.expander("Bu sayfa nasıl çalışıyor?", expanded=False):
    st.markdown("""
Şehri 10×10 m'lik karelere böldük. Bir kare **sulanan yeşil** sayılıyor, eğer:
1. **Kentsel alandaysa** (çevresindeki 250 m'nin %40'ından fazlası bina),
2. ESA'nın yapay zekâyla ürettiği **WorldCover** haritasına göre **ağaç ya da su değilse**,
3. ve **Ağustos'ta yeşilse** (NDVI > 0,5). Yazın yağmur yağmadığına göre yeşil kalan alan sulanıyor.

Sonuç İZSU'nun gerçek park ve mezarlık sulama faturalarıyla karşılaştırıldı.
Ayrıntı ve sınırlar: `docs/ai3_uydu_plani.md`.
""")

# ───────── özet kartlar ─────────
toplam_m2 = df.sulanan_yesil_m2.sum()
cim_mm = ihtiyac_mm(0.95, "yagmurlama")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Sulanan yeşil (km²)", tr(toplam_m2 / 1e6, 2))
k2.metric("Hesaplanan su (milyon m³/yıl)", tr(toplam_m2 * cim_mm / 1e9, 1),
          help=f"Çim varsayımıyla {tr(cim_mm)} L/m²·yıl (Kc 0,95, yağmurlama)")
k3.metric("İZSU faturası 2023 (milyon m³)", tr(df.izsu_2023_m3.sum() / 1e6, 1),
          help="Park ve mezarlık aboneleri; mezarlıklar, ağaç sulaması ve kış tüketimi dahil")
k4.metric("Fatura ile uyum (Spearman ρ)", tr(rho, 2),
          help=f"p = {p:.3f}, n = 11. İlçe büyüklüğü sabit tutulunca kısmi ρ = 0,70.")

# ───────── karşılaştırma grafiği ─────────
g1, g2 = st.columns([1.1, 1])
with g1:
    st.markdown("**Uydu ve fatura, ilçe bazında**")
    grafik = df.assign(yesil_bin_m2=df.sulanan_yesil_m2 / 1e3, fatura_bin_m3=df.izsu_2023_m3 / 1e3)
    taban = alt.Chart(grafik).encode(
        x=alt.X("yesil_bin_m2:Q", title="Uydudan sulanan yeşil (bin m²)"),
        y=alt.Y("fatura_bin_m3:Q", title="İZSU sulama faturası 2023 (bin m³)"),
        tooltip=[alt.Tooltip("ilce:N", title="İlçe"),
                 alt.Tooltip("yesil_bin_m2:Q", title="Sulanan yeşil (bin m²)", format=",.0f"),
                 alt.Tooltip("fatura_bin_m3:Q", title="Fatura (bin m³)", format=",.0f")])
    st.altair_chart((taban.mark_circle(size=110, color=MAVI, opacity=1)
                     + taban.mark_text(align="left", dx=8, dy=-6, fontSize=11, color="#8a8984")
                     .encode(text="ilce:N"))
                    .properties(height=380), width="stretch")
with g2:
    st.markdown("**Harita**")
    st.image(str(KOK / "prototip/cikti/uydu_izmir_harita.png"), width="stretch")

# ───────── dönüşüm senaryosu ─────────
st.divider()
st.subheader("Senaryo: sulanan yeşilin bir kısmı kurakçıl peyzaja dönerse")
s1, s2, s3 = st.columns([1.2, 1, 1])
with s1:
    secim = st.selectbox("İlçe", ["Tüm merkez ilçeler"] + df.ilce.tolist())
with s2:
    oran = st.slider("Dönüştürülen pay (%)", 0, 100, 30, step=5)
with s3:
    tarife = st.number_input("Su tarifesi (TL/m³)", min_value=0.0, value=tarife_bul("İZSU")["tl_m3"],
                             step=1.0, help="Varsayılan: İZSU park ve mezarlık, 01.06.2026, KDV hariç")
alan = toplam_m2 if secim.startswith("Tüm") else int(df.loc[df.ilce == secim, "sulanan_yesil_m2"].iloc[0])
kurak_mm = ihtiyac_mm(0.50, "damla")
mevcut = alan * cim_mm / 1000
sonra = alan * (1 - oran / 100) * cim_mm / 1000 + alan * oran / 100 * kurak_mm / 1000
fark = mevcut - sonra
c1, c2, c3, c4 = st.columns(4)
c1.metric("Mevcut (m³/yıl)", tr(mevcut))
c2.metric("Dönüşüm sonrası (m³/yıl)", tr(sonra), f"-%{tr(100 * fark / mevcut if mevcut else 0, 1)}",
          delta_color="inverse")
c3.metric("Tasarruf (TL/yıl)", tr(fark * tarife))
c4.metric("Hane eşdeğeri", tr(fark / HANE_M3_YIL))
st.caption(f"Varsayım: mevcut sulanan yeşilin tamamı çim (Kc 0,95, yağmurlama, {tr(cim_mm)} L/m²); dönüşen kısım "
           f"lavanta benzeri kurakçıl (Kc 0,50, damla, {tr(kurak_mm)} L/m²). İklim İzmir merkez 2020–2024. "
           "Sulanan yeşilin bir kısmı zaten çalı olabileceği için tasarruf üst sınırdır.")

with st.expander("İlçe tablosu"):
    tablo = df[["ilce", "sulanan_yesil_m2", "izsu_2023_m3", "kentsel_m2"]].rename(columns={
        "ilce": "İlçe", "sulanan_yesil_m2": "Sulanan yeşil (m²)", "izsu_2023_m3": "İZSU 2023 (m³)",
        "kentsel_m2": "Kentsel alan (m²)"})
    st.dataframe(tablo, hide_index=True, width="stretch")

with st.expander("Sınırlar"):
    st.markdown("""
- **Test küçük:** 11 ilçeyle yapıldı. Kural, ilk denemeden sonra kentsel alana sınırlandı; denenen üç kuralın hepsi belgede raporlandı.
- **Çim ile sulanan çalı ayrılmıyor.** İkisi de "sulanan yeşil" sayılıyor.
- **WorldCover 2021 tarihli,** doğruluğu yaklaşık %75–80.
- **Görünmeyen alanlar:** Ağaç altındaki çim ve 10 m'den dar refüjler görünmüyor.
- **Fatura ile hesap birebir karşılaştırılamaz.** İZSU verisinde mezarlıklar da var ve tüketim sütununun anlamı tam net değil.
""")
st.caption(ATIF)
