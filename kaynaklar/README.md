# Kaynaklar

Bu klasörde yalnız yeniden dağıtımı açıkça serbest olan dosyalar var:

- `makaleler/Konca_Ahmad_Apaydin_2026_Water_Ankara_xeriscape.pdf`: CC BY 4.0 (Water 18:1362).
- `resmi/CB_Karari_10502_RG_20251018.pdf`: Resmî Gazete metni.
- `veri/`: Projenin kendi tabloları. `konca2026_ankara_kc_tablosu.csv` Konca vd. (2026) makalesinden (CC BY), `snwa_aylik_olcum.csv` Sovocool (2005) SNWA raporu Tablo 18'den alınan sayılar.

## Repoya konmayan belgeler

Lisansları yeniden dağıtıma izin verdiği belli olmayan belgeler repoya konmadı. Bağlantıları
`arastirma_kaynaklari.md` dosyasında. Kodun çalışması bunlara bağlı değil.

| Belge | Neden gerekli |
|---|---|
| Sovocool (2005), SNWA Xeriscape raporu | Las Vegas sayaç doğrulaması (veri `veri/snwa_aylik_olcum.csv` içinde) |
| Metin (2020), Etimesgut tezi | Ankara park bitki listeleri |
| Ayanoğlu & Demirel (2023) | Konut bahçesi bitki örnekleri |
| Sapkota vd. (2023), HortScience | Yer örtücü su ihtiyacı |
| UCR (2012) yer örtücü raporu | Yer örtücü su ihtiyacı |
| WUCOLS kılavuzu | Peyzaj katsayısı (kd, kmc) yöntemi |
| Tarım ve Orman Bakanlığı, Kurakçıl Peyzaj Rehberi (2024) | Bitki listesi ve EK-1 kategorileri |
| İSKİ 2025 su satış tarifeleri | Tarife değeri (`src/hesap/tarife.py` içinde) |
| Water AI Hackathon kanvas şablonu | `prototip/kanvas_doldur.py` girdisi; hackathon katılımcılarına verilir. Doldurulmuş hali `teslim/` klasöründe |
