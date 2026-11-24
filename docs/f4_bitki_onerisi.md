# F4 – Bitki karışımı öneri motoru

Durum: çalışıyor (24.11.2026) · Motor: `src/model/oneri.py` · Panel: "Bitki önerisi" sayfası · Testler: `tests/test_oneri.py`

## Ne yapıyor?
Kullanıcı alanı ve kısıtlarını giriyor. Motor, Konca vd. (2026) tür tablosundan **toplam yıllık suyu en aza indiren karışımı** seçiyor. Her türün m² başına suyu, F1 hesap çekirdeğinden o ilin iklimiyle hesaplanıyor.

Yöntem karma tamsayılı doğrusal programlama (`scipy.optimize.milp`). Sonuç 0,1 saniyenin altında geliyor. **Bu bir optimizasyondur, makine öğrenmesi değildir.**

## Kısıtlar
| Kısıt | Varsayılan ("En az su" ayarı) |
|---|---|
| Alanın tamamı dolsun | — |
| Çim kalması gereken alan (oyun, piknik) | Kullanıcı girer; çim tipi: serin iklim (Kc 0,95) ya da kurağa dayanıklı 5'li (Kc 0,80) |
| En az gölge ağacı payı | %10. Ardıçlar (*Juniperus*) bu paya sayılmaz; yatık ya da çalı formlu oldukları için gölge vermezler |
| Bir türün en fazla payı | %30 |
| Seçilen her türün en az payı | %3 |
| En az tür sayısı | 4 |
| Hariç tutulan türler | Kullanıcı seçer |

**Kurallar:**
- Yapay çim önerilmez.
- Kc ≥ 0,9 olan çayır ve yonca türleri önerilmez, çünkü çimden fazla su isteyebilirler.
- Ağaç, çalı ve yer örtücüler damla; çim yağmurlama ile sulanır.

**Hazır ayarlar:**
| Ayar | En az gölge ağacı payı | Bir türün en fazla payı | En az tür sayısı |
|---|---|---|---|
| En az su | %10 | %30 | 4 |
| Dengeli: gölge ve çeşitlilik | %25 | %20 | 6 |
| Zengin görünüm | %20 | %12 | 9 |

## Örnek (Ankara, 10.000 m², 2.000 m² çim kalıyor)
| Ayar | m³/yıl | Tamamı çime göre |
|---|---|---|
| Tamamı çim | 11.903 | — |
| En az su | ~4.400 | −%63 |
| Dengeli | ~4.700 | −%61 |

Dengeli ayarda gölge payı iğde (*Elaeagnus angustifolia*) ve duman ağacı (*Cotinus coggygria*) ile dolduruluyor. Kalan 2.000 m² çim, alanın %20'si olduğu halde suyun yarısından fazlasını içiyor.

## Sınırlar
- **Tür tablosu Ankara için derlendi.** Başka illerde türlerin iklime ve toprağa uygunluğu kontrol edilmeli. Panelde "Önerilmesin" listesi bunun için var.
- **Isı etkisi hesaplanmıyor.** Gölgenin sıcaklığa etkisi yalnız "en az gölge ağacı payı" kısıtıyla temsil ediliyor.
- **Kurulum ve bakım maliyeti yok.** Türkiye için karşılaştırılabilir açık veri bulamadık.
- **Kc değerleri literatürden.** Tasarruflar hesaplanmış değerler, ölçülmüş değil. Las Vegas testi bu tasarrufların temkinli olduğunu gösterdi (hesap %62, ölçüm %76).
