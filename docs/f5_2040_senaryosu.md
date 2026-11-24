# F5 – 2040'lar iklim senaryosu

Durum: çalışıyor (24.11.2026) · Kod: `src/veri/projeksiyon.py` · Panel: "2040 senaryosu" sayfası · Testler: `tests/test_projeksiyon.py`

## Soru
İklim değişikliğiyle 2040'larda çim ve kurakçıl peyzaj ne kadar su isteyecek?

## Veri
**Open-Meteo Climate API.** Hesap açmadan erişiliyor; lisansı CC BY 4.0 (CMIP6 ve Open-Meteo'ya atıf). Ücretsiz API ticari olmayan kullanım için.
- **Modeller:** 7 CMIP6 HighResMIP modeli. CMCC-CM2-VHR4, FGOALS-f3-H, HiRAM-SIT-HR, MRI-AGCM3-2-S, EC-Earth3P-HR, MPI-ESM1-2-XR, NICAM16-8S.
- **Senaryo:** Open-Meteo'nun ifadesiyle "CMIP6 içinde RCP8.5'e mümkün olduğunca yakın". Yani **yüksek emisyon, kötümser uç**. Sunumda bunu söylemek gerekiyor.
- **Hazırlık:** Veriler ERA5-Land'e göre doğrusal bias düzeltmeli, ~10 km'ye indirgenmiş.
- **Dönem:** Veri 2050 sonunda bitiyor. "2040'lar" = 2041–2050; taban dönem 1991–2020.

## Yöntem: delta
1. **Oran hesabı.** Her model için ay ay şu oran hesaplanıyor: gelecek dönemin günlük ortalaması / taban dönemin günlük ortalaması. Bu, buharlaşma ihtiyacı (ET₀) ve yağış için ayrı ayrı yapılıyor.
2. **Gözleme uygulama.** Bu oran, gözlenen ERA5 1991–2020 aylık klimatolojisine uygulanıyor. Böylece modellerin mutlak hatası büyük ölçüde siliniyor.
3. **Yağış sınırı.** Kurak aylarda oranın uç değerlere fırlamaması için yağış oranı 0,5–1,5 arasında sınırlanıyor.
4. **Hesap.** Sonuç, F1 hesap çekirdeğine veriliyor. Çim: Kc 0,95, yağmurlama. Kurakçıl: Kc 0,50, damla. Sulama Mart–Kasım.

## Sonuçlar
| | Bugün (1991–2020) | 2040'lar, 7 modelin medyanı | ET₀ değişimi, model aralığı |
|---|---|---|---|
| Ankara çim | 1.193 L/m² | 1.266 (+73 L, +%6) | +%1 ile +%8 (7 modelin 7'si artış) |
| Ankara kurakçıl | 347 L/m² | 373 (+27 L) | |
| İzmir çim | 1.226 L/m² | ~1.350 (+%10) | +%3 ile +%9 (7 modelin 7'si artış) |

- **Ana mesaj:** Ankara'da çimin m² başına artışı, kurakçılınkinin yaklaşık **2,7 katı**. Çimi dönüştürmek bugün su kazandırmanın yanında gelecekteki iklim riskini de azaltıyor.
- **Yağışta modeller ayrışıyor:** −%20 ile +%8 arası. Sonuçtaki belirsizliğin büyük kısmı buradan geliyor.

## Yakalanan hata
İlk sürümde aylık toplamlar "toplam / yıl sayısı" olarak hesaplanıyordu. EC-Earth3P-HR modelinde **2050 yılı yok**. Bu yüzden 9 yılın toplamı 10'a bölünüyor ve model sahte bir **−%9** gösteriyordu.

Oranlar artık günlük ortalamalardan hesaplanıyor; bu hem eksik günleri hem artık yıl farkını çözüyor. Hatanın tekrar etmemesi için bir test eklendi (`test_eksik_gunler_orani_bozmaz`).

## Sınırlar
- **Senaryo kötümser.** Yüksek emisyon senaryosu; düşük emisyon senaryosu bu API'de yok.
- **Sabit tutulanlar:** Bitki katsayıları (Kc), sulama randımanı ve sezon uzunluğu değişmiyor. CO₂'nin bitki su kullanımına etkisi hesaba katılmadı.
- **Tek nokta:** İl merkezinin koordinatı kullanılıyor.
- **Literatürle uyum:** Orta Anadolu için yüzyıl sonunda ET'de +%11 (RCP4.5) ile +%19 (RCP8.5) artış bildirilmiş (Azlak & Şaylan 2024). 2040'lar için bulduğumuz +%6 bununla aynı yönde ve daha küçük.
