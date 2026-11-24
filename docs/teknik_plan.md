# Teknik Plan – Florify

Hazırlanma: 23.11.2026 · Durum: taslak

## 1. Ürün tek cümlede
Belediyenin park/refüj sorumlusu bir alan seçer. Sistem o alanın iklimine göre çimin ne kadar su istediğini, hangi bitki karışımıyla ne kadar tasarruf edilebileceğini (m³, TL, hane eşdeğeri) ve önümüzdeki sezon ile 2040'ta ihtiyacın nasıl değişeceğini gösterir.

## 2. Mimari

```
 Açık veri                      Hesap çekirdeği                 AI katmanları                  Arayüz
 ─────────                      ───────────────                 ─────────────                  ──────
 Open-Meteo arşiv (ERA5) ──┐                                ┌─► (1) Sezon tahmini ──────┐
 Open-Meteo iklim (CMIP6) ─┼─► FAO-56: ET₀ × Kc(ay)         │      + SHAP açıklama      │
 Kc tablosu (Konca+WUCOLS) ┼─►  − efektif yağış        ─────┼─► (2) Bitki karışımı ──────┼─► Streamlit paneli
 OSM park alanları ────────┤    ÷ sulama randımanı          │      optimizasyonu         │   harita + grafik
 İSKİ tarifesi ────────────┘    → m³, TL, hane              └─► (3) Uydudan çim tespiti ─┘   + rapor
                                                                   (zaman kalırsa)
```

## 3. Bileşenler

### 3.1 Veri katmanı – `src/veri/`
| Veri | Kaynak | Not |
|---|---|---|
| Günlük ET₀, yağış, sıcaklık, nem, rüzgar | Open-Meteo Historical API (ERA5) | Çalışıyor, test edildi |
| 2040–2050 iklim senaryosu | Open-Meteo Climate API (CMIP6) | Test edildi (24.11). Değişken adı `et0_fao_evapotranspiration_sum`. 2050'de bitiyor. Modeller arasında büyük fark var (Ankara Temmuz 2040: 7–12 mm/gün), ensemble ortalaması + aralık gösterilecek |
| Mevsimsel tahmin | Open-Meteo Seasonal API (SEAS5) | Test edildi. `et0_fao_evapotranspiration` + 51 üye. Bias düzeltmesi yok, düzeltmeyi biz yapacağız |
| Gerçek sulama tüketimi (doğrulama) | İZSU açık veri: park ve mezarlık aboneleri, mahalle × ay, 2014–2024/09 | Ham dosya repoda değil; script indirip toplar |
| Bitki Kc | `kaynaklar/veri/konca2026_ankara_kc_tablosu.csv` (~140 tür) + WUCOLS sınıfları | Türe aylık Kc eğrisi eklenecek |
| Park/çim alanı | OSM (Kişi A) | `park_alanlari_<il>.csv` |
| Su fiyatı | İSKİ 2025: 85,78 · ASKİ Kasım 2026: 197,04 · İZSU 2026: 71,83 TL/m³ (KDV hariç) | İl ve ay bazında tablo. Geri kazanım suyu ayrı seçenek (ASKİ 17,72, İZSU 8,96) |
| Hane eşdeğeri | Konca vd. (2026) metni: Ankara hanesi 15 m³/ay → 180 m³/hane·yıl | Parametre (`HANE_M3_YIL`) |

Önbellek: API cevapları `veri_onbellek/` klasörüne (git dışı) yazılır, aynı sorgu tekrar çekilmez.

### 3.2 Hesap çekirdeği – `src/hesap/`
Mevcut `prototip/sulama_hesabi.py` modüle dönüşür:
- `et0_al(lat, lon, tarih_araligi)`
- `sulama_ihtiyaci(iklim, karisim, randiman)` → aylık mm ve m³. Karışım: `{tür: alan_m2}`
- `tasarruf(mevcut, oneri, tarife, hane_m3)` → m³, %, TL, hane
- Yenilikler: aylık Kc eğrisi (FAO-56 başlangıç/orta/son dönem), sulama yöntemine göre randıman (yağmurlama %70, damla %90), mevcut alanın sert zemin payı.
- Birim testleri: Konca vd. Batıkent ve Bademlidere sonuçlarını (185.566 ve 90.591 m³/yıl) %10 içinde yeniden üretmeli.

### 3.3 AI katmanı 1 – Sezon tahmini (24.11: BIRAKILDI, yerine son 10 yıl normali)
> Deneme sonucu: LightGBM, son 10 yıl ortalamasından %5–7 kötü (`docs/ai1_deneme_sonucu.md`). Panelde "önümüzdeki sezon" için son 10 yıl normali kullanılacak. Aşağıdaki metin tarihçe için duruyor.

- **Soru:** Önümüzdeki 1–3 ayda bu alanın sulama ihtiyacı ne olacak?
- **Neden basit yöntem yetmez:** Bugün belediyeler "geçen yıl ne kadar suladıysak" ya da uzun yıllar ortalamasıyla planlıyor. Kurak ya da yağışlı yıl sapmasını yakalamıyorlar.
- **Veri:** Türkiye'de ~80 il merkezi × 1990–2025 aylık iklim (Open-Meteo). Hedef: çekirdekten hesaplanan aylık sulama ihtiyacı (mm, Kc = 1).
- **Özellikler:** son 1–6 ayın ET₀/yağış/sıcaklık sapmaları, toprak nemi (ERA5), ay, enlem, rakım, SEAS5 ensemble ET₀ ve yağış (ortalama + yayılım).
- **Not:** SEAS5'in Türkiye'de klimatolojiyi geçtiğini gösteren bir çalışma yok (Çamalan & Akıl 2025 bu karşılaştırmayı yapmıyor). Ölçüt: skill = 1 − hata_model / hata_klimatoloji. Kıyas için ikinci bir baseline daha: persistence (geçen ay aynen devam eder).
- **Gerçek veriyle ikinci test:** İzmir'de İZSU park ve mezarlık tüketiminin yıllar arası sapmasını, modelin öngördüğü ihtiyaç sapmasıyla karşılaştırmak. Abone sayısına göre normalize edilecek.
- **Model:** LightGBM, yıl bazında ayrılmış doğrulama (eğitimde 1990–2018, testte 2019–2025).
- **Başarı ölçütü:** Ortalama mutlak hata, "uzun yıllar ortalaması" tahmininden belirgin şekilde düşük olmalı. Değilse bunu açıkça söyleriz.
- **Açıklanabilirlik:** SHAP. Panelde "bu yaz ihtiyacın %X'i sıcaklık sapmasından, %Y'si kurak bahardan" gibi gösterilir.

### 3.4 AI katmanı 2 – Bitki karışımı optimizasyonu
- **Soru:** Bu alanın işlevini bozmadan en az suyla hangi karışım?
- **Yöntem:** Doğrusal programlama (scipy / PuLP). Amaç: yıllık m³'ü en aza indirmek.
- **Kısıtlar (kullanıcı girer):**
  - Oyun/çim zorunlu alan (m²)
  - En az ağaç/gölge oranı. Phoenix çalışması: kurakçıl alan 3 °C daha sıcak.
  - Bütçe, tür çeşitliliği (en az N tür)
  - Sadece o ilin iklimine uygun türler
- **Kurallar:** Yapay çim önerilmez. Yonca "çim alternatifi" diye sunulmaz: Konca vd.'ne göre çimden fazla su istiyor. Çim türlerinden sıcak iklim çimi (Cynodon, Zoysia; Kc 0,6) öne çıkar.
- **Çıktı:** 2–3 seçenek (en az su / dengeli / en az değişiklik), her biri için m³, TL, hane.

### 3.5 AI katmanı 3 – Uydudan sulanan çim tespiti (24.11: ANA AI KATMANI)
> Ayrıntılı plan ve fizibilite: `docs/ai3_uydu_plani.md`. Sentinel-2 hesapsız erişim çalışıyor; İzmir'de İZSU faturalarıyla bağımsız doğrulama yapılacak.

- Kişi A'nın OSM + Sentinel-2 NDVI çıktısıyla, bir ilçedeki parkların yazın yeşil kalan alanını bulup toplam sulama yükünü tahmin etmek.
- Değeri: Belediyenin elinde envanter olmasa bile "ilçenizde yaklaşık X m² sulanan çim var, yılda Y m³" diyebilmek.

### 3.6 Arayüz – `app/` (Streamlit)
1. İl/ilçe seçimi ve harita (folium), OSM parkları üstünde.
2. Alan girişi: toplam m², mevcut çim/çalı/ağaç/sert zemin oranları; ya da haritadan park seçimi.
3. Sonuç kartları: mevcut yıllık su, öneriyle su, tasarruf (m³, %, TL, hane).
4. Aylık grafik: ET₀, efektif yağış, mevcut ve önerilen sulama.
5. Sekmeler: "Önümüzdeki sezon" (son 10 yıl normali), "2040 senaryosu" (CMIP6), "Önerilen bitkiler" (AI-2), "Uydu haritası" (AI-3).
6. "Peyzaj İzleme Sistemi için özet" düğmesi: CB Kararı 10502 Md.6 kapsamında yıllık raporlamaya yardımcı CSV/PDF.

## 4. Doğrulama planı
| Test | Beklenen | Veri |
|---|---|---|
| Ankara çim yıllık ihtiyacı | ~1.140 L/m² (Konca) | Prototipte 1.190 ✓ |
| Batıkent / Bademlidere toplam | 185.566 / 90.591 m³ ±%10 | Kişi B, B2 |
| Las Vegas çim uygulaması | SNWA ölçümü ~2.970 mm/yıl | Kişi B, B1 |
| AI-1 tahmin hatası | Uzun yıllar ortalamasından düşük | 2019–2025 test yılları |
| İzmir park sulama mevsimselliği | ✓ r = 0,89 (1 ay gecikmeyle 0,97). Yıllar arası uyum yok (r ≈ 0,3) | İZSU açık veri, 2014–2024. Ayrıntı: `docs/dogrulama_ve_sentetik_veri.md` |
| Las Vegas çim ve kurakçıl (yapıldı) | ✓ Profil r = 0,96. Tasarruf: hesap %62, ölçüm %76 (temkinli). Çimde ölçüm hesaptan %21 yüksek (ERA5 ET₀ ~%20 düşük) | SNWA Tablo 17–18 |

## 5. Repo yapısı (hedef)
```
src/veri/      api istemcileri, önbellek
src/hesap/     FAO-56 çekirdeği + testler
src/model/     AI-1 eğitim/tahmin, AI-2 optimizasyon
app/           Streamlit paneli
kaynaklar/     makaleler, resmi belgeler, veri tabloları
docs/          planlar ve notlar
prototip/      ilk deneme (src'ye taşınınca arşiv)
```

## 6. Aşamalar ve öncelik
| Aşama | İş | Olmazsa olmaz mı? |
|---|---|---|
| F1 | ✅ Hesap çekirdeği modülü + aylık Kc + testler (bkz. `docs/f1_hesap_cekirdegi.md`) | Evet |
| F2 | ✅ Streamlit paneli: il seç → alan gir → tasarruf kartları + aylık grafik (bkz. `docs/f2_panel.md`) | Evet |
| F3 | ✅ AI-3 sadeleştirildi: WorldCover + yaz NDVI + kentsel maske, İzmir'de İZSU ile ρ = 0,85 (kısmi 0,70). Bkz. `docs/ai3_uydu_plani.md`. Panelde "Uydu haritası" sayfası var | Evet |
| F4 | ✅ Karışım optimizasyonu (MILP): panelde "Bitki önerisi" sayfası. Bkz. `docs/f4_bitki_onerisi.md` | Evet |
| ~~F4~~ | ~~AI-1 sezon tahmini~~: denendi, bırakıldı | — |
| F5 | ✅ 2040 senaryosu: 7 CMIP6 modeli, delta yöntemi; panelde "2040 senaryosu" sayfası. Bkz. `docs/f5_2040_senaryosu.md` | İyi olur |
| F6 | Peyzaj İzleme raporu, panelde uydu haritası | Zaman kalırsa |
| F7 | Kanvas ve poster doldurma, 3 dk demo senaryosu | Evet |

## 7. Riskler
| Risk | Önlem |
|---|---|
| AI-1, uzun yıllar ortalamasını geçemez | **Gerçekleşti (24.11, 10 il):** model son 10 yıl ortalamasından %5–7 kötü. Bkz. `docs/ai1_deneme_sonucu.md`. AI ağırlığı AI-3 ve AI-2’ye kaymalı |
| Kc değerleri literatürden, sahada ölçülmemiş | Panelde "hesap, ölçüm değil" etiketi; WUCOLS aralığını belirsizlik bandı olarak göster |
| Open-Meteo kesintisi / limit | Demo illeri için veriyi önceden önbelleğe al |
| Kurakçıl peyzajın ısıyı artırması | Ağaç/gölge kısıtı optimizasyonda zorunlu; çıplak çakıl/mineral yüzey için üst sınır |
| Jüri: "ESTRON zaten var" | ESTRON mevcut peyzajın sulama zamanlamasını yapıyor. Biz peyzaj dönüşümüne karar veriyoruz: çimin yerine ne konmalı, sonucu m³/TL/ısı olarak ne olur. İki araç birbirini tamamlar |

## 8. Proje Fikri Kanvası ile eşleşme
| Kanvas alanı | Kısa cevap |
|---|---|
| 01 Problem | Park ve refüjlerde yoğun çim sulaması; İzmir'de yılda ~5 milyon m³, Ankara'da çim yılda ~1.100–1.200 L/m² su istiyor |
| 02 Hedef kullanıcı | Belediye Park ve Bahçeler daireleri; CB Kararı 10502 ile çimi azaltma ve her yıl veri raporlama yükümlülüğü var ama aracı yok |
| 03 Mevcut yaklaşım | Genel "%20–80 tasarruf" rakamları, alan ve tür bazında hesap yok; sabit sulama takvimi |
| 04 Çözüm | Alan seç → mevcut ihtiyaç, önerilen karışım, m³/TL/hane tasarrufu, gelecek sezon ve 2040 |
| 05 AI'ın rolü | ESA'nın yapay zekâ ile üretilmiş arazi haritası + yaz uydu görüntüsü → envanter olmadan sulanan kentsel yeşil ve su yükü (İzmir faturalarıyla doğrulandı, ρ = 0,85) + kısıtlı bitki karışımı optimizasyonu. Sezon tahmini denendi, basit normali geçemedi; dürüstçe raporlanır |
| 06 Veri | Open-Meteo/ERA5, CMIP6, Konca Kc tablosu, OSM, İSKİ tarifesi: hepsi açık |
| 07 Beklenen etki | Gösterge: alan başına yıllık sulama suyu (m³/m²). Ankara örneğinde çim → lavanta %68 daha az |
| 08 İlk test | Varsayım: hesabımız gerçek park ihtiyacını yakalıyor. Test: Konca'nın Batıkent/Bademlidere sonuçlarını ve SNWA ölçümünü yeniden üretmek |
