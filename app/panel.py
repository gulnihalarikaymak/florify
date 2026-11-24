"""Florify – belediye peyzaj suyu karar paneli (F2).

Çalıştırma:  .venv\\Scripts\\python -m streamlit run app/panel.py
"""
import csv
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

from src.hesap import (HANE_M3_YIL, TARIFELER, Bolge, alan_ihtiyaci, bitki_katalogu, efektif_yagis,  # noqa: E402
                       tasarruf)
from src.veri import iklim_al  # noqa: E402
from src.veri.konum import il_sirali, konum_bul  # noqa: E402

AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
GRUP_AD = {"cim": "çim", "agac_cali": "ağaç / büyük çalı", "cali_otsu": "çalı / otsu",
           "yer_ortucu": "yer örtücü", "cayir_yonca": "çayır / yonca"}
YONTEM_AD = {"Yağmurlama (%70)": "yagmurlama", "Damla (%90)": "damla"}
# Renkler: dataviz referans paleti, kategorik sıra (mavi, turuncu); iklim için nötr + yeşil
MAVI, TURUNCU, YESIL, GRI = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"

st.set_page_config(page_title="Florify – peyzaj suyu", page_icon="💧", layout="wide")


# ───────────────────────── veri ─────────────────────────
@st.cache_data
def bitki_listesi():
    """Etiket → (grup, Kc_max). Genel çim karışımları + Konca vd. 2026 tekil tür kataloğu (Türkçe + Latince)."""
    secenek = {
        "Çim karışımı, serin iklim (Lolium/Poa/Festuca) · çim · Kc 0,95": ("cim", 0.95),
        "Çim karışımı, kurağa dayanıklı 5'li (Cynodon/Zoysia katkılı) · çim · Kc 0,80": ("cim", 0.80),
    }
    for r in bitki_katalogu():
        kc = r["kc_max"]
        ad = f"{r['turkce_ad']} ({r['tur']})"
        secenek[f"{ad} · {GRUP_AD[r['grup']]} · Kc {kc:.2f}".replace(".", ",")] = (r["grup"], kc)
    return secenek


@st.cache_data(show_spinner="İklim verisi alınıyor (Open-Meteo / ERA5)…")
def iklim(lat, lon, y1, y2):
    return iklim_al(lat, lon, y1, y2)


@st.cache_data(show_spinner="Konum aranıyor…")
def konum(il, ilce):
    return konum_bul(il, ilce or None)


BITKI = bitki_listesi()
ETIKETLER = list(BITKI)


def etiket(parca):
    return next(e for e in ETIKETLER if parca in e)


def varsayilan(satirlar):
    return pd.DataFrame(satirlar, columns=["Bitki", "Alan (m²)", "Yöntem", "Yoğunluk (kd)"])


def bolgeler(df, onek):
    sonuc = []
    for i, r in df.dropna(subset=["Bitki", "Alan (m²)"]).iterrows():
        if r["Alan (m²)"] <= 0:
            continue
        grup, kc = BITKI[r["Bitki"]]
        sonuc.append(Bolge(ad=f"{onek}{i + 1}. {r['Bitki'].split(' · ')[0]}", grup=grup, kc_max=kc,
                           alan_m2=float(r["Alan (m²)"]),
                           yontem=YONTEM_AD.get(r["Yöntem"], "yagmurlama"),
                           kd=float(r["Yoğunluk (kd)"]) if pd.notna(r["Yoğunluk (kd)"]) else 1.0))
    return sonuc


def tr(x, ondalik=0):
    """Türkçe sayı biçimi: 12.345,6"""
    return f"{x:,.{ondalik}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ───────────────────────── kenar çubuğu ─────────────────────────
with st.sidebar:
    st.header("Yer ve varsayımlar")
    iller = il_sirali()
    il = st.selectbox("İl", iller, index=iller.index("Ankara"))
    ilce = st.text_input("İlçe (isteğe bağlı)", placeholder="ör. Etimesgut")
    donem = st.radio("İklim dönemi", ["Son 5 yıl (2020–2024)", "Uzun dönem normali (1991–2020)"])
    y1, y2 = (2020, 2024) if donem.startswith("Son") else (1991, 2020)
    sezon_secim = st.toggle("Sulama sezonu Mart–Kasım", value=True,
                            help="Kapalıysa 12 ay hesaplanır; kışın ihtiyaç genelde zaten sıfırdır.")
    st.divider()
    tarife_ad = [f"{t['kurum']} · {t['kategori']} · {t['gecerlilik']} · {tr(t['tl_m3'], 2)} TL/m³"
                 for t in TARIFELER] + ["Elle gir"]
    il_kurum = {"Ankara": "ASKİ", "İzmir": "İZSU", "İstanbul": "İSKİ"}.get(il)
    if il_kurum:
        varsayilan_t = max((i for i, t in enumerate(TARIFELER) if t["kurum"] == il_kurum
                            and "geri kazanım" not in t["kategori"].lower()),
                           key=lambda i: TARIFELER[i]["gecerlilik"])
    else:
        varsayilan_t = len(TARIFELER)  # "Elle gir"
    secili = st.selectbox("Su tarifesi (KDV hariç)", tarife_ad, index=varsayilan_t, key=f"tarife_{il}",
                          help="Doğrulanmış tarifesi olmayan illerde elle girin.")
    if secili == "Elle gir":
        tarife = st.number_input("TL/m³", min_value=0.0, value=100.0, step=5.0)
    else:
        tarife = TARIFELER[tarife_ad.index(secili)]["tl_m3"]
    hane = st.number_input("Hane başına yıllık su (m³)", min_value=1, value=HANE_M3_YIL,
                           help="Konca vd. 2026: Ankara hanesi ayda ~15 m³.")

try:
    yer_ad, lat, lon = konum(il, ilce.strip())
except Exception as e:  # ağ hatası ya da bulunamayan ilçe
    st.error(f"Konum bulunamadı: {e}")
    st.stop()
try:
    ik = iklim(lat, lon, y1, y2)
except Exception as e:
    st.error(f"İklim verisi alınamadı: {e}")
    st.stop()
sezon = range(3, 12) if sezon_secim else None

# ───────────────────────── başlık ─────────────────────────
st.title("Çimin yerine ne konsun?")
st.caption(f"{yer_ad} ({lat:.2f}, {lon:.2f}) · iklim {y1}–{y2} · "
           "FAO-56 hesabı; saha ölçümü değildir.")

# ───────────────────────── alan girişi ─────────────────────────
toplam_alan = st.number_input("Parkın toplam alanı (m², sert zemin dahil)", min_value=0,
                              value=10_000, step=500)
kolon = {
    "Bitki": st.column_config.SelectboxColumn("Bitki", options=ETIKETLER, required=True, width="large"),
    "Alan (m²)": st.column_config.NumberColumn("Alan (m²)", min_value=0, step=100, format="%d"),
    "Yöntem": st.column_config.SelectboxColumn("Yöntem", options=list(YONTEM_AD), required=True),
    "Yoğunluk (kd)": st.column_config.NumberColumn(
        "Yoğunluk (kd)", min_value=0.3, max_value=1.3, step=0.1, format="%.1f",
        help="WUCOLS dikim yoğunluğu: seyrek 0,5–0,9 · normal 1,0 · sık 1,1–1,3"),
}
sekme_m, sekme_o = st.tabs(["Mevcut peyzaj", "Önerilen peyzaj"])
with sekme_m:
    mevcut_df = st.data_editor(varsayilan([
        [etiket("Çim karışımı, serin"), 6000, "Yağmurlama (%70)", 1.0],
        [etiket("Buxus sempervirens"), 2000, "Damla (%90)", 1.0],
    ]), column_config=kolon, num_rows="dynamic", key="mevcut", hide_index=True, width="stretch")
with sekme_o:
    oneri_df = st.data_editor(varsayilan([
        [etiket("Çim karışımı, serin"), 2000, "Yağmurlama (%70)", 1.0],
        [etiket("Lavandula angustifolia"), 4000, "Damla (%90)", 1.0],
        [etiket("Buxus sempervirens"), 2000, "Damla (%90)", 1.0],
    ]), column_config=kolon, num_rows="dynamic", key="oneri", hide_index=True, width="stretch")

mevcut_b, oneri_b = bolgeler(mevcut_df, "M"), bolgeler(oneri_df, "Ö")
if not mevcut_b or not oneri_b:
    st.info("Her iki tabloya da en az bir bitki ve alan girin.")
    st.stop()

for ad, bl in (("Mevcut", mevcut_b), ("Önerilen", oneri_b)):
    sulanan = sum(b.alan_m2 for b in bl)
    if toplam_alan and sulanan > toplam_alan:
        st.error(f"{ad} peyzajda sulanan alan ({tr(sulanan)} m²) parkın toplam alanını "
                 f"({tr(toplam_alan)} m²) aşıyor.")
if any(b.grup == "cayir_yonca" and b.kc_max >= 0.9 for b in oneri_b):
    st.warning("Önerilen peyzajda yonca/çayır türleri var. Konca vd. (2026) bu türlerin çimden "
               "fazla su isteyebildiğini gösteriyor; çim alternatifi olarak önerilmez.")

m = alan_ihtiyaci(ik, mevcut_b, sezon)
o = alan_ihtiyaci(ik, oneri_b, sezon)
t = tasarruf(m["m3_yil"], o["m3_yil"], tarife, hane)

# ───────────────────────── sonuç kartları ─────────────────────────
st.divider()
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Mevcut (m³/yıl)", tr(t["mevcut_m3"]))
k2.metric("Önerilen (m³/yıl)", tr(t["oneri_m3"]))
k3.metric("Tasarruf (m³/yıl)", tr(t["tasarruf_m3"]), f"%{tr(t['tasarruf_yuzde'], 1)}")
k4.metric("Tasarruf (TL/yıl)", tr(t["tasarruf_tl"]), help=f"{tr(tarife, 2)} TL/m³, KDV hariç")
k5.metric("Hane eşdeğeri", tr(t["hane_esdegeri"]), help=f"Hane başına {tr(hane)} m³/yıl")

# ───────────────────────── grafikler ─────────────────────────
g1, g2 = st.columns([1.4, 1])
aylik = pd.DataFrame({
    "Ay": AYLAR * 2, "Sıra": list(range(12)) * 2,
    "Peyzaj": ["Mevcut"] * 12 + ["Önerilen"] * 12,
    "m³": [round(v) for v in m["m3_ay"]] + [round(v) for v in o["m3_ay"]],
})
renk = alt.Scale(domain=["Mevcut", "Önerilen"], range=[MAVI, TURUNCU])
with g1:
    st.markdown("**Aylık sulama suyu (m³)**")
    taban = alt.Chart(aylik).encode(
        x=alt.X("Ay:N", sort=AYLAR, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("m³:Q", title="m³ / ay"),
        color=alt.Color("Peyzaj:N", scale=renk, legend=alt.Legend(orient="top", title=None)),
        tooltip=["Peyzaj", "Ay", alt.Tooltip("m³:Q", format=",.0f")])
    st.altair_chart((taban.mark_line(strokeWidth=2) + taban.mark_point(size=60, filled=True))
                    .properties(height=300), width="stretch")

iklim_df = pd.DataFrame({
    "Ay": AYLAR * 2,
    "Değişken": ["Buharlaşma ihtiyacı ET₀"] * 12 + ["Efektif yağış"] * 12,
    "mm": [round(d["et0"]) for d in ik] + [round(efektif_yagis(d["yagis"])) for d in ik],
})
with g2:
    st.markdown("**İklim (mm/ay)**")
    st.altair_chart(alt.Chart(iklim_df).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Ay:N", sort=AYLAR, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset="Değişken:N",
        y=alt.Y("mm:Q", title="mm / ay"),
        color=alt.Color("Değişken:N", scale=alt.Scale(range=[GRI, YESIL]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Değişken", "Ay", "mm"]).properties(height=300), width="stretch")

# ───────────────────────── bölge tablosu ─────────────────────────
satirlar = []
for ad, sonuc, bl in (("Mevcut", m, mevcut_b), ("Önerilen", o, oneri_b)):
    for b in bl:
        s = sonuc["bolgeler"][b.ad]
        satirlar.append({"Peyzaj": ad, "Bölge": b.ad[3:], "Grup": GRUP_AD[b.grup], "Kc": b.kc_max,
                         "Alan (m²)": round(b.alan_m2), "L/m²·yıl": round(s["mm_yil"]),
                         "m³/yıl": round(s["m3_yil"])})
tablo = pd.DataFrame(satirlar)
with st.expander("Bölge bazında sonuçlar", expanded=False):
    st.dataframe(tablo, hide_index=True, width="stretch")
    st.download_button("CSV indir", tablo.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"peyzaj_su_{il}.csv", mime="text/csv")

with st.expander("Yöntem, varsayımlar ve sınırlar"):
    st.markdown(f"""
- **Hesap:** Her ay ET₀ × Kc × kd − efektif yağış (USDA-SCS) = net ihtiyaç. Bu net ihtiyaç sulama randımanına bölünür (yağmurlama %70, damla %90). İklim verisi Open-Meteo / ERA5'ten ({y1}–{y2} ortalaması).
- **Kc değerleri:** Konca, Ahmad & Apaydın (2026), *Water* 18:1362. Aylık Kc profilleri çim için FAO-56'dan alındı; diğer gruplar için FAO-56'nın eğrisi örnek alındı. **Varsayımdır.**
- **Doğrulama:**
  - Las Vegas'ta sayaçla ölçülmüş sulamanın aylık profilini r = 0,96 ile yakalıyor. Tasarrufu ölçülenden düşük tahmin ediyor (%62'ye karşı %76), yani temkinli.
  - İzmir'de park sulama faturalarının mevsimselliğini r = 0,89 ile yakalıyor.
- **Sınırlar:**
  - ERA5, Las Vegas'ta ET₀'ı ~%20 düşük verdi; illerde istasyon karşılaştırması henüz yapılmadı.
  - Ağaç gölgesi ve ısı etkisi bu hesapta yok.
  - Gerçek tüketim, sulama takvimine ve bakıma bağlı olarak bu hesaptan farklı olabilir.
""")
