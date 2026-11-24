"""F4 – Bitki karışımı önerisi: kısıtlar altında en az su isteyen karışım."""
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK))

from src.hesap import HANE_M3_YIL, Bolge, bolge_ihtiyaci, tarife_bul  # noqa: E402
from src.model import OneriHatasi, oner, tur_tablosu  # noqa: E402
from src.veri import iklim_al  # noqa: E402
from src.veri.konum import il_sirali, konum_bul  # noqa: E402

GRUP_AD = {"cim": "çim", "agac_cali": "ağaç / büyük çalı", "cali_otsu": "çalı / otsu",
           "yer_ortucu": "yer örtücü", "cayir_yonca": "çayır"}
YONTEM_AD = {"yagmurlama": "yağmurlama", "damla": "damla"}
# Hazır ayarlar: (en az gölge ağacı %, en az çalı/çiçek %, tek tür en fazla %, en az tür sayısı)
AYAR = {
    "En az su": (10, 0, 30, 4),
    "Dengeli: gölge ve çeşitlilik": (25, 20, 20, 6),
    "Zengin görünüm": (20, 30, 12, 9),
}

st.set_page_config(page_title="Bitki önerisi", page_icon="🌿", layout="wide")


def tr(x, ondalik=0):
    return f"{x:,.{ondalik}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(show_spinner="İklim verisi alınıyor…")
def iklim(il):
    _, lat, lon = konum_bul(il)
    return iklim_al(lat, lon, 2020, 2024)


@st.cache_data
def tur_secenekleri():
    """'Türkçe ad (Latince)' → Latince ad."""
    return {f"{t.turkce_ad} ({t.ad})": t.ad for t in sorted(tur_tablosu(), key=lambda t: t.turkce_ad)}


with st.sidebar:
    st.header("Yer")
    iller = il_sirali()
    il = st.selectbox("İl", iller, index=iller.index("Ankara"))
    st.caption("İklim: son 5 yıl (2020–2024) · sulama Mart–Kasım")
    kurum = {"Ankara": "ASKİ", "İzmir": "İZSU", "İstanbul": "İSKİ"}.get(il)
    tarife = st.number_input("Su tarifesi (TL/m³, KDV hariç)", min_value=0.0, step=1.0, key=f"t_{il}",
                             value=tarife_bul(kurum)["tl_m3"] if kurum else 100.0,
                             help="Ankara, İzmir ve İstanbul için doğrulanmış tarife; diğer illerde elle girin.")

st.title("Çimin yerine hangi bitkiler?")
st.caption("Kısıtlarınızı girin; motor Konca vd. (2026) tür tablosundan en az su isteyen karışımı seçer. "
           "Bu bir optimizasyondur (karma tamsayılı doğrusal programlama), hesaplanan ihtiyaca dayanır, ölçüm değildir.")

ik = iklim(il)
c1, c2, c3 = st.columns(3)
with c1:
    alan = st.number_input("Dönüştürülecek alan (m²)", min_value=100, value=10_000, step=500)
with c2:
    zorunlu = st.number_input("Çim kalması gereken alan (m²)", min_value=0, max_value=int(alan),
                              value=min(2000, int(alan)), step=100, help="Oyun alanı, piknik çimi vb.")
with c3:
    cim_tip = st.radio("Kalan çimin karışımı", ["Serin iklim çimi (Kc 0,95)", "Kurağa dayanıklı 5'li (Kc 0,80)"],
                       help="5'li karışım: Festuca, Lolium, Poa + Cynodon ve Zoysia (Konca vd. 2026 önerisi)")
cim_kc = 0.95 if cim_tip.startswith("Serin") else 0.80

ayar = st.radio("Hazır ayar", list(AYAR), horizontal=True)
a_agac, a_cali, a_pay, a_say = AYAR[ayar]
d1, d2, d3, d4 = st.columns(4)
with d1:
    min_agac = st.slider("En az gölge ağacı payı (%)", 0, 60, a_agac, key=f"a_{ayar}",
                         help="Yalnız gerçek taç gölgesi veren ağaçlar sayılır (çalılar, ardıçlar ve bodur türler hariç).")
with d2:
    min_cali = st.slider("En az çalı / çiçek payı (%)", 0, 60, a_cali, key=f"c_{ayar}",
                         help="Katman dengesi için gölge ağaçları dışındaki çalı, çiçek ve ağaççıklar.")
with d3:
    max_pay = st.slider("Bir türün en fazla payı (%)", 5, 60, a_pay, key=f"p_{ayar}")
with d4:
    min_say = st.slider("En az tür sayısı", 1, 15, a_say, key=f"s_{ayar}")

secenek = tur_secenekleri()
haric_etiket = st.multiselect(
    "Önerilmesin (iklime uymayan veya istenmeyen türler)", list(secenek),
    placeholder="Türkçe veya Latince adla arayın",
    help="Tür tablosu Konca vd. (2026) Ankara çalışmasından alındı; Ankara dışındaki illerde yerel iklim uygunluğunu kontrol edin.",
)
haric = [secenek[e] for e in haric_etiket]
if il != "Ankara":
    st.info(f"Tür havuzu Konca vd. (2026) Ankara çalışmasından derlendi. {il} için su ihtiyacı {il} iklimiyle "
            "hesaplanıyor; ancak 81 il için doğrulanmış resmi soğuk/sıcak eşiği bulunmadığından otomatik tür elemesi "
            "yapılmıyor. İklime uymayan türleri yukarıdaki kutudan çıkarabilirsiniz.")

try:
    r = oner(ik, alan, zorunlu_cim_m2=zorunlu, cim_kc=cim_kc, min_agac_pay=min_agac / 100,
             min_cali_pay=min_cali / 100, max_tur_pay=max_pay / 100, min_tur_sayisi=min_say, haric=haric)
except OneriHatasi as e:
    st.error(str(e))
    st.stop()

mevcut = bolge_ihtiyaci(ik, Bolge("çim", "cim", 0.95, alan), sezon=range(3, 12))["m3_yil"]
fark = mevcut - r["m3_yil"]

st.divider()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Şu an, tamamı çim (m³/yıl)", tr(mevcut))
k2.metric("Öneriyle (m³/yıl)", tr(r["m3_yil"]), f"-%{tr(100 * fark / mevcut, 1)}", delta_color="inverse")
k3.metric("Tasarruf (TL/yıl)", tr(fark * tarife))
k4.metric("Hane eşdeğeri", tr(fark / HANE_M3_YIL))

REHBER_ETIKET = {"ulke_geneli": "Ülke geneli", "trakya_akdeniz": "Trakya/Akdeniz",
                 "ulke_geneli+trakya_akdeniz": "Ülke geneli + Trakya/Akdeniz", "": "—"}
tablo = pd.DataFrame([{
    "Tür": s["turkce_ad"] if s["tur"].startswith("Çim (zorunlu") else f"{s['turkce_ad']} ({s['tur']})",
    "Kategori (EK-1)": s["ek1_kategori"] or GRUP_AD.get(s["grup"], s["grup"]),
    "Gölge ağacı": "Evet" if s["golge"] else "—",
    "Bakanlık Rehberi (2024)": REHBER_ETIKET.get(s.get("bakanlik_rehberi", ""), "—"),
    "Kc": s["kc"],
    "Sulama": YONTEM_AD[s["yontem"]], "Alan (m²)": round(s["alan_m2"]),
    "Pay (%)": round(100 * s["alan_m2"] / alan, 1), "L/m²·yıl": round(s["l_m2"]),
    "m³/yıl": round(s["m3_yil"])} for s in r["secim"]])

g1, g2 = st.columns([1.2, 1])
with g1:
    st.markdown("**Önerilen karışım: alan ve su**")
    uzun = tablo.melt(id_vars=["Tür", "Kategori (EK-1)"], value_vars=["Alan (m²)", "m³/yıl"],
                      var_name="Ölçü", value_name="Değer")
    uzun["Pay"] = uzun.groupby("Ölçü")["Değer"].transform(lambda v: 100 * v / v.sum())
    st.altair_chart(alt.Chart(uzun).mark_bar(cornerRadiusEnd=3).encode(
        y=alt.Y("Tür:N", sort=tablo["Tür"].tolist(), title=None, axis=alt.Axis(labelLimit=260)),
        x=alt.X("Pay:Q", title="Toplamın yüzdesi"),
        yOffset="Ölçü:N",
        color=alt.Color("Ölçü:N", scale=alt.Scale(domain=["Alan (m²)", "m³/yıl"], range=["#2a78d6", "#eb6834"]),
                        legend=alt.Legend(orient="top", title=None, labelExpr=
                                          "datum.label == 'Alan (m²)' ? 'Alan payı' : 'Su payı'")),
        tooltip=["Tür", "Kategori (EK-1)", "Ölçü", alt.Tooltip("Değer:Q", format=",.0f"),
                 alt.Tooltip("Pay:Q", format=".1f", title="Pay (%)")]).properties(height=60 + 34 * len(tablo)),
        width="stretch")
    st.caption("Mavi: alandaki payı · turuncu: suyun içindeki payı. Kalan çim, küçük alanıyla suyun büyük kısmını içer.")
with g2:
    st.markdown("**Tablo**")
    st.dataframe(tablo, hide_index=True, width="stretch")
    st.download_button("CSV indir", tablo.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"bitki_onerisi_{il}.csv", mime="text/csv")

with st.expander("Nasıl çalışıyor, sınırlar"):
    st.markdown(f"""
- **Ne yapıyor:** Motor, alanın tamamını dolduracak şekilde türlere alan dağıtıyor ve toplam yıllık suyu en aza indiriyor. Her türün m² başına suyu F1 hesap çekirdeğinden, {il} iklimiyle hesaplanıyor.
- **Kısıtlar:**
  - Çim alanı (zorunlu kısım) korunuyor.
  - En az gerçek gölge ağacı payı sağlanıyor; çalılar (*Cotinus*, *Robinia hispida*, *Hibiscus*, *Photinia*), ardıçlar (*Juniperus*) ve bodur türler gölge ağacı sayılmıyor.
  - İsteğe bağlı çalı / çiçek payı ile parkta katman dengesi korunuyor.
  - Bir tür belirlenen paydan fazla yer kaplamıyor; seçilen her tür alanın en az %3'ünü kaplıyor ve tekil tür olarak sayılıyor.
- **Kurallar:** Yapay çim önerilmiyor. Kc 0,9 ve üstü çayır/yonca türleri (ör. *Medicago sativa*) önerilmiyor, çünkü çimden fazla su isteyebiliyorlar.
- **Bakanlık Rehberi eşleşmesi:** `kaynaklar/veri/bitki_ozellikleri.csv` içindeki `bakanlik_rehberi` sütunu, Tarım ve Orman Bakanlığı Kurakçıl Peyzaj Uygulamaları Rehberi (2024) Çizelge 4 (ülke geneli) ve Çizelge 5 (Trakya/Akdeniz) tablolarından birebir kontrol edildi.
- **İklim uygunluğu sınırı:** Tür tablosu Ankara için derlendi. 81 ilin tamamı için doğrulanmış açık bir tür–sıcaklık eşiği tablosu bulunmadığından otomatik tür elemesi yapılmıyor; başka illerde uygunluk "Önerilmesin" kutusundan kontrol edilmeli.
- **Maliyet ve bakım yok:** Kurulum ve bakım maliyeti optimizasyona katılmıyor.
""")
