"""F6 – Cumhurbaşkanı Kararı 10502 (RG 18.10.2025/33051) EK-1 Peyzaj İzleme Formu üreticisi.

Mevzuatın EK-1 formundaki 23 maddeyi birebir izler:
- Hesap çekirdeğinden türetilebilen maddeler (1–4, 7, 11, 12–14, 17, 22) otomatik doldurulur
  ve açıkça "[Hesap / Tahmin]" etiketi taşır.
- Saha ölçümü veya kurum içi kayıt gerektiren maddeler (5–6, 8–10, 15–16, 18–21, 23) uydurulmaz,
  "[İdare tarafından doldurulur]" şeklinde boş bırakılır.
- 3–17. maddeler mevcut peyzajdan; önerilen peyzaj yalnız 22. maddede "planlanan" olarak.
"""
from __future__ import annotations

from datetime import date
from html import escape

from .fao56 import bitki_bilgi

EK1_KATEGORILER = (
    "Ağaçlar",
    "Ağaççıklar",
    "Çalılar",
    "Çiçekler",
    "Yer örtücüler",
    "Sarılıcı ve tırmanıcılar",
    "Kaktüsler",
    "Çim",
)


# Katalogdaki EK-1 dışı kategoriler. "Çayır" (yonca, üçgül, fiğ, arpa…) EK-1'de yok;
# bu türler Kc ≥ 0,9 olabildiği için kurakçıl sayılmaz, 11–12. maddelere girmez,
# 13–14. maddelerde çimin yanında ayrıca gösterilir.
CAYIR_KATEGORI = "Çayır"
# Katalogda olmayan satırlar için grup → EK-1 kategorisi
GRUP_KATEGORI = {
    "agac_cali": "Ağaçlar",
    "cali_otsu": "Çalılar",
    "yer_ortucu": "Yer örtücüler",
}


def _tr(x: float, ondalik: int = 0) -> str:
    return f"{x:,.{ondalik}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _alan(s: dict) -> float:
    return float(s.get("alan_m2") or 0)


def satir_sinifi(s: dict) -> tuple[str, str]:
    """Bir peyzaj satırı için (sınıf, etiket). sınıf: 'cim', 'cayir' ya da bir EK-1 kategorisi."""
    tur = (s.get("tur") or "").strip()
    grup = s.get("grup") or ""
    if grup == "cim":
        return "cim", s.get("ad") or tur
    try:
        bilgi = bitki_bilgi(tur)
    except KeyError:
        bilgi = None
    if bilgi is not None:
        kat = bilgi["ek1_kategori"]
        etiket = f"{bilgi['turkce_ad']} ({bilgi['tur']})"
        if kat == CAYIR_KATEGORI:
            return "cayir", etiket
        if kat in EK1_KATEGORILER and kat != "Çim":
            return kat, etiket
        if kat == "Çim":
            return "cim", etiket
    etiket = s.get("ad") or tur
    if grup == "cayir_yonca":
        return "cayir", etiket
    if grup in GRUP_KATEGORI:
        return GRUP_KATEGORI[grup], etiket
    raise ValueError(f"EK-1 kategorisi belirlenemedi: {etiket} (grup: {grup or '—'})")


def cim_cayir_alani(satirlar: list[dict]) -> float:
    """Çim ve çayır/yonca (kurakçıl olmayan sulanan örtü) toplam alanı (m²)."""
    return sum(_alan(s) for s in satirlar if _alan(s) > 0 and satir_sinifi(s)[0] in ("cim", "cayir"))


def donusen_alan_m2(mevcut_satirlar: list[dict], oneri_satirlar: list[dict]) -> float:
    """Kurakçıl peyzaja dönüştürülen çim/çayır alanı (m²)."""
    return max(0.0, cim_cayir_alani(mevcut_satirlar) - cim_cayir_alani(oneri_satirlar))


def _peyzaj_ozeti(satirlar: list[dict]) -> dict:
    """Bir peyzaj (mevcut ya da planlanan) için EK-1 alan ve tür dökümü."""
    kategoriler: dict[str, list[str]] = {k: [] for k in EK1_KATEGORILER}
    cim_turleri: list[str] = []
    cayir_turleri: list[str] = []
    cim_alan = cayir_alan = kurakcil_alan = damla = yagmurlama = sulanan = 0.0
    for s in satirlar:
        a = _alan(s)
        if a <= 0:
            continue
        sulanan += a
        if s.get("yontem") == "damla":
            damla += a
        elif s.get("yontem") == "yagmurlama":
            yagmurlama += a
        sinif, etiket = satir_sinifi(s)
        if sinif == "cim":
            cim_alan += a
            hedefler = (cim_turleri, kategoriler["Çim"])
        elif sinif == "cayir":
            cayir_alan += a
            hedefler = (cayir_turleri,)
        else:
            kurakcil_alan += a
            hedefler = (kategoriler[sinif],)
        for liste in hedefler:
            if etiket and etiket not in liste:
                liste.append(etiket)
    return {
        "sulanan_m2": sulanan,
        "damla_m2": damla,
        "yagmurlama_m2": yagmurlama,
        "cim_m2": cim_alan,
        "cayir_m2": cayir_alan,
        "kurakcil_m2": kurakcil_alan,
        "kategoriler": kategoriler,
        "cim_turleri": cim_turleri,
        "cayir_turleri": cayir_turleri,
    }


def ek1_verisi(
    idare_adi: str,
    adres: str,
    toplam_alan_m2: float,
    mevcut_satirlar: list[dict],
    oneri_satirlar: list[dict],
    tasarruf_sonuc: dict,
    tarife_tl_m3: float,
    belirsizlik: dict | None = None,
    iklim_notu: str = "",
) -> dict:
    """EK-1 Peyzaj İzleme Formu alanlarını yapılandırılmış sözlük olarak üretir.

    EK-1 idarenin mevcut peyzajını bildirdiği bir izleme formudur: 3–17. maddeler
    MEVCUT peyzajdan doldurulur. Önerilen peyzaj yalnız 22. maddede (kazanımlar)
    "planlanan" olarak yer alır.
    """
    m = _peyzaj_ozeti(mevcut_satirlar)
    o = _peyzaj_ozeti(oneri_satirlar)

    oneri_m3 = float(tasarruf_sonuc["oneri_m3"])
    mevcut_m3 = float(tasarruf_sonuc["mevcut_m3"])
    fark_m3 = float(tasarruf_sonuc["tasarruf_m3"])

    return {
        "tarih": date.today().isoformat(),
        "idare_adi": idare_adi.strip() or "[İdare adı girilmedi]",
        "adres": adres.strip() or "[Adres girilmedi]",
        "iklim_notu": iklim_notu,
        "toplam_peyzaj_m2": round(toplam_alan_m2 or m["sulanan_m2"]),
        "toplam_peyzaj_girildi": bool(toplam_alan_m2),
        "toplam_yesil_m2": round(m["sulanan_m2"]),
        "toplam_sulanan_m2": round(m["sulanan_m2"]),
        "mevcut_su_m3_yil": round(mevcut_m3),
        "oneri_su_m3_yil": round(oneri_m3),
        "basincli_sulama_m2": round(m["damla_m2"] + m["yagmurlama_m2"]),
        "damla_m2": round(m["damla_m2"]),
        "yagmurlama_m2": round(m["yagmurlama_m2"]),
        "kategoriler": m["kategoriler"],
        "kurakcil_alan_m2": round(m["kurakcil_m2"]),
        "cim_alan_m2": round(m["cim_m2"]),
        "cayir_alan_m2": round(m["cayir_m2"]),
        "cim_turleri": m["cim_turleri"],
        "cayir_turleri": m["cayir_turleri"],
        "tarife_tl_m3": float(tarife_tl_m3),
        "yillik_su_bedeli_tl": round(mevcut_m3 * float(tarife_tl_m3)),
        "donusen_alan_m2": round(donusen_alan_m2(mevcut_satirlar, oneri_satirlar)),
        "plan_kategoriler": o["kategoriler"],
        "plan_cim_cayir_m2": round(o["cim_m2"] + o["cayir_m2"]),
        "plan_kurakcil_m2": round(o["kurakcil_m2"]),
        "tasarruf_m3_yil": round(fark_m3),
        "tasarruf_yuzde": round(float(tasarruf_sonuc["tasarruf_yuzde"]), 1),
        "tasarruf_tl_yil": round(float(tasarruf_sonuc["tasarruf_tl"] or 0)),
        "hane_esdegeri": round(float(tasarruf_sonuc["hane_esdegeri"])),
        "belirsizlik": belirsizlik,
    }


def ek1_html(v: dict) -> str:
    """Yazdırılabilir (A4 / PDF) resmi CB Kararı 10502 EK-1 Peyzaj İzleme Formu taslağı."""
    b = v.get("belirsizlik") or {}
    t_bant = ""
    if b.get("tasarruf_m3"):
        tb = b["tasarruf_m3"]
        t_bant = f" (Monte Carlo P10–P90: {_tr(tb['p10'])} – {_tr(tb['p90'])} m³/yıl)"
    m_bant = ""
    if b.get("mevcut_m3"):
        mb = b["mevcut_m3"]
        m_bant = f" (P10–P90: {_tr(mb['p10'])} – {_tr(mb['p90'])} m³/yıl)"
    o_bant = ""
    if b.get("oneri_m3"):
        ob = b["oneri_m3"]
        o_bant = f" (P10–P90: {_tr(ob['p10'])} – {_tr(ob['p90'])} m³/yıl)"

    plan_turler = "; ".join(
        f"{escape(k)}: {', '.join(escape(x) for x in v['plan_kategoriler'][k])}"
        for k in EK1_KATEGORILER
        if k != "Çim" and v["plan_kategoriler"].get(k)
    ) or "—"
    cayir_not = ""
    if v["cayir_alan_m2"]:
        cayir_not = (
            f"<br/><span style='font-weight:400;font-size:11px;color:#475569;'>Ayrıca çayır/yonca: "
            f"{_tr(v['cayir_alan_m2'])} m² (kurakçıl sayılmadı)</span>"
        )
    toplam_not = "" if v.get("toplam_peyzaj_girildi") else " <span class='bos'>(toplam alan girilmedi; sulanan alan yazıldı)</span>"

    kat_satir = ""
    for i, kat in enumerate(EK1_KATEGORILER):
        liste = ", ".join(escape(x) for x in v["kategoriler"].get(kat, [])) or "—"
        ilk = (
            '<td rowspan="8" class="lbl">Peyzaj düzenlemesinde kurakçıl bitkiler kullanılıyor ise '
            'kategorisine göre bitkisel peyzaj elemanlarının Türkçe ve Latince isimleri</td>'
            if i == 0
            else ""
        )
        no = '<td rowspan="8" class="no">11.</td>' if i == 0 else ""
        kat_satir += f"<tr>{no}{ilk}<td class='sub'>{escape(kat)}</td><td>{liste}</td></tr>\n"

    cim_tur = ", ".join(escape(x) for x in v["cim_turleri"]) or "Çim alanı yok"
    if v["cayir_turleri"]:
        cim_tur += " · Çayır/yonca: " + ", ".join(escape(x) for x in v["cayir_turleri"])
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="color-scheme" content="light" />
  <title>EK-1 Peyzaj İzleme Formu Taslağı — {escape(v['idare_adi'])}</title>
  <style>
    html {{ background: #fff; }}
    body {{ font-family: "Segoe UI", Arial, sans-serif; color: #111; background: #fff; margin: 24px; font-size: 12.5px; line-height: 1.45; }}
    .wrap {{ max-width: 820px; margin: 0 auto; }}
    .ust {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #111; padding-bottom: 10px; margin-bottom: 14px; }}
    .ek {{ font-weight: 700; font-size: 14px; text-align: right; }}
    h1 {{ margin: 0 0 4px; font-size: 17px; }}
    .not {{ background: #f8fafc; border: 1px solid #cbd5e1; padding: 8px 10px; border-radius: 6px; font-size: 11.5px; margin-bottom: 14px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #334155; padding: 6px 8px; vertical-align: top; }}
    td.no {{ width: 32px; font-weight: 700; text-align: center; background: #f1f5f9; }}
    td.lbl {{ width: 36%; font-weight: 600; background: #f8fafc; }}
    td.sub {{ width: 22%; background: #f8fafc; }}
    .bos {{ color: #64748b; font-style: italic; }}
    .hesap {{ font-weight: 600; color: #0f172a; }}
    .tag {{ display: inline-block; font-size: 10px; padding: 1px 5px; border-radius: 4px; background: #dbeafe; color: #1e40af; margin-left: 4px; }}
    .btn-bar {{ margin-bottom: 14px; display: flex; gap: 8px; }}
    .btn {{ padding: 7px 14px; border: 1px solid #2563eb; background: #2563eb; color: #fff; border-radius: 6px; cursor: pointer; font-weight: 600; }}
    .alt {{ margin-top: 14px; font-size: 11px; color: #475569; }}
    @media print {{ .btn-bar {{ display: none; }} body {{ margin: 10mm; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="btn-bar">
      <button class="btn" onclick="window.print()">Yazdır / PDF Kaydet</button>
    </div>
    <div class="ust">
      <div>
        <h1>PEYZAJ İZLEME FORMU (TASLAK)</h1>
        <div>Dayanak: Cumhurbaşkanı Kararı 10502 (RG 18.10.2025 / 33051, Md. 6 &amp; Geçici Md. 1)</div>
      </div>
      <div class="ek">EK-1<br/><span style="font-weight:400; font-size:11px;">Tarih: {escape(v['tarih'])}</span></div>
    </div>
    <div class="not">
      <strong>Önemli ayrım:</strong> 3–17. maddeler <strong>mevcut</strong> peyzajı, 22. madde <strong>planlanan</strong> dönüşümü gösterir. <span class="tag">HESAP</span> işaretli satırlar Florify FAO-56 Penman-Monteith çekirdeğiyle ({escape(v['iklim_notu'] or 'Open-Meteo/ERA5')}) hesaplanan tahminlerdir; sayaç ölçümü değildir. Kurum içi ölçüm veya beyan gerektiren satırlar idarece doldurulmak üzere boş bırakılmıştır.
    </div>
    <table>
      <tr><td class="no">1.</td><td class="lbl" colspan="2">İdare adı</td><td>{escape(v['idare_adi'])}</td></tr>
      <tr><td class="no">2.</td><td class="lbl" colspan="2">Adres / Konum</td><td>{escape(v['adres'])}</td></tr>
      <tr><td class="no" rowspan="3">3.</td><td class="lbl" colspan="2">Toplam peyzaj büyüklüğü (m²)</td><td class="hesap">{_tr(v['toplam_peyzaj_m2'])} m²{toplam_not}</td></tr>
      <tr><td class="lbl" colspan="2">Toplam yeşil alan büyüklüğü (m²)</td><td class="hesap">{_tr(v['toplam_yesil_m2'])} m² <span class="bos">(varsayım: yeşil alanın tamamı sulanıyor)</span></td></tr>
      <tr><td class="lbl" colspan="2">Toplam sulanan peyzaj büyüklüğü (m²)</td><td class="hesap">{_tr(v['toplam_sulanan_m2'])} m²</td></tr>
      <tr><td class="no">4.</td><td class="lbl" colspan="2">Peyzajda kullanılan yıllık su miktarı (m³/yıl)</td><td class="hesap">{_tr(v['mevcut_su_m3_yil'])} m³/yıl <span class="tag">HESAP</span>{m_bant}<br/><span style="font-weight:400;font-size:11px;color:#475569;">(Sayaç ölçümü değil; idarenin sayaç kaydı varsa o yazılmalı)</span></td></tr>
      <tr><td class="no">5.</td><td class="lbl" colspan="2">Kullanılan suyun kaynak tipine göre dağılımı (şebeke / kuyu / yüzey / arazöz / yağmur hasadı / arıtılmış atıksu)</td><td class="bos">[İdare tarafından sayaç/kayıttan doldurulur]</td></tr>
      <tr><td class="no">6.</td><td class="lbl" colspan="2">Sulama günün hangi döneminde yapılıyor? (Gün doğumu öncesi–batımı sonrası / Gün ortası)</td><td class="bos">[İdare tarafından doldurulur]</td></tr>
      <tr><td class="no">7.</td><td class="lbl" colspan="2">Basınçlı (damla, yağmurlama vb.) sulama yöntemleri ile sulanan alan (m²)</td><td class="hesap">{_tr(v['basincli_sulama_m2'])} m² <span class="tag">HESAP</span> (Damla: {_tr(v['damla_m2'])} m² · Yağmurlama: {_tr(v['yagmurlama_m2'])} m²)</td></tr>
      <tr><td class="no">8.</td><td class="lbl" colspan="2">Peyzajda otomatik sulama sistemi var mı?</td><td class="bos">Evet (  ) &nbsp;&nbsp; Hayır (  )</td></tr>
      <tr><td class="no">9.</td><td class="lbl" colspan="2">Kullanılan su ölçüm ve izleme sistemleri ile kayıt altına alınıyor mu?</td><td class="bos">Evet (  ) &nbsp;&nbsp; Hayır (  )</td></tr>
      <tr><td class="no">10.</td><td class="lbl" colspan="2">Peyzaj tasarımı esnasında toprak analizleri yapılıyor mu?</td><td class="bos">Evet (  ) &nbsp;&nbsp; Hayır (  )</td></tr>
      {kat_satir}
      <tr><td class="no">12.</td><td class="lbl" colspan="2">Kurakçıl bitkilerin yer aldığı alan büyüklüğü (m²)</td><td class="hesap">{_tr(v['kurakcil_alan_m2'])} m²</td></tr>
      <tr><td class="no">13.</td><td class="lbl" colspan="2">Peyzajda kullanılan çim yüzey alanı (m²)</td><td class="hesap">{_tr(v['cim_alan_m2'])} m²{cayir_not}</td></tr>
      <tr><td class="no">14.</td><td class="lbl" colspan="2">Peyzajda kullanılan çim türleri</td><td>{cim_tur}</td></tr>
      <tr><td class="no">15.</td><td class="lbl" colspan="2">Malçlama yapılıyor ise kullanılan malç malzemeleri</td><td class="bos">[İdare tarafından doldurulur]</td></tr>
      <tr><td class="no">16.</td><td class="lbl" colspan="2">Peyzaj tasarımında zonlama yapılıyor mu?</td><td class="bos">Evet (  ) &nbsp;&nbsp; Hayır (  )</td></tr>
      <tr><td class="no">17.</td><td class="lbl" colspan="2">Peyzaj için kullanılan yıllık su bedeli (TL/yıl)</td><td class="hesap">{_tr(v['yillik_su_bedeli_tl'])} TL/yıl <span class="tag">HESAP</span> ({_tr(v['tarife_tl_m3'], 2)} TL/m³, KDV hariç)</td></tr>
      <tr><td class="no">18–21.</td><td class="lbl" colspan="2">Yıllık bakım ve enerji bedeli, yenilenebilir enerji kullanımı</td><td class="bos">[İdare tarafından muhasebe/saha kaydından doldurulur]</td></tr>
      <tr><td class="no" rowspan="5">22.</td><td class="lbl" rowspan="5">Mevcut peyzajın kurakçıl peyzaj ile yeniden düzenlenmesine ilişkin kazanımlar <span class="bos">(planlanan dönüşüm)</span></td><td class="sub">Dönüştürülen çim/çayır alanı (m²)</td><td class="hesap">{_tr(v['donusen_alan_m2'])} m² <span class="tag">PLAN</span></td></tr>
      <tr><td class="sub">Planlanan peyzaj</td><td class="hesap">{_tr(v['plan_kurakcil_m2'])} m² kurakçıl · {_tr(v['plan_cim_cayir_m2'])} m² çim/çayır · {_tr(v['oneri_su_m3_yil'])} m³/yıl <span class="tag">HESAP</span>{o_bant}</td></tr>
      <tr><td class="sub">Planlanan kurakçıl türler</td><td>{plan_turler}</td></tr>
      <tr><td class="sub">Elde edilen su tasarrufu (m³/yıl)</td><td class="hesap">{_tr(v['tasarruf_m3_yil'])} m³/yıl (%{_tr(v['tasarruf_yuzde'], 1)} · ~{_tr(v['hane_esdegeri'])} hane · {_tr(v['tasarruf_tl_yil'])} TL/yıl) <span class="tag">HESAP</span>{t_bant}</td></tr>
      <tr><td class="sub">Enerji ve bakım tasarrufu</td><td class="bos">[İdare tarafından ölçülerek doldurulur]</td></tr>
      <tr><td class="no">23.</td><td class="lbl" colspan="2">Geleneksel olmayan su kaynaklarının kullanımına ilişkin planlamalar</td><td class="bos">[İdare tarafından doldurulur]</td></tr>
    </table>
    <div class="alt">
      <strong>Veri ve yöntem atıfları:</strong> FAO-56 Penman-Monteith (Allen vd. 1998); WUCOLS (Costello vd.); bitki katsayıları Konca, Ahmad &amp; Apaydın (2026), <em>Water</em> 18:1362 (CC BY); Türkçe adlar ve kategori eşleşmeleri Tarım ve Orman Bakanlığı Kurakçıl Peyzaj Rehberi (2024); iklim verisi Open-Meteo / ERA5 (CC BY 4.0).
    </div>
  </div>
</body>
</html>
"""
