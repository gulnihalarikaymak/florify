# F2 – Streamlit paneli

Durum: çalışıyor (24.11.2026) · Kod: `app/panel.py`

## Çalıştırma
```
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app/panel.py
```
Tarayıcıda http://localhost:8501 adresi açılır.

## Ne yapıyor?
1. **Yer seçimi:** 81 ilden biri seçilir, istenirse ilçe yazılır.
   - Koordinat Open-Meteo Geocoding'den gelir (`src/veri/konum.py`). 81 ilin hepsi test edildi.
   - İklim dönemi seçilebilir: son 5 yıl ya da 1991–2020 normali.
   - Sulama sezonu: Mart–Kasım ya da 12 ay.
2. **Tarife:** Ankara, İzmir ve İstanbul'da doğrulanmış tarife kendiliğinden seçilir. Diğer illerde tarife elle girilir.
3. **Mevcut ve önerilen peyzaj:** İki sekmede düzenlenebilir tablo var. Her satırda bitki, alan, sulama yöntemi ve dikim yoğunluğu (kd) girilir.
   - Bitki listesi: Konca vd. 2026 tablosundaki ~140 tür ve iki genel çim karışımı.
4. **Sonuç kartları:** Mevcut ve önerilen yıllık su (m³), tasarruf (m³ ve %), TL ve hane eşdeğeri.
5. **Grafikler:** Aylık sulama suyu (mevcut ve önerilen), iklim (ET₀ ve efektif yağış). Üzerine gelince değerler görünür.
6. **Bölge tablosu:** Her bölge için L/m² ve m³ değerleri, CSV olarak indirilebilir.
7. **Kontroller ve uyarılar:**
   - Sulanan alan parkın toplam alanını aşarsa hata verir.
   - Öneride yonca/çayır varsa uyarır.
   - Yöntem ve sınırlar bölümünde "hesaptır, ölçüm değildir" notu var.

## Uydu sayfası (`app/pages/2_Uydu_haritasi.py`)
Sol menüden "Uydu haritası" seçilir. İzmir'in 11 merkez ilçesi için önceden hesaplanmış sonuçları gösterir; kaynak: `kaynaklar/veri/uydu_izmir_ilce_2023.csv`, üreten script: `prototip/uydu_izmir.py`.
- **Özet kartlar:** Sulanan yeşil (km²), hesaplanan su, İZSU 2023 faturası, fatura ile uyum (ρ).
- **Grafik ve harita:** İlçe bazında uydu ve fatura karşılaştırması; sulanan yeşil haritası.
- **Senaryo:** İlçe ve dönüştürülecek pay seçilir; mevcut su, dönüşüm sonrası su, TL ve hane eşdeğeri gösterilir (F1 hesap çekirdeğiyle).
- **Atıf:** ESA WorldCover, Copernicus, OSM ve İZSU atıfları sayfanın altında.

## Henüz yok (sonraki aşamalar)
- Uydu analizi şimdilik yalnız İzmir merkez için. Başka il, `prototip/uydu_izmir.py` içindeki bölge ve ilçe listesi değiştirilerek çalıştırılabilir (~6 dk).
- Bitki karışımını kendiliğinden önerme (F3, AI-2)
- Sezon tahmini ve SHAP açıklaması (F4, AI-1)
- 2040 senaryosu (F5)
- Etkileşimli harita (şimdilik statik görsel)
- Belirsizlik bandı (Monte Carlo): sonuçta tek sayı yerine aralık
- Peyzaj İzleme Sistemi raporu (F6)
