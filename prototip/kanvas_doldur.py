"""Proje Fikri Kanvası'nı (kaynaklar/hackathon/proje_fikri_kanvasi.pdf) doldurur.

Çıktılar:
    kaynaklar/hackathon/proje_fikri_kanvasi_dolu.pdf   (yazdırılabilir A2)
    docs/proje_fikri_kanvasi.md                        (aynı metin, düzenlemesi kolay)

Metni değiştirmek için aşağıdaki METIN sözlüğünü düzenleyip yeniden çalıştırın.
Okuyucu projeyi bilmiyor varsayılır: teknik terim yok, sayılar hane eşdeğeriyle.
Sayıların kaynağı (24.11.2026, web/sunucu.py fonksiyonlarıyla yeniden hesaplandı):
    - Ankara çim 1.190 L/m²·yıl, 2020–2024 ERA5 (hesap)
    - İzmir 11 ilçe park+mezarlık 2023: 8,37 milyon m³ (İZSU açık verisi, fatura) ≈ 46.500 hane × 180 m³
    - Uydu–fatura Spearman ρ = 0,855, p = 0,0008; kısmi ρ = 0,70 (hesap, n = 11)
    - Ankara 10.000 m², 2.000 m² zorunlu çim, MILP: 11.903 → 4.725 m³/yıl, %60,3, ~40 hane (hesap)
    - SNWA: aylık profil r = 0,96; tasarruf hesap %62 / ölçüm %76
    - 2040'lar Ankara çim +%6,1, 7 modelin 7'si artış (hesap)

Çalıştırma (PyMuPDF gerekir; proje .venv'inde yok):
    py -3 -m pip install pymupdf
    py -3 prototip/kanvas_doldur.py
"""
from pathlib import Path

import pymupdf

KOK = Path(__file__).resolve().parents[1]
GIRDI = KOK / "kaynaklar" / "hackathon" / "proje_fikri_kanvasi.pdf"
CIKTI = KOK / "kaynaklar" / "hackathon" / "proje_fikri_kanvasi_dolu.pdf"
MD = KOK / "docs" / "proje_fikri_kanvasi.md"
FONT = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_B = Path("C:/Windows/Fonts/segoeuib.ttf")

PROJE_ADI = "Florify"
TAKIM_ADI = "Petrichor"
CALISMA_ALANI = "Kent — park ve peyzaj sulaması"
UYELER = [  # (ad soyad, rol)
    ("Kader Demircan", "Açık veri ve mekânsal veri (uydu, OSM)"),
    ("Gül Nihal Arıkaymak", "Literatür ve makale tablolarının veriye dökülmesi"),
    ("Recep Altıntaş", "Kod, hesap çekirdeği ve proje planı"),
]

METIN = {
    "01 Problem": (
        "Parklardaki çim, yazın en çok su isteyen bitki örtüsü. Ankara'da 1 m² çimi bir yıl sulamak "
        "yaklaşık 1.190 litre su gerektiriyor (bizim hesabımız). İzmir'in 11 merkez ilçesinde parklar ve "
        "mezarlıklar 2023'te 8,4 milyon m³ şebeke suyu kullandı (İZSU'nun açık fatura verisi). Bu, "
        "yaklaşık 46 bin hanenin bir yıllık suyu."
    ),
    "02 Hedef kullanıcı ve ihtiyaç": (
        "Belediyelerin park ve bahçe birimleri. Ekim 2025'te çıkan Cumhurbaşkanı Kararı 10502, belediyelerden "
        "çim alanlarını azaltmalarını ve her yıl peyzaj ve su verisi raporlamalarını istiyor. Ama hangi parkta "
        "çimin yerine ne dikerlerse ne kadar su ve para kazanacaklarını hesaplayacak pratik bir araçları yok."
    ),
    "03 Mevcut yaklaşım ve eksikliği": (
        "Bugün kararlar \"kuraklığa dayanıklı bitkiler %20–80 su tasarrufu sağlar\" gibi genel ve çoğu "
        "yurt dışından gelen rakamlarla veriliyor. Park bazında, hangi bitkiyle kaç m³ kazanılacağı "
        "hesaplanmıyor. İzmir'in 10 yıllık fatura verisi, sulamanın kurak ya da yağışlı yıla göre pek "
        "değişmediğine işaret ediyor. İklim, bitki, tarife, uydu ve resmi raporu tek yerde birleştiren "
        "açık bir araç bulamadık."
    ),
    "04 Çözüm önerisi": (
        "Belediye çalışanı bir web sayfasına parkın ilini, büyüklüğünü ve bugünkü bitkilerini girer. Araç, "
        "parkın bugün yılda ne kadar su istediğini, çimin yerine hangi bitkilerin konabileceğini ve bunun "
        "kaç m³ su, kaç TL, kaç hanenin yıllık suyu kadar tasarruf sağlayacağını gösterir. Sonuçlar, kararın "
        "her yıl istediği resmi Peyzaj İzleme Formu'na (EK-1) taslak olarak aktarılır."
    ),
    "05 Yapay zekânın rolü": (
        "Yapay zekâ, uydu görüntülerinden şehirde yazın sulanan yeşil alanları buluyor; park envanteri "
        "olmayan belediye de nerede su harcandığını görüyor. İzmir'de bu tahmin, ilçelerin gerçek park "
        "faturalarıyla örtüştü (11 ilçede sıralama uyumu 0,85 / 1) ve yalnız ilçe büyüklüğüne bakmaktan "
        "daha fazlasını açıkladı. Hackathon'da kendi eğittiğimiz modeli bu yöntemle kıyaslayacağız."
    ),
    "06 Veri ve uygulanabilirlik": (
        "Yalnız herkese açık ve ücretsiz veri kullanıyoruz: geçmiş ve 2040'lar için iklim verisi, Avrupa "
        "Uzay Ajansı'nın uydu görüntüleri ve arazi haritası, Ankara'da yapılmış hakemli bir bitki su "
        "ihtiyacı çalışması, İzmir'in açık su faturası verisi ve belediye su tarifeleri. Henüz "
        "doğrulamadığımız: iklim verisinin Türkiye'deki meteoroloji istasyonlarıyla ne kadar örtüştüğü."
    ),
    "07 Beklenen su etkisi": (
        "Örnek: Ankara'da 10.000 m²'lik bir çim parkın 2.000 m²'si çim kalıp geri kalanına kuraklığa "
        "dayanıklı bitkiler dikilirse, yıllık sulama suyu yaklaşık 11.900 m³'ten 4.700 m³'e iner: %60 daha "
        "az, yaklaşık 40 hanenin bir yıllık suyu (hesap). Takip göstergesi: parkta m² başına yıllık "
        "sulama suyu (sayaçtan)."
    ),
    "08 İlk test": (
        "Varsayımımız: hesabımız tasarrufu abartmıyor. ABD'de sayaçla ölçülmüş bir çalışmada tasarrufu "
        "%62 hesapladık, ölçülen %76'ydı (temkinliyiz). Hackathon günü iklim verisini Türkiye'deki "
        "meteoroloji istasyonlarıyla, uydu yöntemini ikinci bir şehirde (Ankara) sınayacağız; geçme "
        "ölçütlerini önceden yazdık. Sonraki adım: bir belediyeyle sayaçlı pilot park."
    ),
}

# Cevap kutuları (pt), şablondaki beyaz alanlar
KUTU = {
    "01 Problem": (71, 458, 567, 557),
    "02 Hedef kullanıcı ve ihtiyaç": (624, 434, 1120, 557),
    "03 Mevcut yaklaşım ve eksikliği": (71, 714, 567, 837),
    "04 Çözüm önerisi": (624, 714, 1120, 837),
    "05 Yapay zekânın rolü": (71, 994, 567, 1117),
    "06 Veri ve uygulanabilirlik": (624, 1018, 1120, 1117),
    "07 Beklenen su etkisi": (71, 1298, 567, 1397),
    "08 İlk test": (624, 1274, 1120, 1397),
}
RENK = (0.07, 0.11, 0.17)
PAY = 6  # kutu içi kenar boşluğu


def _yaz(sayfa, rect, metin, font, boyut_max=14.0, boyut_min=9.0):
    """Metni kutuya sığan en büyük punto ile yazar; sığmazsa hata verir."""
    boyut = boyut_max
    while boyut >= boyut_min:
        kalan = sayfa.insert_textbox(rect, metin, fontname=font, fontsize=boyut, color=RENK,
                                     lineheight=1.25, overlay=True)
        if kalan >= 0:
            return boyut
        boyut -= 0.25
    raise ValueError(f"Metin kutuya sığmadı: {metin[:40]}…")


def main():
    doc = pymupdf.open(GIRDI)
    s = doc[0]
    s.insert_font(fontname="sg", fontfile=str(FONT))
    s.insert_font(fontname="sgb", fontfile=str(FONT_B))

    puntolar = {}
    for baslik, (x0, y0, x1, y1) in KUTU.items():
        r = pymupdf.Rect(x0 + PAY, y0 + PAY, x1 - PAY, y1 - PAY)
        # insert_textbox sığmayınca da çizebildiği için önce kopyada dene
        deneme = pymupdf.open(GIRDI)
        ds = deneme[0]
        ds.insert_font(fontname="sg", fontfile=str(FONT))
        puntolar[baslik] = _yaz(ds, r, METIN[baslik], "sg")
        deneme.close()
    # Tüm kutularda aynı punto: en küçüğü
    punto = min(puntolar.values())
    for baslik, (x0, y0, x1, y1) in KUTU.items():
        r = pymupdf.Rect(x0 + PAY, y0 + PAY, x1 - PAY, y1 - PAY)
        assert s.insert_textbox(r, METIN[baslik], fontname="sg", fontsize=punto, color=RENK,
                                lineheight=1.25) >= 0

    # Proje adı / takım adı (açık mavi kutular, başlık satırının altı)
    s.insert_text((68, 276), PROJE_ADI, fontname="sgb", fontsize=20, color=RENK)
    if TAKIM_ADI:
        s.insert_text((436, 276), TAKIM_ADI, fontname="sgb", fontsize=20, color=RENK)
    if CALISMA_ALANI:
        s.insert_text((805, 275), CALISMA_ALANI, fontname="sg", fontsize=16, color=RENK)

    # Takım üyeleri: satır y'leri 1·2·3 numaralarıyla hizalı
    for (ad, rol), y in zip(UYELER, (1518, 1542, 1565)):
        if ad:
            s.insert_text((92, y), ad, fontname="sg", fontsize=13, color=RENK)
        s.insert_text((596, y), rol, fontname="sg", fontsize=13, color=RENK)

    doc.save(CIKTI, garbage=3, deflate=True)
    print(f"PDF: {CIKTI.relative_to(KOK)} (punto {punto:g})")

    satirlar = [
        "# Proje Fikri Kanvası — Florify",
        "",
        "`prototip/kanvas_doldur.py` tarafından üretildi; metni orada düzenleyin. "
        "PDF: `kaynaklar/hackathon/proje_fikri_kanvasi_dolu.pdf`.",
        "",
        f"**Proje adı:** {PROJE_ADI} · **Takım adı:** {TAKIM_ADI or '[doldurulacak]'} · "
        f"**Çalışma alanı:** {CALISMA_ALANI or '[doldurulacak]'}",
        "",
    ]
    for baslik in KUTU:
        satirlar += [f"## {baslik}", "", METIN[baslik], ""]
    satirlar += ["## Takım üyeleri", "", "| # | Ad soyad | Rol |", "|---|---|---|"]
    for i, (ad, rol) in enumerate(UYELER, 1):
        satirlar.append(f"| {i} | {ad or '[doldurulacak]'} | {rol} |")
    MD.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print(f"MD:  {MD.relative_to(KOK)}")


if __name__ == "__main__":
    main()
