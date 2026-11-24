# Derin Araştırma Raporu (ChatGPT Deep Research, 24.11.2026) ve doğrulama notu

Bu dosyanın asıl metni ChatGPT Deep Research'ten geldi. Metne dokunmadık. Yalnızca iki değişiklik yaptık: alıntı işaretlerini sildik ve kaynakçadaki bir yazar adını düzelttik. Önemli iddiaları 24.11.2026'da birincil kaynaklardan kendimiz kontrol ettik. Sonuçlar aşağıdaki tabloda.

## Doğrulama tablosu

| İddia | Sonuç | Nasıl kontrol edildi |
|---|---|---|
| İZSU tüketim verisinde "Sulama" grubu var | ✅ **Doğru, beklenenden iyi.** "Sulama" grubundaki satırların tamamı `PARKLAR VE MEZARLIKLAR` abone tipi. 2014/01–2024/09 arası, 30 ilçe, mahalle × ay. | CSV indirildi (76 MB) ve satırlar sayıldı |
| İZSU veri tazeliği | ⚠️ Portalda son güncelleme 13.06.2024. Dosyanın içindeki veri **Eylül 2024'e kadar** gidiyor. | Portal sayfası + dosya |
| ASKİ 2026 resmi kurum park suyu: Mart 165,95 / Ekim 192,95 TL/m³; AAT geri kazanım suyu 17,72 | ✅ Doğru. Kasım 2026 değeri 197,04. Fiyatlar KDV hariç, su için KDV %1. | ASKİ 2026 PDF |
| İZSU park ve mezarlık 71,83 TL/m³, kamu parkları için geri kazanım suyu 8,96 TL/m³ (01.06.2026'dan itibaren) | ✅ Doğru | izsu.gov.tr tarife tablosu |
| Open-Meteo Seasonal API ET₀'ı doğrudan veriyor | ✅ Doğru. `et0_fao_evapotranspiration` ve ensemble üyeleri (`_member01`…) geliyor. | API çağrısı (Ankara) |
| Open-Meteo Climate API ET₀ veriyor, 2050'de bitiyor | ✅ Doğru, ama **değişken adı farklı:** `et0_fao_evapotranspiration_sum`. Raporun ve bizim teknik planın yazdığı `et0_fao_evapotranspiration` adıyla `null` dönüyor. 2051 tarihi "Invalid date" hatası veriyor. | API çağrısı (7 model, 2040 Temmuz) |
| Bandenay vd.: çim Kc 0,92–1,16 / 0,99–1,17 / 1,04–1,52 | ✅ Doğru | Makale özeti (Crossref) |
| Uydu makalesi: Sentinel-2 RGB-NIR+NDVI %96,0; yalnız Sentinel-2 NDVI %77,8; Landsat+ECOSTRESS %98,2 | ✅ Doğru. Rapor bir şeyi atlamış: Landsat 8 RGB-NIR+NDVI termal veri olmadan da %97,3 veriyor. | Makalenin Tablo 1'i |
| Aynı makalenin yazarı "Cooper, R. W." | ❌ **Yanlış.** Doğrusu Coleman, Stavros, Hulley & Parazoo (2020). Kaynakçada düzeltildi. | Crossref |
| ESTRON: Sentinel-2/MODIS + FAO-56 + hava tahmini, hat bazında karar | ✅ Doğru. Sayfada ayrıca "sabit takvime göre %40'a kadar daha az su" yazıyor (beyan). | Ürün sayfası |
| Bursa "Parklar" GeoJSON park verisi | ⚠️ **Abartılı.** Dosyada yalnız 17 turistik park var. Hepsi nokta; alan ve poligon yok, alanlar başlık/adres/resim. Park envanteri olarak işe yaramaz. | GeoJSON indirildi |
| Kadıköy yeşil alan verisi (CC BY 4.0) | ❓ Kontrol edilemedi. Sitenin TLS sertifikası geçersiz. | — |
| Azlak & Şaylan: 1.089 mm → 1.166–1.285 mm; %11 / %19 artış | ✅ Doğru | Makale sayfası |
| Çamalan & Akıl: 190 istasyon | ✅ Doğru. Aylık %59–93 değerlerini kontrol etmedik. | Makale sayfası |
| Siirt ML: RF R²=0,948, XGBoost 0,776 | ✅ Doğru | Özet (Crossref) |
| Napoli 2016, Benson 2025, Volk 2024 (OpenET) | ✅ DOI, başlık ve yazarlar doğru. Rakamları kontrol etmedik. | Crossref |
| Heraklion yüzey sıcaklıkları (30,5 / 37,1 / 39,0 °C) | ❓ **Kaynakçada yok.** Kaynağı belli değil, kullanmayın. | — |
| Antalya park soğutması (Zeğerek Altunbey & Ortaçeşme 2025) | ❓ Kontrol etmedik | — |

## İZSU park ve mezarlık sulaması: ilk bakış

`ORTALAMA_TUKETIM` sütunu satır bazında toplanarak hesaplandı (m³/yıl):

| Yıl | 2014 | 2016 | 2018 | 2020 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| Toplam | 4,85 M | 8,53 M | 11,07 M | 12,11 M | 9,99 M | 9,56 M |

2022 için aylık dağılım: Ocak 0,17 M, Temmuz 1,63 M, Eylül 1,64 M m³. Sulama sinyali açıkça görülüyor.

**Dikkat edilecekler:**
- **Sütunun anlamı belirsiz.** Adı "ortalama". Satırdaki abone sayısıyla çarpınca yılda ~100 milyon m³ çıkıyor, bu İzmir için gerçekçi değil. Satırlar doğrudan toplanınca ~10 milyon m³ çıkıyor, bu daha makul. Kullanmadan önce veri sözlüğünden ya da portaldan kontrol edin.
- Medyada geçen "~5 milyon m³/yıl" uzman beyanı yalnız 2014–2015 düzeyine uyuyor.
- 2014'ten 2018'e iki katına çıkış iklimden değil abone sayısından geliyor. Abone-ay sayısı 9,6 binden 21 bine çıkmış. Modelde abone/alan başına normalize etmek gerekiyor.
- Kapsamda mezarlıklar da var ve sulanan alanın m²'si bilinmiyor. Bu yüzden veri mutlak doğrulama için değil, **mevsimsellik ve yıllar arası iklim tepkisi** için kullanılmalı.
- Lisans: İzmir BB Açık Veri Lisansı, yani CC BY 4.0 (https://acikveri.bizizmir.com/tr/license). Atıf vermek şartıyla kopyalama ve türetme serbest. Ham dosya 76 MB olduğu için repoya koymadık; script indiriyor.

---

## Rapor metni (ChatGPT)


### Yönetici özeti

Bu araştırmada yalnızca doğrudan indirilebilir açık veriler, birincil akademik çalışmalar ve resmi tarife/ürün sayfaları esas alındı. Kullanıcının zaten elinde bulunduğunu belirttiği Konca vd. (2026), Sovocool (2005), WUCOLS, Sapkota vd. (2023), Metin (2020), Ayanoğlu & Demirel (2023), 2024 Kurakçıl Peyzaj Rehberi, 10502 sayılı karar, Saher vd. (2022), İSKİ 2025 tarifesi ve Denizli basın beyanı tekrar özetlenmedi; yalnızca bunları tamamlayan veya ürün tasarımını değiştirecek yeni bulgular öne çıkarıldı.

1. **Türkiye’de bu proje için bulduğum en değerli açık veri İZSU’nun mahalle × ay × abonelik grubu su tüketim veri setidir.** CSV/XLSX doğrudan indirilebiliyor ve veri sözlüğünde `ABONELIK_GRUBU` içinde açıkça “Sulama” kategorisi bulunuyor. Bu, en azından İzmir’de model çıktısının gerçek faturalanmış tüketimle mahalle ve ay ölçeğinde karşılaştırılması için nadir bir fırsat yaratıyor. Portal üst verisi [BEYAN] **13 Haziran 2024**, kaynak dosya üst verisi ise **5 Haziran 2023** son güncellemesini gösteriyor; bu fark ürün içinde veri tazeliği uyarısı olarak gösterilmeli.

2. **Park envanteri için kullanılabilir açık coğrafi veri var, ancak büyükşehirler arasında parçalı.** Bursa’nın “Parklar” veri seti doğrudan GeoJSON olarak, Bursa Açık Veri Lisansı ile yayımlanıyor ve [BEYAN] **20 Mart 2025** tarihli. Kadıköy’de 2023–2025 aktif/pasif yeşil alan miktarları CSV/XLSX olarak, CC BY 4.0 ile indirilebiliyor ve [BEYAN] **11 Ağustos 2026** güncellenmiş. Buna karşılık Ankara’da parkları gösteren kent rehberi/map service bulunsa da araştırmada ham, indirilebilir park/çim alanı envanteri doğrulanamadı; kullanıcı şartına göre bunları “açık veri seti” saymadım.

3. **Akdeniz ikliminde gerçek lizimetre ölçümü, tek bir sabit Kc’nin peyzaj çimi için yeterli olmadığını gösteriyor.** İspanya Akdeniz kıyısında *Agrostis stolonifera* L-93 üzerinde [ÖLÇÜM] yaz Kc’si kontrol lysimetresinde **0,92–1,16**, organik madde ilaveli lysimetrede **0,99–1,17**, hidrojel uygulamasında **1,04–1,52** olarak ölçüldü. ETa su bilançosundan, ET₀ FAO-56 Penman–Monteith ile hesaplandı ve çalışma Kc’yi günlük/aylık/yıllık verdi. Bu, uygulamanızda “tür Kc’si” yanında toprak/ortam ve sezon parametresinin tutulmasını güçlü biçimde destekliyor.

4. **Aranan listedeki lavanta, biberiye, adaçayı, kekik, Achillea, Stipa, Sedum, ardıç, şimşir ve Cotoneaster için Akdeniz koşullarında orijinal makaleden doğrulanmış aylık Kc serileri şaşırtıcı biçimde seyrek.** İkincil tablolarda biberiye Kc değerleri bulunsa da orijinal deneyi doğrulamadan rapora sayı taşımadım. Türk belediyelerinde kurakçıl dönüşüm öncesi/sonrası sayaçlı, yöntemi yayımlanmış bir çalışma da bu taramada bulunamadı. Bu boşluk, projeniz için bir zayıflıktan çok önemli bir veri-toplama ve pilot saha fırsatı.

5. **Open-Meteo Seasonal API artık ET₀’ı doğrudan veriyor.** Resmi dokümantasyonda SEAS5 için [HESAP/MODEL] **36 km**, **51 ensemble üyesi** ve doküman sayfasında **7 aya kadar** mevsimsel öngörü belirtiliyor; `et0_fao_evapotranspiration`, yağış, bağıl nem, çiy noktası, rüzgâr vb. değişkenler API’den alınabiliyor. Ancak veri bias-corrected değil; Open-Meteo açıkça lokal mutlak değer yerine anomali/alan tahmini olarak yorumlanmasını öneriyor. Bu nedenle ayrı bir “LSTM ile geleceğin hava durumunu üretmek” yerine, ilk ürün sürümünde SEAS5 ensemble + lokal bias correction daha savunulabilir bir yaklaşım.

6. **Türkiye için SEAS5 umut verici ama “klimatolojiyi geçti” sonucu henüz gösterilmiş değil.** Çamalan & Akıl’ın Türkiye’de [HESAP/MODEL] **190 istasyon** ve SPEI-3 ile 2024 doğrulamasında aylık genel tutarlılık yaklaşık **%59–93** aralığında değişti; özellikle Ekim zayıftı. Ancak çalışma gerçek bir climatology/persistence benchmark ile skill score karşılaştırması yapmıyor. Dolayısıyla hackathon sunumunda “AI klimatolojiden daha iyi tahmin ediyor” iddiası şu anda savunulamaz; bunu kendi hindcast deneyinizle ölçmeniz gerekir.

7. **Uydu ile “sulanıyor mu?” tespiti yapılabilir; fakat NDVI tek başına yeterli değil.** Güney Kaliforniya’daki Akdeniz/yarı kurak kentsel çalışma [HESAP/MODEL] Sentinel-2 RGB-NIR+NDVI ile **%96,0**, Landsat + termal ECOSTRESS birleşimiyle **%98,2** doğrulama başarısı buldu; yalnızca Sentinel-2 yaz NDVI yaklaşımı ise [HESAP/MODEL] yaklaşık **%77,8** düzeyinde kaldı. Sentinel-2’nin **10 m**, Landsat’ın **30 m** pikseli dar refüjleri ve küçük çim adalarını karıştırabilir. Dolayısıyla uydu modülü park ölçeğinde güçlü, 1–3 m genişliğindeki refüjlerde ise belediye CBS sınırları veya daha yüksek çözünürlük gerekiyor.

8. **Türkiye’de doğrudan rakip sayılabilecek bir ürün var: ESTRON.** Şirketin belediye ürün sayfası [BEYAN] Sentinel-2/MODIS, NDVI, toprak nemi, hava tahmini, FAO-56 su ihtiyacı, sulama geçmişi ve hat bazında günlük karar motorunu aynı platformda sunduğunu belirtiyor. Bu nedenle farklılaşma cümleniz yalnızca “FAO-56 + AI + uydu” olamaz. Daha güçlü ayrışma: **mevcut çim ↔ alternatif bitki karışımı senaryo karşılaştırması, m³/TL tasarruf, açık Kc kaynak izlenebilirliği, çok-amaçlı bitki optimizasyonu, iklim değişikliği senaryosu ve belediye açık verisiyle doğrulama** olmalıdır.

9. **Su fiyatı ekonomik iş değerini çok büyütüyor; geri kazanılmış su ise optimizasyonu değiştirebilir.** ASKİ’nin 2026 tarifesinin Ekim sütununda resmi kurum park ve bahçe suyu [BEYAN] **192,95 TL/m³**, AAT geri kazanım suyu [BEYAN] **17,72 TL/m³**; İZSU’da 1 Haziran 2026’dan itibaren park/mezarlık suyu [BEYAN] **71,83 TL/m³**, kamu parklarında geri kazanım suyu [BEYAN] **8,96 TL/m³** ve fiyatlar KDV hariç. Bu nedenle “en az su isteyen bitki” her zaman “en düşük TL maliyeti” veren çözüm değildir; su kaynağı türü optimizasyona girdi olmalıdır.

10. **Çimi tamamen kaldırmak termal açıdan risksiz değildir; ağaç gölgelemesi tasarım değişkeni olmalı.** Floransa’da ağaç gölgesi [ÖLÇÜM] asfalt yüzey sıcaklığını **13,8–22,8°C**, çimi **6,9–9,4°C** düşürdü. Heraklion’da bitkilendirilmiş yüzeyler yaz sabahında [ÖLÇÜM] yaklaşık **30,5°C** iken çakıl/kuru toprak gibi yüzeyler çok daha sıcaktı; Fort Collins’te xeriscape bahçeler sabahları [ÖLÇÜM] çimden yaklaşık **1,5°C** daha sıcak, her **%10** ilave ağaç örtüsü ise [ÖLÇÜM] ortalama radyant sıcaklıkta yaklaşık **1°C** düşüşle ilişkiliydi. Bu nedenle öneri motoru yalnız suyu değil, “minimum ağaç gölge oranı / maksimum çıplak-mineral yüzey” gibi ısı kısıtlarını da dikkate almalı.

### Türkiye’de açık veri

#### Bulgular

En güçlü veri seti İZSU’ya ait “Yıllık İlçe ve Mahalle Bazlı Su Tüketim Miktarları”. Veri doğrudan CSV ve XLSX olarak indirilebiliyor; yıl, ay, ilçe, mahalle, abonelik grubu, abonelik türü, abone tipi, abone adedi ve ortalama tüketim alanları var. Özellikle veri sözlüğünde `ABONELIK_GRUBU` için “**Sulama**, Sanayi, Konut/Dışı vb.” ifadesinin resmi olarak yer alması önemli. Bu, sulama tüketimini konut/işyeri tüketiminden ayırma ihtimalini doğrudan destekliyor. Bununla birlikte kaynak dosya üst verisi [BEYAN] **5 Haziran 2023**, veri seti sayfasının üst verisi [BEYAN] **13 Haziran 2024** olduğu için dosyanın fiilen hangi döneme kadar gözlem içerdiği indirilip kontrol edilmeden “2024’e kadar güncel” denmemeli.

Bursa’da “Parklar” veri seti doğrudan GeoJSON biçiminde indirilebiliyor; Bursa Açık Veri Lisansı taşıyor ve [BEYAN] **20 Mart 2025** tarihinde güncellenmiş. Bu veri sulama miktarı vermiyor, fakat belediye park geometrilerini iklim, uydu ve alan hesabıyla birleştirmek için işlevsel.

Kadıköy Belediyesi’nin “Yeşil Alan Miktarı” veri seti 2023, 2024 ve 2025 yıllarını ayrı CSV/XLSX kaynakları olarak sunuyor; aktif/pasif yeşil alan ile kişi başı yeşil alanı içeriyor. Lisans CC BY 4.0 ve [BEYAN] son güncelleme **11 Ağustos 2026**. Ayrıca aynı Park ve Bahçeler Müdürlüğü altında koordinat içeren “Kadıköy Yeşil Alan” veri seti de katalogda bulunuyor. İlçe ölçeğinde olması, İstanbul geneline doğrudan genellenmesini engelliyor; ancak prototip doğrulama sahası için oldukça uygun.

Ankara’da CBS Başkent/Kent Rehberi içinde park katmanları bulunmasına karşın araştırmada, kullanıcının koşulunu karşılayan yani **ham dosya olarak açıkça indirilebilir** ve park/çim/sulama envanteri niteliğinde bir veri setini doğrulayamadım. Aynı nedenle yalnızca haritada görüntülenebilen veya WMS benzeri servis olarak sunulan katmanları Tablo A’ya almadım. İBB için de bu taramada parkların çim alanı veya sulama tüketimini açıkça indirilebilir biçimde veren, metadata ve lisansı doğrulanmış bir büyükşehir veri seti bulamadım. “Yoktur” demek yerine “bu araştırmada doğrulanamadı” demek daha doğru.

TÜİK ve Tarım ve Orman Bakanlığı açık veri sayfalarında da belediye parkı bazında çim m²’si, park sulama sayacı veya abone-kategorisi bazında belediye peyzaj tüketimini doğrudan indirmeye açan bir veri seti bu araştırmada doğrulanmadı. Bu nedenle kurumdan talep edilebilecek verileri kullanıcı talimatına uygun olarak listeye eklemedim.

#### Tablo A – Açık veri setleri

| Ad | Kurum | Doğrudan link | Kapsam | Format | Lisans | Güncellik | İşimize yarar mı? |
|---|---|---|---|---|---|---|---|
| Yıllık İlçe ve Mahalle Bazlı Su Tüketim Miktarları | İZSU / İzmir BB | https://acikveri.bizizmir.com/tr/dataset/yillik-ilce-ve-mahalle-bazli-su-tuketim-miktarlari | İzmir; yıl × ay × ilçe × mahalle × abonelik grubu; “Sulama” kategorisi var | CSV, XLSX | İzmir BB Açık Veri Lisansı | [BEYAN] Veri seti sayfası 13.06.2024; kaynak dosya 05.06.2023 | **Çok yüksek.** Gerçek tüketimle model doğrulaması için en iyi bulunan kaynak |
| İZSU CSV doğrudan dosya | İZSU | https://openfiles.izmir.bel.tr/309436/docs/izsu-yillik-ilce-mahalle-su-tuketimi.csv | Yukarıdaki veri | CSV | İzmir BB Açık Veri Lisansı | [BEYAN] 05.06.2023 kaynak güncellemesi | **Çok yüksek**; API/ETL için pratik |
| Parklar | Bursa BB | https://acikyesil.bursa.bel.tr/dataset/parklar | Bursa; park coğrafi verisi | GeoJSON | Bursa Açık Veri Lisansı | [BEYAN] 20.03.2025; otomatik güncelleme | **Yüksek.** Uydu/iklim/alan hesabıyla birleştirilebilir |
| Kadıköy Yeşil Alan Miktarı | Kadıköy Belediyesi | https://acikveri.kadikoy.bel.tr/dataset/kadikoy-yesil-alan-miktari | Kadıköy; 2023–2025, aktif/pasif yeşil alan ve kişi başı alan | CSV, XLSX | CC BY 4.0 | [BEYAN] 11.08.2026 | **Yüksek**, fakat yalnız ilçe ölçeğinde |
| Kadıköy Yeşil Alan | Kadıköy Belediyesi | https://acikveri.kadikoy.bel.tr/dataset/?organization=park-ve-bahceler-mudurlugu | Kadıköy; yeşil alan koordinatları | Portalda indirilebilir veri kaynağı | Portal varsayılanı CC BY 4.0 | Güncellik ayrı kaynak sayfasında doğrulanmalı | **Orta-yüksek.** Geometri eşleştirmesi için |

**Projemiz için anlamı.** İlk pilotun İzmir veya Bursa/Kadıköy’de yapılması veri erişimi bakımından Ankara’dan daha kolay görünüyor. İzmir özelinde en değerli doğrulama deneyi, FAO-56 ile mahalle bazında tahmin edilen peyzaj sulama ihtiyacını açık tüketim verisindeki “Sulama” grubuyla aylık karşılaştırmak olur. Burada amaç birebir park sayacı doğrulaması değil, modelin mevsimselliğinin ve büyüklük mertebesinin gerçek faturalama verisiyle tutarlı olup olmadığını test etmektir. Bu, hackathon demosunda salt “hesap makinesi”nden daha güçlü bir doğrulama hikâyesi sağlar.

### Sahada ölçülmüş peyzaj bitkisi su tüketimi ve Kc

#### Doğrulanmış ölçümler

Bandenay, Renau-Pruñonosa, Morell ve Esteller’in İspanya Akdeniz kıyısındaki çalışması, bu araştırmada kullanıcı listesindeki mevcut kaynaklara ek olarak bulunan en doğrudan peyzaj Kc deneyidir. *Agrostis stolonifera* L-93 çimi lysimeter koşullarında yetiştirilmiş; ET₀ FAO Penman–Monteith, ETa su dengesiyle ve Kc = ETa/ET₀ olarak hesaplanmıştır. Yaz aylarında kontrol lysimetresinde [ÖLÇÜM] **Kc 0,92–1,16**, organik madde uygulamasında [ÖLÇÜM] **0,99–1,17**, hidrojel uygulamasında [ÖLÇÜM] **1,04–1,52** bulunmuştur. Çalışmanın özellikle günlük, aylık ve yıllık Kc hesaplaması yapması, aylık katsayı eğrisi gereksiniminize doğrudan karşılık veriyor.

Bu sonuç önemli bir modelleme uyarısı veriyor: aynı çim türü için bile su-tutma ortamı Kc’yi değiştiriyor. Dolayısıyla veritabanınızda `species_kc` tek kolonlu sabit bir sayı yerine en az `species`, `month/season`, `climate_zone`, `measurement_method`, `soil/substrate`, `source`, `confidence` alanları bulunmalı. Bu öneri, ölçümdeki [ÖLÇÜM] **0,92–1,52** aralığının aynı tür/deney ailesinde ortaya çıkmasına dayanıyor.

Cynodon dahil sıcak-mevsim çimlerini lizimetreyle karşılaştıran bir saha çalışmasında *Cynodon dactylon* test edilen sıcak-mevsim türleri arasında en düşük su kullanımı ve yüksek su kullanım etkinliği/drought survival performansı gösterdi; ancak erişilebilen birincil özetten güvenle aktarılabilecek mutlak ET veya aylık Kc rakamı çıkmadığı için kullanıcı kuralına uygun olarak sayısal değer vermiyorum. Bu çalışma DOI **10.1071/FP11244** ile doğrulanmıştır.

Lavanta ve biberiye için Akdeniz saha deneyleri mevcut, fakat bulduğum doğrudan çalışmaların önemli bir kısmı bitki su potansiyeli, fotosentez veya uygulanan sulama miktarını rapor ediyor; gerçek ET/Kc’yi lizimetre/sap-flow ile çıkarmıyor. Örneğin *Rosmarinus officinalis* ve *Lavandula stoechas* üzerinde yaz sulama rejimlerini karşılaştıran çalışma su durumunu ölçüyor ancak doğrudan peyzaj Kc serisi üretmiyor. Bu nedenle Table B’ye Kc olarak alınmadı.

#### Tablo B – Bitki su ihtiyacı / Kc değerleri

| Tür | Kc ya da su tüketimi | İklim / yer | Yöntem etiketi | Kaynak |
|---|---|---|---|---|
| *Agrostis stolonifera* L-93 | Yaz Kc: kontrol **0,92–1,16**; organik madde **0,99–1,17**; hidrojel **1,04–1,52** | İspanya, Akdeniz kıyısı | **[ÖLÇÜM]** Lizimetre su bilançosu; ET₀ FAO-56; günlük/aylık/yıllık Kc | Bandenay vd., 2021, DOI: 10.1002/ird.2544 |
| *Cynodon dactylon* | Test edilen sıcak-mevsim çimleri arasında en düşük su kullanımlarından biri; erişilebilir birincil özetten güvenilir mutlak Kc çıkarılamadı | Sıcak/kurak saha koşulları, Avustralya | **[ÖLÇÜM]** lizimetre; sayı rapora alınmadı | DOI: 10.1071/FP11244 |
| *Rosmarinus officinalis* | Doğrudan ET/Kc yerine su durumu ve sulama uygulaması ölçülmüş; **Kc sayı olarak kullanılmadı** | Akdeniz | **[ÖLÇÜM]**, ancak Kc ölçümü değil | Orijinal saha çalışması |
| *Lavandula stoechas* | Doğrudan ET/Kc yerine su durumu ve sulama uygulaması ölçülmüş; **Kc sayı olarak kullanılmadı** | Akdeniz | **[ÖLÇÜM]**, ancak Kc ölçümü değil | Orijinal saha çalışması |

İkincil derlemelerde biberiye için yaklaşık Kc sayıları bulunuyor, fakat bunların dayandığı orijinal deney bu araştırma içinde yeterli güvenle doğrulanamadı. Kullanıcının “başka kaynağın aktardığı sayıyı orijinalini bulmadan kullanma” kuralı nedeniyle tabloya alınmadılar; durum **“orijinal doğrulanamadı”** olarak kaydedildi.

Türk belediyelerinde kurakçıl dönüşüm öncesi ve sonrası aynı sahada sayaçla ölçülmüş, yöntem/alan/süre açık biçimde yayımlanmış bir çalışma bulamadım. Belediyelerin “%X tasarruf” açıklamalarının önemli bölümü yöntem açıklamadığı için [BEYAN] sınıfına giriyor; kullanıcının elindeki Denizli örneğini bu nedenle yeniden delil olarak kullanmadım.

**Projemiz için anlamı.** Ürün içinde iki veri katmanı ayırmak iyi olur: “**ölçülmüş Kc**” ve “**uzman sınıflaması / türetilmiş Kc**”. Kullanıcı arayüzünde bunlar aynı güven seviyesinde görünmemeli. Ayrıca aylık değer bulunmadığında tek bir yıllık katsayıyı otomatik kullanmak yerine güven aralığı veya “düşük/orta/yüksek güven” etiketi gösterilmesi akademik olarak daha savunulabilir.

### Sulama ihtiyacı tahmininde makine öğrenmesi ve mevsimsel tahmin

#### Open-Meteo ve SEAS5

Open-Meteo Seasonal Forecast API, doğrudan `et0_fao_evapotranspiration` değişkenini destekliyor; ayrıca sıcaklık, bağıl nem, çiy noktası, yağış, rüzgâr ve ilgili diğer meteorolojik bileşenleri veriyor. Resmi doküman [HESAP/MODEL] **36 km** SEAS5 çözünürlüğü, **51 ensemble üyesi** ve dokümantasyon sayfasında **7 aylık** tahmin ufku veriyor. Veriler bias-corrected değil ve Open-Meteo lokal nokta tahmini yerine alan ölçeğinde “normalden sıcak/soğuk/ıslak/kurak” sinyali gibi yorumlamayı öneriyor.

Bu, proje mimarisi açısından önemli bir sadeleştirme: sezonluk ET₀ için sıcaklık/nem/radyasyon/rüzgârı ayrı ayrı ML ile üretip sonra Penman–Monteith uygulamak zorunda değilsiniz. İlk benchmark olarak doğrudan SEAS5 ET₀ kullanılabilir; sonra belediye/stasyon/ERA5-Land geçmişine karşı quantile mapping veya aylık bias correction uygulanabilir. Ancak bu düzeltme, geçmiş hindcast’e out-of-sample uygulanmalıdır; aksi halde skill şişer. Open-Meteo’nun kendisi de ham sezonluk verinin lokal bias taşıyabileceğini açıkça belirtiyor.

Open-Meteo Climate API de `Reference Evapotranspiration (ET₀)`, yağış, sıcaklık, bağıl nem, çiy noktası, rüzgâr ve kısa dalga radyasyonu sağlıyor. Sistem CMIP6 HighResMIP modellerini ERA5-Land’e göre bias-correct edip bölgesel olarak yaklaşık **10 km** çıktı ızgarasına indiriyor; resmi sayfa geçmiş+gelecek veri aralığını [HESAP/MODEL] **1950–2050** olarak tanımlıyor ve **2100’e kadar projeksiyon sunmadığını** açıkça söylüyor. Bu yüzden 2040–2050 risk analizi için uygundur, fakat kullanıcı araştırma sorusundaki 2040–2060 penceresinin son on yılını karşılamaz.

#### Türkiye’de SEAS5 skill

Çamalan & Akıl (2025) Türkiye’de SEAS5’i 2024 yılı için **190 meteoroloji istasyonu** ve 1991–2020 normalleriyle değerlendirdi; SPEI-3 üzerinden kategorik kuraklık doğrulaması yaptı. Çalışmadaki aylık tüm nemlilik sınıfları için tutarlılık [HESAP/MODEL] Ocak **%84**, Şubat **%72**, Mart **%78**, Nisan **%83**, Mayıs **%82**, Haziran **%89**, Temmuz **%83**, Ağustos **%93**, Eylül **%75**, Ekim **%59**, Kasım **%74**, Aralık **%77** düzeyindeydi; Ekim en zayıf ay olarak öne çıkıyor.

Buna rağmen bu sayıları “SEAS5 klimatolojiyi %X geçiyor” şeklinde yorumlamak doğru değil. Çalışma tahmin-anomali + istasyon normali yaklaşımını doğruluyor, fakat aynı tarihler için “yalnız 1991–2020 aylık klimatolojisini kullan” benchmark’ı ile MAE/CRPS/Brier Skill Score karşılaştırması vermiyor. Dolayısıyla kullanıcı sorusunun en kritik alt sorusu olan **“1–3 ay önce klimatolojiyi ne kadar geçiyor?” için Türkiye özelinde güvenilir nicel cevap bulamadım**.

Çalışmanın yöntem ve tartışması ayrıca sıcaklık sinyalinin mevsimsel modellerde yağıştan daha güvenilir olabildiğini; [HESAP/MODEL] **36 km** çözünürlüğün topoğrafya ve konvektif yağışı özellikle İç ve Doğu Anadolu gibi karmaşık alanlarda temsil etmekte sınırlı olduğunu vurguluyor. Bu nedenle park su ihtiyacı tahmininde “tahmin edilen yağış” belirsizliği, ET₀ kadar hatta bazı aylarda daha kritik olabilir.

#### ML literatürü

Siirt için aylık ET₀ kestiriminde yayımlanan güncel bir ML çalışmasında [HESAP/MODEL] Random Forest için **R²=0,948**, XGBoost için **R²=0,776** raporlanıyor. Ancak bu tür çalışma esas olarak meteorolojik girdilerden ET₀ kestirimi/rekonstrüksiyonu yapıyor; 1–3 ay ileri gerçek mevsimsel tahmin problemi değil ve klimatoloji benchmark’ı içermiyor. Bu ayrım hackathon sunumunda özellikle korunmalı. DOI: **10.1007/s11269-025-04460-8**.

Ankara için 2026 tarihli hibrit LSTM + XGBoost çalışması NASA POWER 2001–2024 verisi ve FAO-56 ET₀ üzerinden “climate-driven atmospheric irrigation potential” tahminini ele alıyor; ancak erişilebilir kaynakta kullanıcı sorusunu cevaplayacak biçimde 1–3 aylık hindcast skill’i ve climatology karşılaştırması doğrulanamadı. Bu nedenle metrik uydurmak yerine referans olarak bırakıyorum.

Birçok başka ET₀ ML makalesi günlük veya 1–4 haftalık tahminde iyi R²/RMSE değerleri veriyor, fakat **“aylar önceden tahmin” ile “aynı günün meteorolojisinden ET₀ kestirmek” birbirine karıştırılıyor.** Bu proje için akademik olarak doğru benchmark aşağıdaki problem olmalı: her ayın başında yalnız o tarihe kadar bilinen veriler ve mevsimsel ensemble kullanılarak önümüzdeki 1, 2 ve 3 aylık toplam net sulama ihtiyacı tahmin edilmeli; karşılaştırma ise aynı ayların 1991–2020 klimatolojisi ve persistence baseline’ına karşı yapılmalı.

**Projemiz için anlamı.** En savunulabilir “AI” katmanı, ham hava tahmini üretmekten ziyade **bias correction + ensemble post-processing + yerel hata düzeltme** olabilir. Girdi olarak SEAS5 ensemble ET₀/yağış, geçmiş ERA5/Open-Meteo, ay, topoğrafya, lag’ler; model olarak LightGBM/XGBoost; hedef olarak istasyon/ERA5-Land gerçekleşen aylık ET₀ veya doğrudan net sulama talebi kullanılabilir. Sunulacak temel metrikler MAE/RMSE yanında **skill = 1 − error_model/error_climatology** olmalı. Pozitif skill elde edilmeden “AI klimatolojiyi geçiyor” denmemesi raporun en önemli metodolojik önerilerinden biridir.

### Uydudan sulanan çim ve yeşil alan tespiti

Güney Kaliforniya hava havzasında yapılan çalışma, sulanan ve sulanmayan bitki örtüsünü ayırmak için Sentinel-2, Landsat 8, ECOSTRESS termal verisi ve yüksek çözünürlüklü arazi örtüsünü karşılaştırdı. [HESAP/MODEL] Sentinel-2 RGB-NIR + NDVI sınıflandırması **%96,0**, Landsat 8 RGB-NIR/NDVI + bitki-fraksiyonu ile ağırlıklandırılmış ECOSTRESS LST kombinasyonu **%98,2** doğrulama doğruluğuna ulaştı. Aynı çalışma tüm yöntemlerde [HESAP/MODEL] **%50,4–98,2** gibi geniş bir doğruluk aralığı buldu; bu da NDVI’nın tek başına sensör/season seçiminden çok etkilendiğini gösteriyor.

Çalışmanın önemli operasyonel sonucu, Sentinel-2’nin [HESAP/MODEL] **10 m** optik çözünürlüğünün ve birkaç günlük tekrar süresinin tek-sensörlü kentsel sınıflandırma için güçlü olması; Landsat’ın **30 m** ve ECOSTRESS termal bilginin ise daha güçlü ayrım sağlayabilmesine rağmen mixed-pixel sorununa daha açık olmasıdır. Dar refüjlerde pikselin çim, asfalt ve ağaç gölgesini birlikte görmesi kaçınılmaz olabilir.

OpenET, belediye parkları için metodolojik açıdan güçlü bir örnek olsa da **Türkiye’yi kapsamaz**; sistem alan ölçeğinde [HESAP/MODEL] **30 m** ET üretmek üzere contiguous United States için tasarlanmıştır. Doğrulama çalışmasında **152** in-situ istasyon/çoğunlukla eddy-covariance kule kullanılmış; tarım alanlarında ensemble MAE [HESAP/MODEL] **15,8 mm/ay**, yani gözlenen ortalama ET’nin yaklaşık **%17’si**, mean bias **−5,3 mm/ay** ve **R²=0,90** bulunmuştur. Bu doğruluk seviyeleri Türkiye’de otomatik olarak geçerli kabul edilemez, ancak Landsat-temelli çok-model ET yaklaşımının ulaşabileceği referans seviyeyi gösterir.

FAO WaPOR v3, Türkiye açısından daha doğrudan kullanılabilir. Resmi FAO sayfasına göre Level 1 [HESAP/MODEL] **300 m** çözünürlükte küresel kapsama ve **2018–günümüz** zamansal kapsama sahiptir; Level 2 [HESAP/MODEL] **100 m** çözünürlükte Afrika, Near East ve seçili diğer alanları kapsar. Türkiye’nin en az global Level-1 ürününde olması kesin; ancak belediye parkları ve özellikle refüjler için **300 m çok kaba** kalır. Veri ücretsiz indirilebilir.

MODIS MOD16 küresel ET ürünü de Türkiye’yi kapsar, ancak yaklaşık **500 m** uzamsal ölçekte olduğu için belediye parkı tasarımından çok şehir/bölge su bütçesi ve anomali izlemesine uygundur. SSEBop’un USGS küresel sürümü yaklaşık **1 km** çözünürlükte küresel/dekadal-aylık ET sağlar; buna karşılık Landsat tabanlı yüksek çözünürlüklü SSEBop ürünlerinin bazı resmi sürümleri ABD odaklıdır. Bu ayrımı ürün arayüzünde “global kaba ET” ve “şehir ölçeği özel hesap” olarak yapmak gerekir.

| Ürün / yaklaşım | Türkiye kapsamı | Çözünürlük | Ücretsiz? | Belediye parkı için yorum |
|---|---:|---:|---:|---|
| Sentinel-2 optik/NDVI | Evet | [HESAP/MODEL] 10 m | Evet | **En uygun başlangıç**; büyük park/çim adaları için güçlü, dar refüjde mixed pixel |
| Landsat 8/9 optik + termal | Evet | [HESAP/MODEL] 30 m optik/termal ürün ölçeği | Evet | Sulanmış/sulanmamış ayrımında termal sinyal çok değerli; küçük alanlarda kaba |
| OpenET | **Hayır; CONUS** | [HESAP/MODEL] 30 m | ABD’de açık | Metodoloji örneği, Türkiye veri kaynağı değil |
| FAO WaPOR v3 Level 1 | Evet | [HESAP/MODEL] 300 m | Evet | Şehir/bölge trendi; park/refüj için çoğunlukla çok kaba |
| MODIS MOD16 ET | Evet, global | [HESAP/MODEL] ~500 m | Evet | Bölgesel benchmark, park ölçeği değil |
| SSEBop Global | Evet | [HESAP/MODEL] ~1 km | Evet | Bölgesel su bütçesi, park ölçeği değil |

**Projemiz için anlamı.** En uygulanabilir MVP yolu, park poligonları + Sentinel-2 yaz dönemi NDVI/EVI + sezonlar arası yeşillik sürekliliği + mümkünse Landsat/ECOSTRESS yüzey sıcaklığı kullanarak “muhtemelen sulanan” piksel üretmek. Ardından yalnızca bu maskede FAO-56 talebi hesaplanabilir. Ancak uyduyu gerçek sayaç yerine kullanmamak gerekir: uydu **sulama sinyali** ve ET tahmini sağlar; borudan geçen gerçek m³ için sayaç veya faturalama veri seti hâlâ altın standarttır. Güney Kaliforniya’nın [HESAP/MODEL] **%98,2** sonucu, yüksek çözünürlüklü arazi örtüsü ve termal bilginin birlikte kullanılmasına bağlıdır.

### Mevcut araçlar, rakipler ve optimizasyon boşluğu

EPA WaterSense Water Budget Tool; yerel iklim, peyzaj zonu, bitki kategorisi ve sulama sistemi girdileriyle tahmini peyzaj su ihtiyacını standart yeni yapı yaklaşımıyla karşılaştırıyor. Ancak EPA açıkça aracın **sulama zamanlaması için tasarlanmadığını** ve Version 2.0’ın yalnız ABD ZIP kodlarıyla çalıştığını belirtiyor. Bu, sizin ürününüz için net ayrım yaratıyor: Türkiye coğrafyası, günlük/aylık ihtiyaç, gelecek sezon tahmini ve alternatif bitki karışımı ekonomisi.

California MWELO, yeni ve yenilenen peyzajlarda su bütçesi, bitki türü, sulama verimliliği, yerel iklim, yağmur/gri/geri kazanım suyu gibi bileşenleri mevzuat çerçevesine sokuyor ve WUCOLS ile CIMIS’i referanslıyor. 2025 düzenlemeleriyle yerel kurumların MWELO veya en az onun kadar etkili bir düzenlemeyi uygulaması gerekiyor. Bu bir ürün olmaktan çok düzenleyici hesaplama standardı; sizin avantajınız “uygunluk hesabı” yerine karar desteği ve ekonomik/iklimsel senaryo optimizasyonu olabilir.

WUCOLS’un Landscape Coefficient yaklaşımında `KL = ks × kmc × kd`; yani tür faktörü yanında mikroiklim ve dikim yoğunluğu da hesaba giriyor. Bu, yalnızca tür Kc kullanmanın özellikle çok katmanlı belediye peyzajında eksik olabileceğine dair güçlü bir metodolojik karşılaştırma. Güncel UC açıklaması veri tabanında [BEYAN] **4.100’den fazla bitki grubu** ve **6 California bölgesi** bulunduğunu belirtiyor; bu değerler Türkiye için doğrudan kalibrasyon değildir.

ESTRON belediye ürünü bu araştırmadaki en yakın Türkiye rakibi. Resmi ürün sayfası [BEYAN] Sentinel-2 ve MODIS, NDVI/soil moisture, hava tahmini, FAO-56 su talebi, sulama geçmişi, günlük hat-bazlı karar, sayaç kaydı, LoRaWAN ve SCADA entegrasyonu sunduğunu belirtiyor. Sayfanın kamuya açık içeriğinde ise alternatif peyzaj kompozisyonlarının **m³ + TL karşılaştırması**, kaynakça-izlenebilir Kc kütüphanesi, uzun dönem iklim senaryosu veya matematiksel bitki-karışımı optimizasyonu belgelenmiyor. Bu “yoktur” demek değildir; yalnızca kamuya açık ürün sayfasında doğrulanamadı.

#### Tablo C – Rakip araçlar

| Ad | Ne yapar? | Projenize göre eksik / ayrışma alanı | Link |
|---|---|---|---|
| EPA WaterSense Water Budget Tool | Yerel ET/yağış ve peyzaj zonlarından su bütçesi hesaplar | ABD ZIP koduyla sınırlı; EPA açıkça scheduling aracı olmadığını söylüyor; bitki karışımı optimizasyonu ve Türkiye tarifesi yok | https://www.epa.gov/watersense/water-budget-tool |
| California MWELO | Peyzaj su bütçesi ve verimlilik mevzuatı; WUCOLS/CIMIS ile bağlantılı | Düzenleyici çerçeve; Türkiye verisi, sezon tahmini, TL senaryo optimizasyonu yok | https://www.water.ca.gov/Programs/Water-Use-And-Efficiency/Urban-Water-Use-Efficiency/Model-Water-Efficient-Landscape-Ordinance |
| WUCOLS / Landscape Coefficient | Tür × yoğunluk × mikroiklim ile peyzaj su katsayısı | California uzman sınıflaması; Türkiye’ye özgü saha Kc kalibrasyonu ve ekonomik optimizasyon yok | https://ucanr.edu/sites/oc/files/132534.pdf |
| ESTRON Smart Irrigation for Municipalities | [BEYAN] FAO-56 + uydu + hava tahmini + hat bazında kontrol ve ölçüm | Kamu sayfasında bitki-kompozisyon senaryosu, m³/TL dönüşüm optimizasyonu, climate-change scenario ve açık Kc provenance doğrulanmadı | https://estron.com.tr/en/for-municipalities/ |
| EPA/WaterSense weather-based controller ekosistemi | Hava koşullarına göre sulama zamanını/miktarını ayarlar | Donanım/kontrol odağı; belediye peyzajının yeniden tasarımı ve bitki seçimi değil | https://www.epa.gov/watersense/weather-based-irrigation-controllers |

Bitki karışımı seçimini doğrudan “şu türlerden şu oranları seç, su + maliyet + biyoçeşitlilik + gölge kısıtlarını optimize et” şeklinde doğrusal/tamsayılı programlamayla yapan ve peyzaj sulama bağlamında kullanıcı kriterlerinize açıkça uyan birincil akademik çalışma bu taramada doğrulanamadı. Çok sayıda tarımsal crop-planning optimizasyonu vardır, ancak bunları peyzaj bitki karışımı literatürüymüş gibi sunmak doğru olmaz.

Bu boşluk ürün açısından değerlidir. Bir belediye yatağı için karar değişkenleri `x_i = tür i’nin alan payı` olabilir ve şu kısıtlar uygulanabilir: `Σx_i=1`, minimum yerli tür oranı, maksimum bakım maliyeti, minimum evergreen oranı, minimum ağaç gölge alanı, uygun USDA/iklim zonu, invaziv tür yasağı, yaya görüş üçgeni/yükseklik sınırı. Amaç fonksiyonu örneğin `α·su + β·maliyet + γ·ısı-cezası – δ·biyoçeşitlilik` olabilir. Bu öneri literatürden doğrulanmış bir peyzaj standardı değil, mevcut ürün boşluğundan türetilmiş bir mühendislik tasarımıdır.

**Projemiz için anlamı.** Pitch’te “akıllı sulama sistemi” yerine **“peyzaj dönüşümü karar motoru”** konumlandırması daha ayrıştırıcı. ESTRON benzeri ürünler mevcut peyzajın ne zaman sulanacağını optimize ederken, sizin araç “bu alan bugün çim olmalı mı, hangi karışımla değiştirilirse 10 yıllık su/TL/ısı sonucu ne olur?” sorusuna odaklanabilir.

### İklim değişikliği projeksiyonları ve kentsel sulama etkisi

Azlak & Şaylan (2024), Orta Anadolu’da 1980–2000 referans dönemini HadGEM2-ES ve MPI-ESM-MR RCP4.5/RCP8.5 projeksiyonlarıyla karşılaştırdı ve Penman–Monteith dahil altı ET yöntemini kullandı. Referans bölgesel ortalama ET [HESAP/MODEL] **1.089 mm/yıl**; geleceğe ilişkin altı yöntemin ortalaması HadGEM RCP4.5 için **1.199 mm**, HadGEM RCP8.5 için **1.285 mm**, MPI RCP4.5 için **1.166 mm**, MPI RCP8.5 için **1.248 mm** olarak hesaplandı. Yazarlar yüzyıl sonuna doğru artışı RCP4.5’te [HESAP/MODEL] **%11’e**, RCP8.5’te **%19’a** kadar özetliyor.

Bu çalışma kullanıcı sorusundaki 2040–2060 aralığının tam il-bazlı haritasını vermese de Orta Anadolu için yön sinyalini netleştiriyor: ET talebi yukarı gidiyor. Çalışma gelecek dönemleri **2025–2049**, **2050–2074** ve **2075–2098** olarak ele alıyor; dolayısıyla Ankara/Konya gibi belediyeler için “bugünkü çim tasarımını 20–40 yıl sabit kabul etme” varsayımı riskli.

Büyük Menderes Havzası için CMIP6 tabanlı bir downscaling çalışması SSP2-4.5 altında yıllık yağışta [HESAP/MODEL] yakın dönem 2025–2050 için yaklaşık **−12,2 mm**, 2051–2075 için **−19,6 mm**, geç dönemde **−33,7 mm** değişim bildiriyor. Bu değer tek havza/modelleme zincirine aittir; Türkiye geneline uygulanmamalıdır.

Türkiye/GAP ve Konya için 2026 tarihli yeni CMIP6 ET₀ çalışmalarına da ulaşıldı, ancak erişilebilir birincil sayfalardan kullanıcıya güvenle aktarılabilecek il/bölge bazlı 2040–2060 sayısal ET₀ değişimleri tam olarak doğrulanamadığından rakam uydurulmadı. Bu çalışmalar gelecek iterasyonda tam metin tablo/ek dosya çıkarmaya değer.

Open-Meteo Climate API’nin önemli sınırlaması burada ortaya çıkıyor: resmi API [HESAP/MODEL] **2050’ye kadar** veri sunuyor. Dolayısıyla 2040–2050 belediye risk taraması yapılabilir, fakat “2040–2060” için API tek başına yeterli değildir. 2050 sonrası için tam CMIP6/Euro-CORDEX veri arşivine geçmek gerekir.

Sulama ihtiyacına etkisini doğrudan şu şekilde göstermek daha güvenli: sabit Kc ve sulama randımanı varsayımı altında ET₀ artışı, efektif yağış aynı kalırsa net su talebini yükseltir; yağış da düşerse etki güçlenir. Ancak Orta Anadolu’daki [HESAP/MODEL] **%11–19 ET artışını** doğrudan “park sulaması %11–19 artar” diye çevirmek doğru değildir, çünkü efektif yağış, tür değişimi, CO₂ etkisi, sezon uzunluğu ve sulama verimliliği de sonucu değiştirir.

**Projemiz için anlamı.** Üründe 3 zaman ufku öneriyorum: “bugün”, “2035–2050 iklim stresi”, “mevcut sezon tahmini”. Kullanıcı bir dönüşüm kararını verirken yalnız bu yılın su tasarrufunu değil, iklim değişikliği altında aynı tasarımın gelecekteki su açığını da görebilir. Open-Meteo Climate API ilk iki on yıl için hızlı MVP sağlarken, üretim sürümünde 2050 sonrası CMIP6 ensemble’a geçilmesi gerekir.

### Ödünleşimler, ekonomi, bulunamayanlar ve kaynakça

**Araştırma sorusu 7 — Isı, yüzey sıcaklığı ve ağaçla telafi.** Heraklion’daki küçük bir Akdeniz kent parkının restorasyonunda yerinde yüzey sıcaklığı ölçümleri, bitki örtüsünün yaz sabahında [ÖLÇÜM] ortalama **30,5°C**, kuru çıplak toprağın **37,1°C**, çakılın **39,0°C** olduğunu; öğlen yeşil elemanların [ÖLÇÜM] yaklaşık **33,1°C**, yeşil olmayan yüzeylerin ise **42°C’nin üzerinde** olduğunu gösterdi. Restorasyon öncesi bir yaz öğleninde asfalt [ÖLÇÜM] **49,5°C**, hava sıcaklığı **29,3°C** idi. Bu sonuç çim yerine yalnız mineral mulch/çakıl koymanın “su tasarrufu” açısından iyi, termal konfor açısından kötü olabileceğini gösteriyor.

Antalya’da 2021 yazında **9 parkta** yapılan ölçümlerde, **2 hektardan büyük** parklar çevrelerine göre [ÖLÇÜM] ortalama yaklaşık **1°C** soğutma sağlamış ve etki [ÖLÇÜM] yaklaşık **50 m** mesafeye kadar izlenmiştir. Çalışma park boyutu ile bitki yoğunluğunu temel belirleyiciler arasında buluyor.

Floransa Cascine Parkı’nda 10 ağaç türünün gölgeleme etkisinin saha ölçümlerinde asfalt üzerindeki yüzey sıcaklığı azalması [ÖLÇÜM] **13,8–22,8°C**, çim üzerinde **6,9–9,4°C** olarak ölçüldü. Çimde daha küçük ek gölgeleme etkisinin nedeni zaten evapotranspirasyonla soğuma gerçekleşmesi olarak yorumlandı. Bu, “ağaç + düşük su isteyen yerörtücü” tasarımının termal açıdan “yalnız çim kaldır” yaklaşımından daha dengeli olabileceğine güçlü kanıt sağlar.

Fort Collins’te 32 ön bahçe üzerinde yapılan 2023 yaz ölçümlerinde xeriscape alanlar sabah hava sıcaklığında [ÖLÇÜM] çim bahçelerden yaklaşık **1,5°C** daha sıcaktı; her [ÖLÇÜM] **%10** ek kanopi örtüsü, ortalama radyant sıcaklıkta yaklaşık **1°C** düşüşle ilişkiliydi. Bu çalışma Akdeniz değil yarı-kurak ABD bağlamındadır, ancak su-tasarrufu/ısı ödünleşimini doğrudan ölçmesi bakımından değerlidir.

Toz tutma ve biyoçeşitlilik için Türkiye/Akdeniz kentlerinde “çim kaldırma öncesi-sonrası” şeklinde, kullanıcı talebindeki kadar doğrudan ve sayısal birincil çalışma bu taramada bulunamadı. Genel ağaç/çalı ekosistem hizmeti literatürünü bu boşluğu doldurmak için kullanmadım.

**Araştırma sorusu 8 — 2025–2026 su tarifeleri.** ASKİ’nin resmi 2026 tarife PDF’sinde fiyatlar aylık değişiyor. Ekim 2026 sütununda “Resmi Kurum Park ve Bahçe” ve “Özel Park ve Bahçe” için su bedeli [BEYAN] **192,95 TL/m³**, atıksu **0 TL/m³**; AAT geri kazanım suyu [BEYAN] **17,72 TL/m³**. PDF ayrıca su tarifesinde **%1 KDV** notunu veriyor; tabloda rakamlar KDV hariç. Mart için aynı park tarifesi [BEYAN] **165,95 TL/m³**, dolayısıyla “2026 tarifesi” tek sayı olarak sabitlenmemeli; ürün tarih-geçerli tarife tablosu kullanmalı.

İZSU’nun 1 Haziran 2026’dan itibaren geçerli resmi tarifesinde “Park ve Mezarlık Aboneleri” [BEYAN] **71,83 TL/m³**, atıksu bedeli yok; “Geri Kazanım Suyu Kamuya Ait Park ve Mezarlık Amaçlı Kullanım” [BEYAN] **8,96 TL/m³**. Rakamlar KDV hariç. Bu iki tarifenin farkı, peyzaj dönüşümü yanında su kaynağı dönüşümünü de ekonomik senaryoya eklemeniz gerektiğini gösteriyor.

| İdare | Doğrulanmış 2026 kategori | Birim fiyat | Tarih | Not |
|---|---|---:|---|---|
| ASKİ | Resmi kurum park ve bahçe | **[BEYAN] 192,95 TL/m³** | Ekim 2026 | Atıksu 0; KDV hariç |
| ASKİ | AAT geri kazanım suyu | **[BEYAN] 17,72 TL/m³** | Ekim 2026 | Tarife PDF’sinde ayrı satır |
| İZSU | Park ve mezarlık aboneleri | **[BEYAN] 71,83 TL/m³** | 01.06.2026’dan itibaren | Atıksu yok; KDV hariç |
| İZSU | Geri kazanım suyu – kamu park/mezarlık | **[BEYAN] 8,96 TL/m³** | 01.06.2026’dan itibaren | KDV hariç |
| ASAT | Parka özgü kategori | **Doğrulanamadı** | 2026 | “Resmi daire/belediye” sınıfı var, fakat park sınıfına eşitlemek doğru değil |
| İSKİ | 2026 güncel yeşil alan birim fiyatı | **Bu taramada doğrulanamadı** | 2026 | Kullanıcının elindeki 2025 değerini güncelmiş gibi taşımadım |
| BUSKİ | 2026 park/yeşil alan özel tarife | **Bu taramada doğrulanamadı** | 2026 | Genel tarife sayfası bulunmasına rağmen kategori fiyatı güvenle çıkarılamadı |

ASKİ ile İZSU arasında aynı “park sulama” işi için çok farklı birim maliyet olması, TL tasarrufunun sadece m³ tasarruf × tek ulusal fiyat şeklinde hesaplanamayacağını gösteriyor. Örneğin aynı [HESAP/MODEL] **1.000 m³** azaltım, Ekim 2026 ASKİ park tarifesinde yaklaşık **192.950 TL**, İZSU park tarifesinde yaklaşık **71.830 TL** brüt su bedeli azaltımı anlamına gelir; bunlar KDV ve diğer maliyetler hariç yalnız tarife çarpımıdır.

Türkiye’de kurakçıl dönüşümün **m² başına kurulum maliyeti** ve **yıllık m² bakım maliyeti** için karşılaştırılabilir, yöntem/kalem/yıl bazında açık birincil kaynak bu taramada bulunamadı. Belediye ihalelerinde toplam peyzaj işleri bedeli bulunabilse de sulama altyapısı, toprak, bitki, nakliye, işçilik ve bakım aynı pakette olduğu için doğrudan “xeriscape TL/m²” olarak raporlamak güvenilir olmaz. Bu alanı genel piyasa fiyatıyla doldurmadım.

**Bulunamayanlar / yeterince doğrulanamayanlar**

- Türkiye’de kurakçıl peyzaja dönüştürülmüş belediye parkında dönüşüm öncesi-sonrası aynı sayaçla yayımlanmış, yöntem ve dönem bilgisi açık **ölçülmüş** su tasarrufu.
- *Lolium*, *Poa*, *Festuca arundinacea*, *Zoysia*, lavanta, biberiye, adaçayı, kekik, *Achillea*, *Stipa*, *Sedum*, ardıç, şimşir ve *Cotoneaster* için Türkiye/Akdeniz koşullarında orijinal kaynaktan doğrulanmış **12 aylık Kc dizisi**. Bazı ikincil Kc tabloları bulundu; orijinalleri doğrulanamadığı için sayı aktarılmadı.
- Türkiye için 1–3 ay ileri ET₀/net sulama talebinde LSTM/XGBoost/LightGBM’in **aynı hindcast döneminde klimatoloji baseline’ını** ne kadar geçtiğini veren güçlü bir çalışma.
- Türkiye için SEAS5 ET₀ tahmininin doğrudan istasyon FAO-56 ET₀’a karşı aylık CRPS/MAE skill’i.
- Peyzaj tür karışımını doğrusal/tamsayılı programlamayla doğrudan optimize eden, belediye peyzajı bağlamında birincil akademik çalışma.
- Türkiye/Akdeniz kentlerinde çim kaldırmanın **toz** ve **biyoçeşitlilik** etkisini doğrudan öncesi-sonrası sayısallaştıran saha çalışması.
- Türkiye’de karşılaştırılabilir, güncel ve bileşenleri açık **xeriscape kurulum TL/m² ve bakım TL/m²** veri serisi.
- İSKİ, BUSKİ ve ASAT için Kasım 2026 itibarıyla “park/yeşil alan” adına birebir karşılık gelen, güvenle doğrulanmış özel birim fiyatların tamamı.
- İBB ve Ankara BB için bu taramada, lisans/format/güncelleme metadatası açık **doğrudan indirilebilir çim alanı veya park sulama tüketimi** veri seti.

**Tam kaynakça**

Bandenay, G. L., Renau-Pruñonosa, A., Morell, I. & Esteller, M. V. (2021). *Effects of different amendments (organic matter and hydrogel) on the actual evapotranspiration and crop coefficient of turf grass under field conditions*. Irrigation and Drainage, 70, 293–305. DOI: https://doi.org/10.1002/ird.2544

Çamalan, G. & Akıl, S. (2025). *Evaluation of 2024 Meteorological Drought Forecasts for Türkiye: Using ECMWF SEAS5 Data and the SPEI Index*. Indonesian Journal of Earth Sciences, 5(1), A1559. DOI: https://doi.org/10.52562/injoes.2025.1559

Azlak, M. & Şaylan, L. (2024). *Analysing the impact of climate change on evapotranspiration in a climate-sensitive region: Example of Central Anatolia (Türkiye)*. Soil and Water Research, 19(1), 64–76. DOI: https://doi.org/10.17221/107/2023-SWR

Napoli, M., Massetti, L., Brandani, G., Petralli, M. & Orlandini, S. (2016). *Modeling Tree Shade Effect on Urban Ground Surface Temperature*. Journal of Environmental Quality, 45, 146–156. DOI: https://doi.org/10.2134/jeq2015.02.0097

Benson, A., Eskelson, B. N. I., Warziniack, T. & McHale, M. R. (2025). *From canopy to comfort: The impact of residential landscape choices on thermal dynamics in a semi-arid city*. Urban Forestry & Urban Greening, 128992. DOI: https://doi.org/10.1016/j.ufug.2025.128992

Zeğerek Altunbey, P. & Ortaçeşme, V. (2025). *An investigation on cooling potential of micro scale parks in Antalya (Türkiye)*. Journal of Agriculture Faculty of Ege University, 62(3). https://dergipark.org.tr/en/pub/zfdergi/article/1650830

Volk, J. M., Huntington, J., Melton, F., Allen, R. M., Anderson, M., Fisher, J., Kilic, A., Ruhoff, A., Senay, G. B. et al. (2024). *Assessing the accuracy of OpenET satellite-based evapotranspiration data to support water resource and land management applications*. Nature Water, 2, 193–205. DOI: https://doi.org/10.1038/s44221-023-00181-7

Coleman, R. W., Stavros, N., Hulley, G. & Parazoo, N. (2020). *Comparison of Thermal Infrared-Derived Maps of Irrigated and Non-Irrigated Vegetation in Urban and Non-Urban Areas of Southern California*. Remote Sensing, 12(24), 4102. https://www.mdpi.com/2072-4292/12/24/4102

FAO (2023–2026). *WaPOR v3 data / WaPOR data*. Food and Agriculture Organization of the United Nations. https://www.fao.org/in-action/remote-sensing-for-water-productivity/wapor-data/en

Open-Meteo (erişim: 24 Kasım 2026). *Seasonal Weather Forecast API*. https://open-meteo.com/en/docs/seasonal-forecast-api

Open-Meteo (erişim: 24 Kasım 2026). *Climate API*. https://open-meteo.com/en/docs/climate-api

U.S. EPA WaterSense (erişim: 24 Kasım 2026). *Water Budget Tool*. https://www.epa.gov/watersense/water-budget-tool

California Department of Water Resources (erişim: 24 Kasım 2026). *Model Water Efficient Landscape Ordinance*. https://www.water.ca.gov/Programs/Water-Use-And-Efficiency/Urban-Water-Use-Efficiency/Model-Water-Efficient-Landscape-Ordinance

University of California Agriculture and Natural Resources. *Water Use Classification of Landscape Species / Landscape Coefficient Method*. https://ucanr.edu/sites/oc/files/132534.pdf

ESTRON (erişim: 24 Kasım 2026). *Smart Irrigation for Municipalities and Parks*. https://estron.com.tr/en/for-municipalities/

İZSU (erişim: 24 Kasım 2026). *Yıllık İlçe ve Mahalle Bazlı Su Tüketim Miktarları*. İzmir Büyükşehir Belediyesi Açık Veri Portalı. https://acikveri.bizizmir.com/tr/dataset/yillik-ilce-ve-mahalle-bazli-su-tuketim-miktarlari

İZSU (2026). *Su ve Atık Su Tarifesi*. https://izsu.gov.tr/su-ve-atik-su-tarifesi

ASKİ Genel Müdürlüğü (2026). *2026 Yılında Uygulanan Su ve Atıksu Tarifeleri*. https://www.aski.gov.tr/Yukle/Dosya/YillikTarife/2026.pdf

Bursa Büyükşehir Belediyesi (2025). *Parklar*. Bursa Açık Yeşil Platformu. https://acikyesil.bursa.bel.tr/dataset/parklar

Kadıköy Belediyesi (2026). *Kadıköy Yeşil Alan Miktarı*. Kadıköy Açık Veri Portalı. https://acikveri.kadikoy.bel.tr/dataset/kadikoy-yesil-alan-miktari