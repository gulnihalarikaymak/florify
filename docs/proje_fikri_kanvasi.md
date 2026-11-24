# Proje Fikri Kanvası — Florify

`prototip/kanvas_doldur.py` tarafından üretildi; metni orada düzenleyin. PDF: `kaynaklar/hackathon/proje_fikri_kanvasi_dolu.pdf`.

**Proje adı:** Florify · **Takım adı:** Petrichor · **Çalışma alanı:** Kent — park ve peyzaj sulaması

## 01 Problem

Parklardaki çim, yazın en çok su isteyen bitki örtüsü. Ankara'da 1 m² çimi bir yıl sulamak yaklaşık 1.190 litre su gerektiriyor (bizim hesabımız). İzmir'in 11 merkez ilçesinde parklar ve mezarlıklar 2023'te 8,4 milyon m³ şebeke suyu kullandı (İZSU'nun açık fatura verisi). Bu, yaklaşık 46 bin hanenin bir yıllık suyu.

## 02 Hedef kullanıcı ve ihtiyaç

Belediyelerin park ve bahçe birimleri. Ekim 2025'te çıkan Cumhurbaşkanı Kararı 10502, belediyelerden çim alanlarını azaltmalarını ve her yıl peyzaj ve su verisi raporlamalarını istiyor. Ama hangi parkta çimin yerine ne dikerlerse ne kadar su ve para kazanacaklarını hesaplayacak pratik bir araçları yok.

## 03 Mevcut yaklaşım ve eksikliği

Bugün kararlar "kuraklığa dayanıklı bitkiler %20–80 su tasarrufu sağlar" gibi genel ve çoğu yurt dışından gelen rakamlarla veriliyor. Park bazında, hangi bitkiyle kaç m³ kazanılacağı hesaplanmıyor. İzmir'in 10 yıllık fatura verisi, sulamanın kurak ya da yağışlı yıla göre pek değişmediğine işaret ediyor. İklim, bitki, tarife, uydu ve resmi raporu tek yerde birleştiren açık bir araç bulamadık.

## 04 Çözüm önerisi

Belediye çalışanı bir web sayfasına parkın ilini, büyüklüğünü ve bugünkü bitkilerini girer. Araç, parkın bugün yılda ne kadar su istediğini, çimin yerine hangi bitkilerin konabileceğini ve bunun kaç m³ su, kaç TL, kaç hanenin yıllık suyu kadar tasarruf sağlayacağını gösterir. Sonuçlar, kararın her yıl istediği resmi Peyzaj İzleme Formu'na (EK-1) taslak olarak aktarılır.

## 05 Yapay zekânın rolü

Yapay zekâ, uydu görüntülerinden şehirde yazın sulanan yeşil alanları buluyor; park envanteri olmayan belediye de nerede su harcandığını görüyor. İzmir'de bu tahmin, ilçelerin gerçek park faturalarıyla örtüştü (11 ilçede sıralama uyumu 0,85 / 1) ve yalnız ilçe büyüklüğüne bakmaktan daha fazlasını açıkladı. Hackathon'da kendi eğittiğimiz modeli bu yöntemle kıyaslayacağız.

## 06 Veri ve uygulanabilirlik

Yalnız herkese açık ve ücretsiz veri kullanıyoruz: geçmiş ve 2040'lar için iklim verisi, Avrupa Uzay Ajansı'nın uydu görüntüleri ve arazi haritası, Ankara'da yapılmış hakemli bir bitki su ihtiyacı çalışması, İzmir'in açık su faturası verisi ve belediye su tarifeleri. Henüz doğrulamadığımız: iklim verisinin Türkiye'deki meteoroloji istasyonlarıyla ne kadar örtüştüğü.

## 07 Beklenen su etkisi

Örnek: Ankara'da 10.000 m²'lik bir çim parkın 2.000 m²'si çim kalıp geri kalanına kuraklığa dayanıklı bitkiler dikilirse, yıllık sulama suyu yaklaşık 11.900 m³'ten 4.700 m³'e iner: %60 daha az, yaklaşık 40 hanenin bir yıllık suyu (hesap). Takip göstergesi: parkta m² başına yıllık sulama suyu (sayaçtan).

## 08 İlk test

Varsayımımız: hesabımız tasarrufu abartmıyor. ABD'de sayaçla ölçülmüş bir çalışmada tasarrufu %62 hesapladık, ölçülen %76'ydı (temkinliyiz). Hackathon günü iklim verisini Türkiye'deki meteoroloji istasyonlarıyla, uydu yöntemini ikinci bir şehirde (Ankara) sınayacağız; geçme ölçütlerini önceden yazdık. Sonraki adım: bir belediyeyle sayaçlı pilot park.

## Takım üyeleri

| # | Ad soyad | Rol |
|---|---|---|
| 1 | Kader Demircan | Açık veri ve mekânsal veri (uydu, OSM) |
| 2 | Gül Nihal Arıkaymak | Literatür ve makale tablolarının veriye dökülmesi |
| 3 | Recep Altıntaş | Kod, hesap çekirdeği ve proje planı |
