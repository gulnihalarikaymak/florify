# Sunuma Kadar Yapılacaklar (Paket 2 — İsteğe Bağlı Güçlendirmeler)

Bu liste, ürünün çalışan çekirdeği (F1–F6 + web arayüzü + 81 il canlı uydu + EK-1 raporu) tamamlandıktan sonra **sunuma kadar vakit kalırsa** yapılacak yüksek etkili güçlendirmeleri içerir.

---

## 1. Uydu Tarafında Çok Mevsimli ML Sınıflandırıcı ve Kıyas (Yüksek Jüri Etkisi)
- **Neden:** Mevcut AI-3 kuralı (ESA WorldCover + kentsel maske + Ağustos NDVI > 0,5) basit, açıklanabilir ve İzmir'de İZSU ile ρ = 0,85 veriyor; ancak teknik bir jüri *"kendi eğittiğiniz bir ML modeli nerede?"* diye sorabilir.
- **Ne yapılacak:**
  - Sentinel-2 ilkbahar + yaz + sonbahar bantları ve indeksleri (NDVI, NDWI, NDBI, mevsimsel ΔNDVI) ile **Random Forest / LightGBM** piksel sınıflandırıcı eğit.
  - Eğitim etiketlerini yalnızca açık veriden (OSM park/çim, orman, tarım, su, yapı poligonları) üret; etiket gürültüsünü temizle.
  - **Kabul ölçütü:** İzmir 11 ilçede mevcut sabit eşik kuralıyla (`ρ = 0,85`, kısmi `0,70`) birebir kıyasla. Geçerse ana katmana al; geçemezse AI-1 gibi dürüstçe raporla (*"basit kuralı geçemedi"*).

## 2. İkinci Şehirde Uydu Doğrulaması (Ankara)
- **Neden:** Uydu kuralının yalnızca İzmir'in kurak Ağustos'una aşırı uyum (overfit) yapmadığını göstermek.
- **Ne yapılacak:**
  - `src/uydu/analiz.py` ile Ankara Batıkent / Etimesgut / Çankaya çevresini çalıştır.
  - Konca vd. (2026) Batıkent Rekreasyon Alanı (431.600 m², çim+çayır ~%77) ve OSM park sınırlarıyla piksel bazında çapraz kontrol yap.

## 3. ERA5 – MGM İstasyon Karşılaştırması (Görev B4)
- **Neden:** ERA5, Las Vegas'ta ET₀'ı ~%20 düşük verdi. Türkiye illerindeki sapma yönü ve büyüklüğü henüz ölçülmedi.
- **Ne yapılacak:**
  - MGM açık 1991–2020 il istasyon normalleriyle (sıcaklık, yağış, mümkünse ET₀) ERA5 1991–2020 ortalamalarını 5–10 farklı iklim bölgesindeki ilde karşılaştır.
  - Sapma oranını belirsizlik modülüne (`src/hesap/belirsizlik.py`) ve sunuma ekle.

## 4. Haritadan Gerçek OSM Parkı Seçimi
- **Neden:** Canlı demoda `10.000 m²` varsayılan sayı girmek yerine gerçek bir belediye parkına (ör. *Batıkent Rekreasyon Alanı*, *Kültürpark*) tıklayıp alanın otomatik dolması anlatımı çok güçlendirir.
- **Ne yapılacak:**
  - Ankara ve İzmir için 10–15 bilinen parkın OSM poligonlarını küçük bir açık GeoJSON dosyasına al (`kaynaklar/veri/ornek_parklar.geojson`).
  - Web panelinde "Örnek park seç" açılır kutusuyla alan + koordinat + mevcut çim tahminini tek tıkla doldur.

## 5. Sunum ve Demo Hazırlığı (F7 — Zorunlu)
- [x] **Proje Fikri Kanvası** (`kaynaklar/hackathon/proje_fikri_kanvasi.pdf`) 8 kutunun son metinleriyle doldurulması.
- [ ] **3 dakikalık canlı demo akışı** (tek akış):
  1. **Uydu Haritası:** İzmir'de İZSU doğrulaması (ρ = 0,85) → bir ilçeye tıkla → canlı Ankara haritasını göster.
  2. **Bitki Önerisi (MILP):** "Dengeli" ayarla gerçek gölge ağacı + çalı karışımı üret → **"Park Hesabına Aktar →"** tıkla.
  3. **Park Hesabı:** P10–P90 belirsizlik bandı + m³/TL/hane + **EK-1 Formu (CB 10502)** çıktısını aç.
  4. **2040 Senaryosu:** 7 CMIP6 modeli (çimin artışı kurakçılın ~2,7 katı) ile kapat.
- [ ] **Demo güvenliği:** Demo günü gösterilecek illerin (Ankara, İzmir, Antalya, Erzurum) ERA5, CMIP6 ve uydu önbelleklerinin `veri_onbellek/` içinde hazır olduğundan emin ol (ağ/rate-limit riski sıfır).
