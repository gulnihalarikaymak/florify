# Doğrulama testleri ve sentetik veri planı

Hazırlanma: 24.11.2026 · Script: `prototip/dogrulama_testleri.py` · Grafikler: `prototip/cikti/test1_*.png`, `test2_*.png`

## 1. Gerçek veriyle iki test

### Test 1 – Las Vegas, SNWA sayaç ölçümü (1995–2001)
Veri: Sovocool (2005), Tablo 17–18 → `kaynaklar/veri/snwa_aylik_olcum.csv`. İklim: Open-Meteo/ERA5, 1995–2001.

| | Ölçülen | Bizim hesap |
|---|---|---|
| Çim, yıllık | 2.977 mm | 2.366 mm (Kc 0,95, yağmurlama %70) |
| Kurakçıl, yıllık | 701 mm | 902 mm (Kc 0,50, damla) · 496 mm (Kc 0,30) |
| Tasarruf | **%76** | **%62** (lavanta senaryosu) · %79 (Kc 0,30) |
| Aylık profil uyumu (r) | | çim 0,96 · kurakçıl 0,84 |

**Sonuçlar:**
- **Mevsimsellik çok iyi tutuyor** (r = 0,96).
- **Tasarruf tahminimiz temkinli.** Ölçülen tasarruf %76, bizim lavanta senaryomuz %62 veriyor. Jüriye "abartmıyoruz" diyebiliriz.
- **Çimde ölçüm hesabımızdan %21 yüksek.** Bunun iki nedeni var:
  - ERA5'in yıllık ET₀'ı 1.877 mm. SNWA'nın kendi değeri ~2.290–2.350 mm, yani ERA5 Las Vegas'ta ET₀'ı **~%20 düşük** veriyor. SNWA'nın ET₀'ı kullanılırsa hesap ~3.000 mm çıkıyor ve ölçüme çok yakın. Ama bu düzeltmeyi sonuç görüldükten sonra yaptık, kanıt sayılmaz.
  - Rapor, sakinlerin Mayıs'tan itibaren çimi ihtiyacın üstünde suladığını yazıyor.
- **Kurakçıl için Kc 0,5 Las Vegas'ta yüksek kalıyor.** Oradaki kurakçıl bahçeler seyrek dikilmiş çöl bitkileri. SNWA'nın "0,33 × ET₀" kuralı ölçümü tutturuyor.
- **Yapılacak:** ERA5 ET₀'ı Türkiye'de MGM istasyon değerleriyle karşılaştırmak (görev B4). Ankara'da Konca ile uyum iyiydi (1.190 / 1.140), ama her il için kontrol gerekiyor. Dikim yoğunluğu da (WUCOLS kd) parametre olmalı.

### Test 2 – İzmir, İZSU park ve mezarlık tüketimi (2014/01–2024/09, 129 ay)
Veri: İZSU, "Yıllık İlçe ve Mahalle Bazlı Su Tüketim Miktarları", İzmir Büyükşehir Belediyesi Açık Veri Portalı. Lisans: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.tr). Kaynaktaki "Sulama" grubunu kullandık; satırları ay bazında topladık, abone sayısına göre normalize ettik. Türetilmiş tablo: `prototip/cikti/test2_izsu_aylik.csv`. Abone sayısı 10 yılda ikiye katlandığı için tüketim, o yılın ortalama abone sayısına bölündü.

| Ölçüt | r |
|---|---|
| 12 aylık ortalama profil | **0,89** · 1 ay fatura gecikmesiyle **0,97** |
| 129 ayın tamamı | 0,78 · gecikmeyle 0,85 |
| Aylık sapmalar (mevsimsellik çıkarılmış) | 0,18 |
| Yaz toplamı, yıllar arası (trend çıkarılmış, n = 11) | 0,33 · gecikmeyle 0,22 |

**Sonuçlar:**
- **Türkiye'de gerçek tüketimin mevsimselliğini yakalıyoruz.** Bu, elimizdeki ilk gerçek Türkiye testi.
- **1 ay gecikme bir hipotez.** Sayaç okunduğu ay faturalanıyor, yani okunan su önceki ayın tüketimi. Gecikmeyi sonuca baktıktan sonra denedik; sunumda iki değeri de gösterin.
- **Yıllar arası iklim sapmasını tüketimde göremiyoruz** (r 0,2–0,3, anlamsız). İki şey söylüyor:
  - Belediye kurak ya da serin yıla göre sulamayı ayarlamıyor, sabit takvimle suluyor. Bu, ürünün çözdüğü sorunun gerçek veride görünen kanıtı.
  - AI-1'i İZSU'nun yıllar arası değişimiyle doğrulayamayız.
- **Kışın sulama hesabımız neredeyse sıfır** (%1,5), ama yıllık tüketimin **%10'u** kış aylarında gerçekleşiyor. Olası nedenler: mezarlıklar, süs havuzları, kayıplar ya da kışın da süren sabit sulama. Ayrıştıramıyoruz.
- **2020'den sonra abone başına yaz tüketimi ~%35 düşmüş, iklim bunu açıklamıyor.** Kuraklık önlemleri ya da yönetim kararı olabilir; doğrulanmadı.
- **Mutlak miktarı test edemiyoruz.** Sulanan m² bilinmiyor ve `ORTALAMA_TUKETIM` sütununun anlamı belirsiz.

### Jüriye söylenebilecek dürüst cümle
> "Hesabımız, ABD'deki sayaçlı çalışmada çim ve kurakçıl sulamanın aylık profilini r = 0,96 ile yakalıyor. Tasarrufu %62 tahmin ediyor, ölçülen %76; yani temkinliyiz. Türkiye'de İzmir'in 10 yıllık gerçek park sulama faturasının mevsimselliğini r = 0,89 ile yakalıyor. Aynı veri, belediyelerin kurak yıla göre sulamayı ayarlamadığını da gösteriyor. Çözdüğümüz sorun bu."

---

## 2. Sentetik veri: nasıl ve ne kadar

**Ana ilke:** Hava verisini sentetik üretmeye gerek yok, 35 yıllık gerçek iklim verisi açık. Sentetik veri yalnız gerçek verinin olmadığı iki yerde kullanılacak: **park senaryoları** ve **parametre belirsizliği**.

### 2.1 AI-1 sezon tahmini: sentetik değil, "fizikten etiket"
- **Girdiler gerçek:** ERA5 aylık ET₀, yağış, sıcaklık, toprak nemi.
- **Hedef:** Hesap çekirdeğinin ERA5'ten ürettiği aylık net sulama ihtiyacı (Kc = 1, mm).
- **Boyut:**
  - 81 il merkezi × 1991–2025 × 12 ay ≈ **34.000 satır**. 1, 2 ve 3 ay ufuklarıyla ≈ **100.000 örnek**.
  - Gerekirse Türkiye'yi 0,25° ızgaradan ~300 nokta ile örneklemek ≈ 126.000 satır.
- **Bölme yıl bazında:**
  - Eğitim 1991–2016, ayar 2017–2019, test 2020–2025.
  - Aynı yılın farklı illeri aynı kümede kalmalı; iller aynı yıl birbirine benzediği için aksi bilgi sızdırır.
- **Önemli sınır: SEAS5 geçmiş tahminleri Open-Meteo'da yok.** Servis yalnız 2025-09'dan sonrasını veriyor (test edildi). Bu yüzden:
  - AI-1 30 yıl boyunca **yalnız ERA5 geçmişinden** öğrenecek: geçmiş ayların sapmaları, toprak nemi, mevsim.
  - SEAS5 ile karşılaştırma ancak Eylül 2025'ten bu yana ~14 tahmin başlangıcıyla yapılabilir.
  - 1993–2016 SEAS5 hindcast'leri Copernicus CDS'de açık (CC BY). Ama kayıt gerekiyor; kararı ekip verir.
- **Kıyas (baseline):** klimatoloji (aynı ayın uzun dönem ortalaması) ve persistence (geçen ayın sapması devam eder).

### 2.2 AI-2 karışım optimizasyonu: eğitim verisi gerekmiyor
Doğrusal programlama veriden öğrenmez. Sentetik parklar yalnız **test ve demo** için üretilecek.
- **Üreteç:** Latin hiperküp örneklemesi.

| Değişken | Aralık / dağılım | Dayanak |
|---|---|---|
| İl | 81 il | — |
| Alan | 500–50.000 m², log-düzgün | OSM park alanları gelince onların dağılımı |
| Çim oranı | %30–90 | Konca: Batıkent ve Bademlidere oranları |
| Ağaç örtüsü | %0–40 | — |
| Sert zemin | %5–30 | — |
| Zorunlu çim (oyun alanı) | %0–30 | — |
| Sulama yöntemi | yağmurlama / damla | — |
| Bütçe | — | — |

- **Boyut:** **~2.000 park** (81 il × ~25). İl bazında tasarruf dağılımını göstermeye ve optimizasyonun her durumda çözüm bulduğunu test etmeye yeter.

### 2.3 Belirsizlik: Monte Carlo
Her senaryo için **1.000 çekiliş**. Parametreler:
- Kc: WUCOLS bandı içinde.
- Sulama randımanı: yağmurlama 0,6–0,8, damla 0,85–0,95.
- ET₀ hatası: ±%15 (Las Vegas'ta ERA5 ~%20 düşük çıktı).
- Dikim yoğunluğu (kd).

Panelde tek bir sayı yerine **P10–P90 aralığı** gösterilecek ("yılda 410–620 m³ tasarruf" gibi).

### 2.4 Yapmayacaklarımız
- **Sentetik hava üreten GAN/LSTM.** Gerçek veri varken gerek yok, jüri de sorgular.
- **Formülün çıktısını formülün girdilerinden tahmin eden bir ML modeli.** Böyle bir model yalnızca aritmetiği öğrenir. "AI ne katıyor?" sorusunu cevaplamaz, tersine zayıflatır.
- **Sentetik "ölçülmüş tasarruf" verisi.** Hiçbir yerde gerçek veri gibi sunulmaz.

### 2.5 Etiketleme kuralı
Sentetik her dosyanın adında `_sentetik` geçer ve `kaynak = sentetik` sütunu bulunur. Gerçek ve sentetik veri aynı grafikte aynı renkle gösterilmez.
