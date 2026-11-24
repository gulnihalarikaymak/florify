# Gerçek Veri Araştırması – Görev Dağılımı (2 kişi)

Hazırlanma: 23.11.2026 · Durum: açık

**Kural:** Kimseden veri istemiyoruz: başvuru, e-posta ya da telefon yok. Sadece açıkça yayımlanmış ve kullanma izni olan veriyi kullanıyoruz.

## Neden gerekli?

Şu anki hesabımız (`prototip/sulama_hesabi.py`) fizik tabanlı bir hesap: FAO-56 ET₀ × Kc − efektif yağış. Literatürle uyumlu: Ankara'da çim için bizim hesabımız yılda 1.190 L/m², Konca vd. (2026) 1.140 L/m². Ama Türkiye'deki tasarruf rakamlarının hiçbiri sahada ölçülmüş değil (ayrıntı: `kaynaklar/arastirma_kaynaklari.md`). Gerçek veri iki iş için lazım:

1. **Doğrulama:** Hesabımız gerçek ölçümle tutuyor mu?
2. **AI'ı beslemek:** Gerçek alan büyüklükleri, gerçek park envanteri ve uydudan gözlenen yeşillik.

## Hızlı karar tablosu

| Öncelik | Veri | Kim | Durum |
|---|---|---|---|
| 1 | SNWA sayaç ölçümleri (rapor Tablo 17–18) | B | Elimizde, tabloya dökülecek |
| 2 | Belediye açık veri portallarında park ve sulama verisi | A | Bakılacak. Bir şey çıkmazsa A, B'nin işlerine geçer |
| 3 | OpenStreetMap ile park ve çim alanları (m²) | A | Açık veri (ODbL lisansı) |
| 4 | Sentinel-2 uydu görüntüsünden yaz yeşilliği (NDVI) | A | Açık veri (Copernicus) |
| 5 | Metin (2020) tezindeki sulama çizelgeleri | B | Elimizde |
| 6 | Konca vd. (2026) tablolarından park bazında hesap girdileri | B | Elimizde, açık erişim makale |
| 7 | İklim verisinin bağımsız kaynakla karşılaştırılması | B | Açık veri |

---

## Kişi A – Açık veri portalları ve mekânsal veri

### A0. Bulunanlar (24.11.2026, derin araştırma ile birlikte doğrulandı)
- **İzmir: İZSU mahalle × ay tüketimi.** "Sulama" grubu = park ve mezarlık aboneleri, 2014–2024/09. **İlk iş:** veri sözlüğünden `ORTALAMA_TUKETIM` sütununun anlamını kesinleştir. Satır toplamı mı, abone başına ortalama mı? Ayrıntı: `kaynaklar/arastirma/derin_arastirma_chatgpt_2026-11-24.md`
- Bursa "Parklar": sadece 17 turistik park nokta olarak var, işe yaramaz.
- Kadıköy "Yeşil Alan Miktarı": site sertifika hatası verdi, bakılamadı. Tarayıcıda tekrar dene.
- Ankara, İBB: indirilebilir park/çim verisi bulunamadı. Bunlar için OSM'ye (A2) geç.
- A2'ye **İzmir'i öncelikli ekle.** İZSU verisiyle birleşince en güçlü doğrulama İzmir'de çıkar.

### A1. Belediye açık veri portalları (kalan: Antalya, Konya, Denizli, Manisa; en fazla yarım gün)
Her portalda "park", "yeşil alan", "sulama", "su tüketimi", "abone" ara:
- İBB Açık Veri Portalı
- Ankara BB açık veri
- İzmir BB açık veri
- Diğer büyükşehirler (Antalya, Konya, Bursa, Denizli, Manisa) açık veri portalı varsa
- TÜİK Belediye Su İstatistikleri (park sulaması ayrı kalem olarak var mı?)

Her bulgu için kontrol et:
- **Lisans:** Kullanım izni var mı? Yoksa kullanma.
- **Kapsam:** Hangi il ve yıllar?
- **Ölçüm mü, beyan mı?**

**Hiçbir portalda park sulama verisi çıkmazsa** A2 ve A3'e geç. Bunlar da bitince B'nin listesinden iş al.

### A2. Park ve çim alanları – OpenStreetMap
- Overpass ile Ankara, İzmir ve Denizli'deki `leisure=park`, `landuse=grass`, `landuse=meadow`, `leisure=pitch` poligonlarını ve alanlarını (m²) çek.
- Çıktı: `kaynaklar/veri/park_alanlari_<il>.csv` (osm_id, ad, ilçe, etiket, alan_m2).
- Konca vd.'deki Batıkent (431.600 m²) ve Bademlidere (240.000 m²) değerleriyle karşılaştırarak OSM'nin ne kadar doğru olduğunu kontrol et.

### A3. Uydudan sulanan çim alanı – Sentinel-2 NDVI
> **24.11 güncellemesi:** Bu iş projenin ana AI katmanı oldu. Plan: `docs/ai3_uydu_plani.md`. **Etiketleme gerekmiyor:** yöntem sadeleştirildi (ESA WorldCover + yaz NDVI). İzmir'de sonuç alındı. Kişi A için açık iş: İzmir **mahalle sınırları** için açık kaynak bulmak; testi 11 ilçeden yüzlerce mahalleye çıkarır.
- Temmuz–Ağustos'ta yağış neredeyse sıfır. Bu aylarda yeşil (NDVI yüksek) kalan çim alanları sulanıyor demektir.
- A2'deki park poligonları için yaz NDVI ortalamasını hesapla (Copernicus Browser ya da Google Earth Engine).
- Çıktı: `kaynaklar/veri/park_ndvi_<il>.csv`.
- Bu, AI için iyi bir görev olabilir: uydudan "sulanan çim alanı" tespit edip su ihtiyacını tahmin etmek. Hiçbir belediyeye bir şey sormadan çalışır.

---

## Kişi B – Elimizdeki kaynaklardan veri çıkarmak

### B1. SNWA ölçüm verisi (en önemli iş)
- Dosya: `kaynaklar/makaleler/Sovocool_2005_SNWA_xeriscape.pdf`. Sayaçla ölçülmüş çim ve kurakçıl alan sulaması; elimizdeki tek gerçek ölçüm seti.
- Dikkat: Ek 3 "Raw Data" bölümü verinin kendisi değil, veri tabanının sütun sözlüğü. Ham veri PDF'te yok; raporda tablo olarak verilenlerle yetineceğiz.
- ✅ Yapıldı (24.11): Tablo 18 → `snwa_aylik_olcum.csv`. Tablo 17 (yıllık, s.30) ve Tablo 18 (aylık çim ve kurakçıl uygulama, s.33) değerlerini CSV'ye dök. Çıktı: `kaynaklar/veri/snwa_aylik_olcum.csv`.
- Kullanım: Las Vegas için Open-Meteo'dan ET₀ çekip hesabımızın SNWA'nın ölçtüğü çim sulamasını (yılda ~2.970 mm) yakalayıp yakalamadığına bakacağız.

### B2. Konca vd. (2026) park tabloları
- Dosya: `kaynaklar/makaleler/Konca_Ahmad_Apaydin_2026_Water_Ankara_xeriscape.pdf` (CC BY açık erişim).
- Tablo 3, 4 ve 5: Batıkent ve Bademlidere için bitki grubuna göre aylık ETc (mm/gün) ve yıllık m³.
- Çıktı: `kaynaklar/veri/konca2026_park_aylik.csv`. Kendi hesabımızı aynı alanlar için çalıştırıp karşılaştıracağız.

### B3. Metin (2020) tez çizelgeleri
- Dosya: `kaynaklar/makaleler/Metin_2020_Etimesgut_tez_652598.pdf`, Tablo 4.1 ve 4.2 (s.42–45).
- Not: Bu tezde su ihtiyacı ölçülmemiş; araştırmacı sabit miktarda su vermiş (klasik alana 7 L/gün, kurakçıl alana 2 L/gün). Doğrulama verisi olarak değil, örnek veri olarak kullanılacak.
- Çıktı: `kaynaklar/veri/metin2020_sulama_cizelgesi.csv`

### B4. İklim verisinin kontrolü
- Open-Meteo ET₀ değerini Konca vd. Tablo 2'deki Ankara Temmuz değerleriyle karşılaştır: ortalama sıcaklık 23,4 °C, bağıl nem %48, rüzgar 2,1 m/s.
- MGM'nin sitesinde açıkça yayımlanan il bazlı uzun yıllar normalleriyle (sıcaklık, yağış) aynı karşılaştırmayı yap. Başvuru gerektiren MEVBİS verisini kullanmıyoruz.

---

## Teslim formatı (ikiniz için ortak)

Bulduğunuz her veri için `kaynaklar/veri/VERI_ENVANTERI.md` dosyasına bir satır ekleyin:

| Veri adı | Kaynak | Link | Lisans | Kapsam (yer, yıl) | Ölçüm mü, tahmin mi? | Dosya | Durum |
|---|---|---|---|---|---|---|---|

- **"Ölçüm mü, tahmin mi?" sütunu zorunlu.** Bu projede en çok bu ayrımda hata yaptık. Bakanlık rehberindeki "%33,85" bir hesap hatası çıktı, "%80" ise Arizona verisiydi.
- Lisansı belirsiz veriyi repoya koymayın, sadece linkini yazın.
