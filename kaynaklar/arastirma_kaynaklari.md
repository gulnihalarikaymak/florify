# Su Tasarrufu Hackathonu – Bilimsel Dayanak Notları (23.11.2026)

Durum etiketleri: **[TAM METİN]** kaynağın kendisinden okundu · **[ÖZET]** yalnızca özet/kayıt okundu · **[İKİNCİL]** başka belge üzerinden

## 1. Yöntem: su ihtiyacı nasıl hesaplanır
- **[TAM METİN] WUCOLS / Landscape Coefficient Method** – UC Cooperative Extension & California DWR, *A Guide to Estimating Irrigation Water Needs of Landscape Plantings in California*.
  - Formül: `KL = ks × kd × kmc` (tür × yoğunluk × mikroiklim); su ihtiyacı = `ET₀ × KL`
  - Tür katsayısı (ks): Yüksek 0,7–0,9 · Orta 0,4–0,6 · Düşük 0,1–0,3 · Çok düşük <0,1
  - Çim: "Turf crop coefficients range from 0.6 (warm season species) to 0.8 (cool season species)"
  - https://pwds.oc.gov/sites/ocpwocds/files/2021-06/Guide%20to%20Estimating%20Irrigation%20Water%20Needs.pdf

## 2. İklim verisi (ET₀)
- **[TEST EDİLDİ] Open-Meteo Historical API** (ERA5 tabanlı, ücretsiz, anahtarsız), değişken `et0_fao_evapotranspiration` (FAO-56 Penman-Monteith).
  - Ankara 2024: yıllık ET₀ 1.302 mm, yağış 464 mm; Nisan–Eylül ET₀ 991 mm.
  - https://open-meteo.com/en/docs/historical-weather-api

## 2b. EN YAKIN ÇALIŞMA – Ankara, aynı yöntem
- **[TAM METİN – tarayıcıdan] Konca, M., Ahmad, S. & Apaydın, H. (2026). Sustainable Urban Green Spaces: A Comparative Water-Saving Analysis of Xeriscaping in Ankara, Türkiye. *Water* 18(11):1362. doi:10.3390/w18111362** (Ankara Üni. + UNLV, açık erişim)
  - Alanlar: Batıkent (431.600 m²) ve Bademlidere (240.000 m²) rekreasyon alanları.
  - Yöntem: FAO-56 Penman-Monteith + CROPWAT + türe özel Kc; efektif yağış düşülmüş; sulama randımanı damla %90, yağmurlama %70.
  - Mevcut yıllık ihtiyaç: Bademlidere 90.591 m³, Batıkent 185.566 m³. Batıkent'in %77'si çayır + çim.
  - Kurakçıl öneri (Batıkent): 82.835 m³ → **102.731 m³/yıl, %55,4 tasarruf** (≈600 hane).
  - **Yonca çimden fazla su istiyor:** yonca 1,31 m³/m²/yıl, çim 1,14 m³/m²/yıl.
  - Çim karışımı Kc ≈ 0,94–0,96 (Lolium/Poa 1,0, Festuca 0,9); önerilen karışım 0,8 (Cynodon/Zoysia 0,6).
  - Ek tablolarda ~140 türün Kc değeri var: lavanta 0,5, şimşir 0,5, ardıç 0,45–0,5, biberiye/adaçayı 0,6, Achillea/Stipa 0,4, gül 0,9, Betula/Platanus orientalis 1,1. → `veri/konca2026_ankara_kc_tablosu.csv`
  - Yazarların uyarısı: çim tamamen reddedilmemeli, işlevsel alanlarda tutulmalı; yapay çim serinletme sağlamaz.
  - Makale Metin & Koçan'ı da ≈%70 tasarruf diye aktarıyor (bizim düzeltmemizle aynı).
  - Yazarların kendi uyarısı: %55,4 **sahada ölçülmüş değil, senaryo tabanlı hesap** (Batıkent proje alanında 432 → 192 mm/m²).
  - Dosya: `makaleler/Konca_Ahmad_Apaydin_2026_Water_Ankara_xeriscape.pdf`
  - https://www.mdpi.com/2073-4441/18/11/1362

## 3. Ölçülmüş tasarruf kanıtları
- **[TAM METİN] Sovocool, K. (2005). Xeriscape Conversion Study, SNWA (Las Vegas).** Ayrı sayaçlı deney + kontrol grubu.
  - Çim 73,0 gal/ft²/yıl (≈2.970 mm), kurakçıl 17,2 gal/ft²/yıl (≈700 mm) → kurakçıl, çimin %23,6'sı (m² başına ≈%76 tasarruf), p<0,01 (s.30, Tablo 17)
  - Konut toplamında %30 tasarruf; en çok yazın.
  - https://www.snwa.com/assets/pdf/reports-xeriscape.pdf
- **[TAM METİN] Metin, M. Z. (2020). Yüksek lisans tezi, Bartın Üni. (Danışman: N. Koçan), YÖK Tez No 652598.** Dosya: `makaleler/Metin_2020_Etimesgut_tez_652598.pdf`
  - Düzenek (s.37-41): Etimesgut Bağlıca, 09.09.2019–09.07.2020, 2 adet 1 m² alan.
    - Klasik: leylak, yayılıcı ardıç, kasımpatı/karanfil + çim.
    - Kurakçıl: porsuk, 3 mavi çim (Festuca glauca), Cotoneaster, 3 Sedum + volkan tüfü malç.
  - **Su tüketimi ölçülmemiş, sulama miktarı sabit verilmiş** (s.42): klasik alana günde 7 L, kurakçıl alana günde 2 L (ilk hafta 4 L). Kasım–Mart arası sulama yok, Ağustos verisi yok.
  - 10 ay ortalaması: klasik 4,57 L/gün, kurakçıl 1,35 L/gün. 20.800 m² yeşil alana ölçeklenince günde 95.056 L → 28.080 L (s.46).
  - **"%33,85" hatalı:** 4,57 / 1,35 = 3,385 oranı yüzde gibi yazılmış. Gerçek tasarruf 1 − 28.080/95.056 ≈ **%70,5**. Bakanlık rehberi bu hatayı aynen aktarmış.
  - "%85 tüm çim / %20" rakamları bu tezde yok.
- **[TAM METİN] Ayanoğlu, Z. & Demirel, K. (2023). Türkiye Peyzaj Araştırmaları Dergisi 6(2):156-176. doi:10.51552/peyad.1390272**
  - Balıkesir Altıeylül, 322 m² konut bahçesi. **Ölçüm değil, tasarım hesabı** (sulama süresi 102 dk → 55 dk).
  - Su %54, elektrik %36, bakım %64, uygulama maliyeti %5 tasarruf.

- **[TAM METİN] Sapkota, A., Haghverdi, A. vd. (2023). HortScience 58(3):274–285. doi:10.21273/HORTSCI16915-22** – UC Riverside, 2020–21 saha deneyi, 10 yer örtücü, ET₀'ın %24–99'u.
  - Rhagodia, Baccharis 'Starn', Eriogonum %24 ET₀'da kaliteyi korudu; biberiye (Rosmarinus), Ruschia, Eremophila %49 ET₀'da iyi.
  - Dosya: `makaleler/Sapkota_2023_HortScience_groundcover_deficit.pdf`
- **[TAM METİN] UC Riverside (2012) yer örtücü denemesi** – 17 tür + 1 çim, ET₀'ın %60 → %40'ı.
  - Bazı türler (Vinca, Hedera, Baccharis) ET₀'ın %30–40'ı ile yaşıyor (sıcak iklim çimi kadar); Gazania, Potentilla soğuk iklim çimi kadar su istiyor.
  - Önemli cümle: "yer örtücüler genel olarak çimden az su ister" fikri doğru değil → **tür seçimi kritik**.
  - Dosya: `makaleler/UCR_2012_groundcover_su_ihtiyaci.pdf`

### Karşı görüş / ödünleşim (jüri sorabilir)
- **[ÖZET – EurekAlert] Saher, Middel, Stephen & Ahmad (2022). Hydrology (MDPI) 9(6):104. doi:10.3390/hydrology9060104** – Phoenix (ASU)
  - Kurakçıl (xeric) alan, ağaç+çim alana göre ortalama 3°C daha sıcak; en düşük sıcaklık ağaç+çimde.
  - Öneri: "oasis" karışık peyzaj; her kaldırılan çim alanı için yerli/yağmurla beslenen ağaç dikilmeli.
  - Bizim için: model sadece su değil, **gölge/ağaç örtüsünü** de korumalı; yapay çim önerilmemeli.

## 4. Mevzuat ve resmi belgeler
- **[TAM METİN] İSKİ 2025 Su Satış Tarifeleri (01.01.2025, KDV hariç)** – "Yeşil Alanları Sulama" **85,78 TL/m³**; geri dönüşüm suyu 5,61 TL/m³. → Tasarrufu TL'ye çevirmek için. Dosya: `resmi/ISKI_2025_su_satis_tarifeleri.pdf`
- **[TAM METİN – Lexpera] Cumhurbaşkanı Kararı 10502, Kurakçıl Peyzaj Uygulamalarına İlişkin Usul ve Esaslar, RG 18.10.2025/33051**
  - Kapsam: kamusal ve yarı özel açık-yeşil alanlar; yükümlü: "sorumlu idare"
  - Md.3/4: çim alan oranı azaltılır (sayısal eşik yok); su kullanımı ölçüm-izleme sistemiyle kayıt altına alınır
  - Md.5: içme-kullanma suyu şebekesinden peyzaj sulaması yapılmaması esastır
  - Md.6: her yıl Şubat sonuna kadar önceki yılın peyzaj/sulama verileri **Peyzaj İzleme Sistemi**ne girilir
  - Geçici Md.2: çimin zorunlu olduğu spor tesisleri 3 yıl içinde uyum sağlar
  - https://www.lexpera.com.tr/resmi-gazete/metin/kurakcil-peyzaj-uygulamalarina-iliskin-usul-ve-esaslar-karar-sayisi-10502-33051
- **[TAM METİN] Tarım ve Orman Bakanlığı – Kurakçıl Peyzaj Uygulamaları Rehber Dokümanı (2024)**
  - Kısmi uygulamada %20–50 tasarruf (Taner 2010); "%80'e varan" tasarruf (Çilek 2023 – **Arizona State Üni. kampüsü**, Türkiye ölçümü değil)
  - Çim ≈7–10 L/m²/gün; bitki listeleri var ama su katsayısı yok
  - https://www.tarimorman.gov.tr/SYGM/Belgeler/Kurakçıl%20Peyzaj%20Rehber%20Dokümanı/KURAKCIL%20PEYZAJ%20REHBER%20DOKÜMANI.pdf

## 5. Belediye örnekleri (beyan; ölçüm yöntemi belirtilmemiş)
- Manisa BB (Habertürk, 31.12.2025): 28.388 m² kavşak, park ve refüjde yılda 70 bin ton su ve 17 milyon TL bakım tasarrufu
- İzmir ESBAŞ (Bakanlık rehberi): 1 dönümde yıllık 900 ton → 90 ton
- Burdur Bucak (AA 2022): yılda 25 bin ton; Antalya (Milliyet 2021): kavşak/refüjlerde su ve elektrikte %50
- **Denizli BB** (Cumhuriyet, 16.10.2025; Park ve Bahçeler Dai. Bşk. B. N. Çavuşoğlu): Nisan–Eylül 2024 → 2025 park-bahçe sulaması 1.397.357 → 763.216 m³ = **634.141 m³, %45 tasarruf**. 77.264 m² çim kaldırıldı, ~218 bin kurakçıl bitki (biberiye, lavanta, ardıç, zakkum), haftada 6 → 4 gün gece sulama, sensörlü damla. Çim kaldırma + sulama düzeni birlikte değiştiği için etkiler ayrışmıyor.
  - https://www.cumhuriyet.com.tr/cumhuriyet-in-egesi/denizli-buyuksehir-suyu-akilla-koruyor-2444120
- **İzmir** (DHA, 19.11.2025; Prof. Dr. Cenk Küçükyumuk, İzmir Demokrasi Üni.): park-bahçelerde yılda ~5 milyon m³ (orta ölçekli baraj hacmi); kurakçıl + ölçülü sulama ile ~%50 tasarruf mümkün (uzman görüşü).
  - https://www.izmirdesondakika.com.tr/izmirde-park-bahcelerde-yilda-5-milyon-metrekup-su-kullaniliyor

## 6. Çapraz kontrol (kendi hesabımız)
Ankara 2024, Nisan–Eylül ET₀ = 991 mm (183 gün):
- Soğuk iklim çimi (Kc 0,8) → 793 mm ≈ **4,3 L/m²/gün** (Etimesgut ölçümü: 4,57)
- Düşük su ihtiyaçlı bitki (ks 0,25) → 248 mm ≈ **1,35 L/m²/gün** (Etimesgut ölçümü: 1,35)
- Farklı yıl, yağış düşülmedi. Ayrıca tezdeki değerler ölçülmüş bitki ihtiyacı değil, araştırmacının sabit verdiği su. Uyum tesadüf olabilir, doğrulama sayılmaz.

## 7. Derin araştırma ekleri (24.11.2026, doğrulandı)
Ayrıntı ve doğrulama tablosu: `arastirma/derin_arastirma_chatgpt_2026-11-24.md`
- **[ÖLÇÜM] İZSU mahalle × ay su tüketimi.** "Sulama" grubu = `PARKLAR VE MEZARLIKLAR` aboneleri, 2014/01–2024/09, 30 ilçe. Yılda ~10 milyon m³ (2018–2023). Temmuz–Eylül tüketimi Ocak'ın ~10 katı. Faturalanmış gerçek tüketim. Ancak sulanan m² yok ve `ORTALAMA_TUKETIM` sütununun anlamı belirsiz. Türkiye'de bulduğumuz **tek açık sulama ölçümü**.
  - https://acikveri.bizizmir.com/tr/dataset/yillik-ilce-ve-mahalle-bazli-su-tuketim-miktarlari (İzmir BB Açık Veri Lisansı = CC BY 4.0: atıfla kopyalama, değiştirme ve ticari kullanım serbest)
- **[ÖLÇÜM] Bandenay vd. 2021** (Irrigation and Drainage, doi:10.1002/ird.2544). İspanya Akdeniz kıyısında lizimetre. *Agrostis* çiminde yaz Kc'si 0,92–1,16; hidrojelli ortamda 1,52'ye çıkıyor. Çim Kc'sini 0,95 almamızı destekliyor.
- **[HESAP/MODEL] Coleman vd. 2020** (Remote Sensing 12:4102). Los Angeles'ta sulanan/sulanmayan bitki örtüsü ayrımı. Sentinel-2 RGB-NIR+NDVI ile %96,0, yalnız yaz NDVI ile %77,8, Landsat+ECOSTRESS termal ile %98,2. AI-3 için yöntem dayanağı.
- **[HESAP/MODEL] Azlak & Şaylan 2024** (Soil and Water Research, doi:10.17221/107/2023-SWR). Orta Anadolu'da ET 1.089 mm'den 1.166–1.285 mm'ye çıkıyor; yüzyıl sonunda RCP4.5'te +%11'e, RCP8.5'te +%19'a kadar. 2040 sekmesi için.
- **[HESAP/MODEL] Çamalan & Akıl 2025** (InJoES, doi:10.52562/injoes.2025.1559). Türkiye'de SEAS5 doğrulaması, 190 istasyon. **Klimatolojiyle karşılaştırma yapmıyor.** Yani "SEAS5/AI klimatolojiyi geçer" iddiası için Türkiye'de kanıt yok, bunu kendimiz ölçmeliyiz.
- **[ÖLÇÜM] Napoli vd. 2016** (doi:10.2134/jeq2015.02.0097) ve **Benson vd. 2025** (doi:10.1016/j.ufug.2025.128992). Ağaç gölgesi ve kurakçıl bahçede ısı ödünleşimi. Rakamları kontrol etmedik.
- **Tarifeler [BEYAN, resmi]:**
  - ASKİ 2026 resmi kurum park suyu aylık artıyor: Mart 165,95, Ekim 192,95, Kasım 197,04 TL/m³. AAT geri kazanım suyu Ekim'de 17,72 TL/m³.
  - İZSU park ve mezarlık 71,83 TL/m³, geri kazanım suyu (kamu parkları) 8,96 TL/m³ (01.06.2026'dan beri).
  - Tümü KDV hariç. Sonuç: tarife il ve ay bazında parametre olmalı, ayrıca **geri kazanım suyu** seçeneği eklenmeli.
- **Rakip: ESTRON** (estron.com.tr). Belediyelere akıllı sulama sunuyor: Sentinel-2/MODIS, FAO-56, hava tahmini, vana kontrolü; "%40'a kadar" tasarruf beyanı. Mevcut peyzajın **ne zaman** sulanacağına karar veriyor. Bizim farkımız: **çimin yerine ne konmalı** ve bunun m³/TL/ısı sonucu.
- **Rapordaki kullanılmayacak kısımlar:** Heraklion sıcaklıkları (kaynakçada yok). Bursa "Parklar" (17 nokta, park envanteri değil).
