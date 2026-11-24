"""F5 – 2040'lar senaryosu: iklim değişikliği çimin ve kurakçıl peyzajın su ihtiyacını nasıl değiştirir?"""
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK))

from src.hesap import Bolge, bolge_ihtiyaci, tarife_bul  # noqa: E402
from src.veri import iklim_al  # noqa: E402
from src.veri.konum import il_sirali, konum_bul  # noqa: E402
from src.veri.projeksiyon import GELECEK, TABAN, degisim_oranlari, gelecek_iklimi, model_gunluk  # noqa: E402

MAVI, TURUNCU, GRI = "#2a78d6", "#eb6834", "#8a8984"
AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
SEZON = range(3, 12)
CIM = Bolge("çim", "cim", 0.95, 1)
KURAK = Bolge("kurakçıl", "cali_otsu", 0.50, 1, yontem="damla")

st.set_page_config(page_title="2040 senaryosu", page_icon="🌡️", layout="wide")


def tr(x, ondalik=0):
    return f"{x:,.{ondalik}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(show_spinner="İklim modelleri alınıyor (7 model, 1991–2050)…")
def senaryo(il):
    _, lat, lon = konum_bul(il)
    gozlem = iklim_al(lat, lon, *TABAN)
    oranlar = degisim_oranlari(model_gunluk(lat, lon))
    return gozlem, oranlar, gelecek_iklimi(gozlem, oranlar)


with st.sidebar:
    st.header("Yer")
    iller = il_sirali()
    il = st.selectbox("İl", iller, index=iller.index("Ankara"))

st.title("2040'larda çim ne kadar su isteyecek?")
st.caption(f"7 iklim modeli (CMIP6 HighResMIP, yüksek emisyon senaryosu) · {GELECEK[0]}–{GELECEK[1]} ortalaması, "
           f"{TABAN[0]}–{TABAN[1]} normaline göre · sulama Mart–Kasım")

try:
    gozlem, oranlar, gelecek = senaryo(il)
except Exception as e:
    st.error(f"İklim verisi alınamadı: {e}")
    st.stop()


def ihtiyac(iklim12, bolge):
    return bolge_ihtiyaci(iklim12, bolge, SEZON)


cim_bugun, kur_bugun = ihtiyac(gozlem, CIM), ihtiyac(gozlem, KURAK)
cim_m = {m: ihtiyac(k, CIM) for m, k in gelecek.items()}
kur_m = {m: ihtiyac(k, KURAK) for m, k in gelecek.items()}
cim_gel = float(np.median([v["mm_yil"] for v in cim_m.values()]))
kur_gel = float(np.median([v["mm_yil"] for v in kur_m.values()]))
artis_cim, artis_kur = cim_gel - cim_bugun["mm_yil"], kur_gel - kur_bugun["mm_yil"]
yukselen = sum(o["et0_yil_%"] > 0 for o in oranlar.values())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Çim, bugün (L/m²·yıl)", tr(cim_bugun["mm_yil"]))
k2.metric("Çim, 2040'lar (L/m²·yıl)", tr(cim_gel), f"+{tr(artis_cim)} L (%{tr(100 * artis_cim / cim_bugun['mm_yil'], 1)})",
          delta_color="inverse", help="7 modelin medyanı")
k3.metric("Kurakçıl, 2040'lar (L/m²·yıl)", tr(kur_gel), f"+{tr(artis_kur)} L", delta_color="inverse",
          help=f"Lavanta benzeri, Kc 0,50, damla. Bugün {tr(kur_bugun['mm_yil'])} L/m²")
k4.metric("Buharlaşma artışı öngören model", f"{yukselen} / {len(oranlar)}")

if artis_kur > 0:
    st.info(f"**Çimin m² başına artışı, kurakçıl peyzajınkinin yaklaşık {tr(artis_cim / artis_kur, 1)} katı.** "
            "Çimi dönüştürmek bugün su kazandırmanın yanında gelecekteki iklim riskini de azaltıyor.")

# ───────── aylık grafik: bugün ve 2040'lar (medyan + model aralığı) ─────────
satir = []
for i, ay in enumerate(AYLAR):
    if i + 1 not in SEZON:
        continue
    for ad, bugun, modeller in (("Çim", cim_bugun, cim_m), ("Kurakçıl", kur_bugun, kur_m)):
        degerler = [v["mm"][i] for v in modeller.values()]
        satir.append({"Ay": ay, "Bitki": ad, "Bugün": bugun["mm"][i], "Gelecek": float(np.median(degerler)),
                      "En düşük": min(degerler), "En yüksek": max(degerler)})
df = pd.DataFrame(satir)
renk = alt.Scale(domain=["Çim", "Kurakçıl"], range=[MAVI, TURUNCU])
x = alt.X("Ay:N", sort=AYLAR, title=None, axis=alt.Axis(labelAngle=0))
bant = alt.Chart(df).mark_area(opacity=0.18).encode(x=x, y="En düşük:Q", y2="En yüksek:Q",
                                                     color=alt.Color("Bitki:N", scale=renk, legend=None))
gelecek_cizgi = alt.Chart(df).mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=50, filled=True)).encode(
    x=x, y=alt.Y("Gelecek:Q", title="L/m² · ay"),
    color=alt.Color("Bitki:N", scale=renk, legend=alt.Legend(orient="top", title=None)),
    tooltip=["Bitki", "Ay", alt.Tooltip("Bugün:Q", format=".0f"), alt.Tooltip("Gelecek:Q", format=".0f", title="2040'lar (medyan)"),
             alt.Tooltip("En düşük:Q", format=".0f"), alt.Tooltip("En yüksek:Q", format=".0f")])
bugun_cizgi = alt.Chart(df).mark_line(strokeWidth=1.5, strokeDash=[5, 4]).encode(
    x=x, y="Bugün:Q", color=alt.Color("Bitki:N", scale=renk, legend=None))
st.markdown("**Aylık sulama ihtiyacı:** düz çizgi 2040'lar (medyan), kesik çizgi bugün, gölge modeller arası aralık")
st.altair_chart((bant + bugun_cizgi + gelecek_cizgi).properties(height=340), width="stretch")

# ───────── parkınız için ─────────
st.divider()
st.subheader("Parkınız için")
p1, p2 = st.columns(2)
with p1:
    alan = st.number_input("Çim alanı (m²)", min_value=0, value=10_000, step=500)
with p2:
    kurum = {"Ankara": "ASKİ", "İzmir": "İZSU", "İstanbul": "İSKİ"}.get(il)
    tarife = st.number_input("Su tarifesi (TL/m³, KDV hariç, bugünkü fiyat)", min_value=0.0, step=1.0,
                             value=tarife_bul(kurum)["tl_m3"] if kurum else 100.0, key=f"t5_{il}")
q1, q2, q3 = st.columns(3)
q1.metric("Çim kalırsa 2040'larda ek su (m³/yıl)", tr(alan * artis_cim / 1000))
q2.metric("Çim kalırsa 2040'larda toplam (m³/yıl)", tr(alan * cim_gel / 1000))
q3.metric("Kurakçıla dönerse 2040'larda (m³/yıl)", tr(alan * kur_gel / 1000),
          f"-{tr(alan * (cim_gel - kur_gel) / 1000)} m³ · {tr(alan * (cim_gel - kur_gel) / 1000 * tarife)} TL",
          delta_color="inverse")

with st.expander("Model bazında sonuçlar"):
    st.dataframe(pd.DataFrame([{
        "Model": m, "ET₀ değişimi (%)": round(o["et0_yil_%"], 1), "Yağış değişimi (%)": round(o["yagis_yil_%"], 1),
        "Çim 2040'lar (L/m²)": round(cim_m[m]["mm_yil"]), "Kurakçıl 2040'lar (L/m²)": round(kur_m[m]["mm_yil"])}
        for m, o in oranlar.items()]), hide_index=True, width="stretch")

with st.expander("Yöntem ve sınırlar"):
    st.markdown(f"""
- **Modeller:** Open-Meteo Climate API'deki 7 CMIP6 HighResMIP modeli. Senaryo, Open-Meteo'ya göre "CMIP6 içinde RCP8.5'e en yakın" olanı, yani **yüksek emisyon; kötümser uç**. Veriler ERA5-Land'e göre bias düzeltmeli. **Veri 2050'de bittiği için "2040'lar" = {GELECEK[0]}–{GELECEK[1]}.**
- **Delta yöntemi:**
  - Her model için aylık buharlaşma ihtiyacı (ET₀) ve yağış oranı hesaplanır: {GELECEK[0]}–{GELECEK[1]} / {TABAN[0]}–{TABAN[1]}.
  - Bu oran, aynı dönemin gözlenen (ERA5) iklimine uygulanır; böylece modellerin kendi mutlak hataları büyük ölçüde silinir.
  - Kurak aylarda yağış oranı 0,5–1,5 arasında sınırlanır.
- **Modeller arasında fark var.** Bu yüzden tek bir sayı değil, medyan ve aralık gösteriliyor; her modelin sonucu aşağıdaki tabloda.
- **Eksik veri:** EC-Earth3P-HR modelinde 2050 yılı yok. Bu yüzden oranlar günlük ortalamalardan hesaplanıyor; eksik günler sonucu bozmuyor.
- **Değişmeyen varsayımlar:** Bitki katsayıları (Kc), sulama randımanı ve sezon uzunluğu sabit tutuldu. CO₂'nin bitki su kullanımına etkisi hesaba katılmadı.
- **Literatür:** Orta Anadolu için yüzyıl sonuna kadar ET'de +%11 (RCP4.5) ile +%19 (RCP8.5) artış bildirilmiş (Azlak & Şaylan 2024). Bizim 2040'lar sonuçlarımız bununla aynı yönde ve daha küçük.
- **Kaynak:** CMIP6 verisi CC BY 4.0; Open-Meteo Climate API. Ücretsiz API ticari olmayan kullanım içindir.
""")
st.caption("İklim: Open-Meteo Climate API (CMIP6 HighResMIP, CC BY 4.0) ve Open-Meteo/ERA5.")
