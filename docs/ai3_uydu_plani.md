# AI-3 – Uydudan sulanan kentsel yeşil (sadeleştirilmiş)

Güncelleme: 24.11.2026 · Script: `prototip/uydu_izmir.py` · Sonuç: `prototip/cikti/uydu_izmir_sonuc.json`

## Basitçe ne yapıyor?
Şehri 10×10 m'lik karelere bölüyoruz. Bir kare şu üç koşulu birden sağlıyorsa onu **"sulanan yeşil"** sayıyoruz:
1. **Kentsel alanda.** Çevresindeki 250 m'nin %40'ından fazlası bina. Şehir dışındaki tarlalar ve meralar böylece hesaba girmiyor.
2. **Ağaç ya da su değil.** Bunu ESA WorldCover haritasından alıyoruz. ESA bu haritayı tüm dünya için yapay zekâyla üretmiş.
3. **Ağustos'ta yeşil.** 2023 yazının Sentinel-2 görüntülerinde NDVI > 0,5. İzmir'de yazın yağmur yağmadığına göre yeşil kalan alan sulanıyor.

Kareler sayılınca ilçe başına sulanan yeşil m²'si çıkıyor. Bu m² hesap çekirdeğiyle çarpılınca yıllık m³ elde ediliyor.

Elle etiketleme ve kendi modelimizi eğitmek gerekmedi. Önceki planı bu sadeleştirilmiş yöntemle değiştirdik.

## Sonuç: İzmir'in 11 merkez ilçesi, 2023
Uydunun bulduğu alanı İZSU'nun gerçek park ve mezarlık sulama faturalarıyla karşılaştırdık:

| Ölçüt | Değer |
|---|---|
| Sulanan kentsel yeşil, toplam | 3,38 km² |
| Bu alanın hesaplanan ihtiyacı (çim, 1.378 L/m²) | ~4,7 milyon m³ |
| İZSU faturası, aynı ilçeler | 8,4 milyon m³ (mezarlıklar, ağaç ve çalı sulaması, fazla sulama ve kış tüketimi dahil) |
| İlçe sıralaması uyumu (Spearman ρ) | **0,85** (p = 0,001) |
| Yalnız kentsel alan büyüklüğüyle uyum | 0,73 |
| **Kentsel alan sabit tutulunca** (kısmi ρ) | **0,70** (p = 0,015) |

**Ne anlama geliyor?**
- **Uydunun bulduğu sulanan alan, gerçek sulama faturalarıyla uyumlu.** Uydu ve İZSU birbirinden tamamen bağımsız iki kaynak.
- **Uyum ilçe büyüklüğünden gelmiyor.** Büyük ilçe hem daha çok park hem daha yüksek fatura demek olabilir. Ama büyüklüğün etkisi çıkarıldığında da ilişki sürüyor (0,70). Yani uydu gerçekten bilgi ekliyor.
- **Hacimler aynı mertebede.** Hesaplanan ihtiyaç 4,7 milyon m³, fatura 8,4 milyon m³. Aradaki fark beklenen yönde, çünkü faturada mezarlıklar ve fazla sulama da var.

## Denediğimiz her şey (seçici raporlama yok)
| Kural | ρ | Not |
|---|---|---|
| A) WorldCover "çim" + Ağustos'ta yeşil | 0,08 | Tarla ve merayı sayıyor, kent parklarını kaçırıyor; WorldCover kent parklarını çoğunlukla "ağaç" ya da "yapı" diye sınıflıyor |
| B) A + yalnız kentsel alan | 0,61 | |
| **C) Kentsel + ağaç/su değil + Ağustos'ta yeşil** | **0,85** | **Kullanılan kural** |

C'yi sonuçları gördükten sonra seçtik. Gerekçesi önceden de belliydi: İZSU aboneleri kent parkları. Üç denemeyi hesaba katan sıkı bir düzeltmeyle (Bonferroni) bile p ≈ 0,003 kalıyor.

## Sınırlar
- **11 ilçe az bir sayı.** Mahalle düzeyinde test, mahalle sınırları bulunursa yapılmalı. İzmir'in açık veri portalında mahalle sınırı yok; OSM'nin sorgu sunucusu da bu sorguda hata verdi.
- **Sulanan çim ile sulanan çalı ayrılamıyor.** İkisi de Ağustos'ta yeşil. Bu yüzden "sulanan yeşil" diyoruz.
- **WorldCover 2021 tarihli.** Doğruluğu yaklaşık %75–80. Ağaç altındaki çim görünmüyor. 1–3 m'lik refüjler 10 m kareye sığmıyor.
- **Eşikleri ayarlamadık.** NDVI 0,5 ve %40 bina oranı ilk denemede seçildi. Başka iller için kontrol edilmeli.

## Ürüne bağlantı (sıradaki adım)
Panelde ilçe seçilince şunlar gösterilecek:
- Sulanan yeşil alan (m²) ve hesaplanan yıllık su (m³, TL).
- Harita katmanı.

"Bu alanın %X'i kurakçıl peyzaja dönerse ne olur" sorusu, F1 hesap çekirdeği ve F4 öneri motoruyla cevaplanacak.

## Lisanslar ve atıf
Hepsi atıf şartıyla serbest. Grafiklerde atıf satırı var.

| Kaynak | Lisans |
|---|---|
| ESA WorldCover 2021 v200 | CC BY 4.0. "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium"; Zanaga vd. 2022, doi:10.5281/zenodo.7254221 |
| Sentinel-2 L2A (Earth Search/AWS) | Copernicus açık lisansı |
| OSM ilçe sınırları | ODbL |
| İZSU | CC BY 4.0 |
