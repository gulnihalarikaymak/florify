# Ekibe kısa açıklama

**Proje ne?** Belediyeler için bir araç: Bir park ya da refüj seçiliyor. Sistem o şehrin iklimine göre çimin ne kadar su içtiğini, yerine hangi bitkiler konursa ne kadar su ve para tasarruf edileceğini, önümüzdeki sezon ve 2040'ta ihtiyacın nasıl değişeceğini gösteriyor.

**Neden önemli?** Ekim 2025'te çıkan Cumhurbaşkanı Kararı 10502 ile belediyelerin çim alanlarını azaltması ve her yıl sulama verisi raporlaması gerekiyor. Ama "hangi alanda, hangi bitkiyle, ne kadar" sorusunu cevaplayacak araçları yok.

**Ne hazır?**
- Bilimsel dayanak: FAO-56 yöntemi, Ankara'da aynı yöntemle yapılmış hakemli bir makale (Konca vd. 2026, %55 tasarruf), Las Vegas'ta sayaçla ölçülmüş %76 tasarruf. Hepsi `kaynaklar/` klasöründe, özeti `kaynaklar/arastirma_kaynaklari.md` dosyasında.
- Çalışan prototip: Ankara'da çim yılda 1.190 L/m² su istiyor, lavanta 383 L/m² (%68 daha az). Grafik `prototip/cikti/` klasöründe.

**Sizden ne istiyoruz?** Gerçek veri. Ama kimseden istemeden, sadece açık kaynaklardan:
- **Kişi A:** Belediye açık veri portallarında park/sulama verisi var mı bak. Sonra OpenStreetMap'ten park ve çim alanlarını, uydu görüntüsünden yazın yeşil kalan (yani sulanan) alanları çıkar.
- **Kişi B:** Elimizdeki makalelerdeki tabloları (Las Vegas ölçümleri, Ankara parkları, Etimesgut tezi) Excel/CSV'ye dök. Bunlarla hesabımızı doğrulayacağız.

Ayrıntılı görev listesi: `docs/gercek_veri_arastirmasi.md`. Teknik plan: `docs/teknik_plan.md`.

**Tek kural:** Bulduğunuz her veri için "bu ölçülmüş mü, yoksa birinin tahmini mi?" ve "kullanma izni var mı?" sorularını yazın. Şimdiye kadarki en büyük hatalarımız bu ayrımı yapmamaktan çıktı.
