"""Florify Water AI Hackathon 2026 sunumunu üretir (HTML + opsiyonel Chrome PDF).

Palet: Yeşil (#1B4D3E / #3D7A62 / #E5F1EC) · Toz Pembe (#9E5563 / #C98A92 / #F8E9EC) · Mavi (#245B7A / #4A89AC / #E5F0F7)
Çıktılar:
    teslim/Florify_Sunum.html   (tek dosya, tüm görseller base64 gömülü, tarayıcıda ok tuşlarıyla sunulabilir)
    teslim/Florify_Sunum.pdf    (headless Chrome ile 16:9 baskı kalitesinde PDF)

Çalıştırma:
    .venv\\Scripts\\python sunum/sunum_uret.py
"""
from __future__ import annotations

import base64
import shutil
import subprocess
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
GORSEL_DIR = KOK / "sunum" / "gorseller"
TESLIM_DIR = KOK / "teslim"
TESLIM_DIR.mkdir(parents=True, exist_ok=True)

# Demo slaytındaki "Kendiniz çalıştırın" bağlantısı (public repo).
DEMO_LINK = "https://github.com/gulnihalarikaymak/florify"
DEMO_LINK_YAZI = "github.com/gulnihalarikaymak/florify"


def _img_data_uri(yol: Path) -> str:
    b64 = base64.b64encode(yol.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_html() -> str:
    img_ankara = _img_data_uri(GORSEL_DIR / "grafik_ankara_aylik.png")
    img_uydu_scatter = _img_data_uri(GORSEL_DIR / "grafik_uydu_izmir.png")
    img_dogrulama = _img_data_uri(GORSEL_DIR / "grafik_dogrulama.png")
    img_2040 = _img_data_uri(GORSEL_DIR / "grafik_2040.png")
    img_izmir_harita = _img_data_uri(KOK / "prototip" / "cikti" / "uydu_izmir_harita.png")

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Florify — Water AI Hackathon 2026 Proje Sunumu (Petrichor)</title>
<style>
  :root {{
    --green-deep: #1B4D3E;
    --green: #3D7A62;
    --green-mid: #6EA58E;
    --green-soft: #E6F2EC;
    --green-border: #BBD8CB;

    --rose-deep: #9E5563;
    --rose: #C98A92;
    --rose-mid: #DBA9B0;
    --rose-soft: #F8E9EC;
    --rose-border: #E5C1C7;

    --blue-deep: #245B7A;
    --blue: #4A89AC;
    --blue-mid: #7DB0CC;
    --blue-soft: #E5F0F7;
    --blue-border: #BBD5E5;

    --bg: #FAFBF9;
    --card: #FFFFFF;
    --ink: #1C2B29;
    --muted: #536765;
    --line: #DDE7E3;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  @page {{
    size: 1280px 720px;
    margin: 0;
  }}

  html, body {{
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    background: #DCE5E2;
    color: var(--ink);
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  .deck {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
    padding: 24px 0 80px;
  }}

  .slide {{
    width: 1280px;
    height: 720px;
    background: var(--bg);
    position: relative;
    overflow: hidden;
    box-shadow: 0 14px 40px rgba(27, 77, 62, 0.14);
    display: flex;
    flex-direction: column;
    page-break-after: always;
    break-after: page;
  }}

  .slide:last-child {{
    page-break-after: auto;
    break-after: auto;
  }}

  /* Üst 3 renkli ince palet şeridi */
  .top-stripe {{
    height: 6px;
    width: 100%;
    background: linear-gradient(90deg, var(--green-deep) 0%, var(--green) 38%, var(--rose) 38%, var(--rose) 66%, var(--blue) 66%, var(--blue-deep) 100%);
    flex-shrink: 0;
  }}

  /* Yumuşak arka plan daireleri */
  .blob {{
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
  }}

  /* Slayt gövdesi */
  .slide-inner {{
    position: relative;
    z-index: 1;
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    padding: 26px 46px 20px;
  }}

  /* Başlık alanı */
  .slide-head {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 18px;
    gap: 20px;
  }}

  .kicker {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 999px;
    margin-bottom: 8px;
  }}
  .kicker.green {{ background: var(--green-soft); color: var(--green-deep); border: 1px solid var(--green-border); }}
  .kicker.rose  {{ background: var(--rose-soft);  color: var(--rose-deep);  border: 1px solid var(--rose-border); }}
  .kicker.blue  {{ background: var(--blue-soft);  color: var(--blue-deep);  border: 1px solid var(--blue-border); }}

  .slide-title {{
    font-size: 30px;
    font-weight: 800;
    line-height: 1.15;
    color: var(--green-deep);
    letter-spacing: -0.015em;
  }}

  .slide-sub {{
    font-size: 14.5px;
    color: var(--muted);
    margin-top: 5px;
    line-height: 1.38;
  }}

  /* Alt bilgi çubuğu */
  .slide-foot {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 46px 14px;
    font-size: 11.5px;
    color: var(--muted);
    border-top: 1px solid var(--line);
    background: rgba(255, 255, 255, 0.72);
    position: relative;
    z-index: 2;
    flex-shrink: 0;
  }}
  .foot-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
    color: var(--green-deep);
  }}
  .foot-dots {{
    display: inline-flex;
    gap: 4px;
  }}
  .foot-dots span {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }}

  /* Kartlar & Gridler */
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; flex: 1; min-height: 0; }}
  .grid-2-wide-r {{ display: grid; grid-template-columns: 0.92fr 1.28fr; gap: 24px; flex: 1; min-height: 0; }}
  .grid-2-wide-l {{ display: grid; grid-template-columns: 1.22fr 0.98fr; gap: 24px; flex: 1; min-height: 0; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}

  .card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 3px 12px rgba(27, 77, 62, 0.04);
  }}
  .card.green {{ background: var(--green-soft); border-color: var(--green-border); }}
  .card.rose  {{ background: var(--rose-soft);  border-color: var(--rose-border); }}
  .card.blue  {{ background: var(--blue-soft);  border-color: var(--blue-border); }}

  .card-title {{
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
    color: var(--green-deep);
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .card.rose .card-title  {{ color: var(--rose-deep); }}
  .card.blue .card-title  {{ color: var(--blue-deep); }}

  .kpi-num {{
    font-size: 32px;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.02em;
  }}
  .kpi-label {{
    font-size: 13px;
    color: var(--muted);
    margin-top: 4px;
    line-height: 1.35;
  }}

  .tag {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    vertical-align: middle;
  }}
  .tag.hesap  {{ background: var(--blue-soft);  color: var(--blue-deep);  border: 1px solid var(--blue-border); }}
  .tag.olcum  {{ background: var(--green-soft); color: var(--green-deep); border: 1px solid var(--green-border); }}
  .tag.uyari  {{ background: var(--rose-soft);  color: var(--rose-deep);  border: 1px solid var(--rose-border); }}

  .chart-frame {{
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 0;
    min-width: 0;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(27, 77, 62, 0.05);
  }}
  .chart-frame img {{
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    display: block;
  }}
  .ico {{
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    vertical-align: -2px;
  }}

  ul.clean {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  ul.clean li {{
    font-size: 14px;
    line-height: 1.44;
    padding-left: 18px;
    position: relative;
    color: var(--ink);
  }}
  ul.clean li::before {{
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--green);
    position: absolute;
    left: 0;
    top: 7px;
  }}
  ul.clean.rose li::before {{ background: var(--rose-deep); }}
  ul.clean.blue li::before {{ background: var(--blue-deep); }}

  table.data-tbl {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  table.data-tbl th {{
    text-align: left;
    padding: 9px 12px;
    background: var(--green-deep);
    color: #FFFFFF;
    font-weight: 700;
    font-size: 12.5px;
  }}
  table.data-tbl th:first-child {{ border-radius: 10px 0 0 0; }}
  table.data-tbl th:last-child  {{ border-radius: 0 10px 0 0; }}
  table.data-tbl td {{
    padding: 8.5px 12px;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
    line-height: 1.35;
  }}
  table.data-tbl tr:nth-child(even) td {{
    background: #F5F9F7;
  }}

  /* Kapak slaytı özel */
  .cover-slide {{
    background: linear-gradient(135deg, #F5FAF7 0%, #FAFBF9 48%, #FBF0F2 76%, #EBF4FA 100%);
  }}
  .cover-grid {{
    display: grid;
    grid-template-columns: 1.25fr 0.85fr;
    gap: 32px;
    flex: 1;
    align-items: center;
    padding: 36px 56px 28px;
    position: relative;
    z-index: 2;
  }}
  .cover-badge {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: #FFFFFF;
    border: 1px solid var(--green-border);
    color: var(--green-deep);
    padding: 7px 16px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 20px;
    box-shadow: 0 3px 10px rgba(27, 77, 62, 0.06);
  }}
  .cover-logo {{
    font-size: 68px;
    font-weight: 900;
    letter-spacing: -0.03em;
    color: var(--green-deep);
    line-height: 1.0;
    margin-bottom: 14px;
  }}
  .cover-logo span {{
    color: var(--rose-deep);
  }}
  .cover-tagline {{
    font-size: 24px;
    font-weight: 600;
    color: var(--blue-deep);
    line-height: 1.32;
    margin-bottom: 18px;
    max-width: 620px;
  }}
  .cover-desc {{
    font-size: 15.5px;
    color: var(--muted);
    line-height: 1.55;
    max-width: 610px;
    margin-bottom: 26px;
  }}
  .cover-pills {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 26px;
  }}
  .pill {{
    padding: 9px 15px;
    border-radius: 12px;
    font-size: 13.5px;
    font-weight: 700;
  }}
  .pill.g {{ background: var(--green-soft); color: var(--green-deep); border: 1px solid var(--green-border); }}
  .pill.r {{ background: var(--rose-soft);  color: var(--rose-deep);  border: 1px solid var(--rose-border); }}
  .pill.b {{ background: var(--blue-soft);  color: var(--blue-deep);  border: 1px solid var(--blue-border); }}

  .cover-meta {{
    display: flex;
    gap: 28px;
    padding-top: 16px;
    border-top: 1px solid var(--line);
    font-size: 13.5px;
    color: var(--muted);
  }}
  .cover-meta strong {{ color: var(--ink); display: block; font-size: 14.5px; margin-top: 2px; }}

  /* Adım akışı */
  .step-box {{
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 18px 18px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    position: relative;
  }}
  .step-num {{
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 15px;
    color: #FFFFFF;
  }}

  /* Sunum kontrol çubuğu (sadece ekranda görünür, PDF baskısında gizli) */
  .nav-bar {{
    position: fixed;
    bottom: 18px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(27, 77, 62, 0.92);
    color: #FFFFFF;
    padding: 8px 16px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 13px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
    z-index: 999;
    backdrop-filter: blur(8px);
  }}
  .nav-bar button {{
    background: rgba(255, 255, 255, 0.16);
    color: #FFFFFF;
    border: none;
    border-radius: 999px;
    padding: 5px 12px;
    cursor: pointer;
    font-size: 12.5px;
    font-weight: 600;
  }}
  .nav-bar button:hover {{ background: rgba(255, 255, 255, 0.28); }}

  @media print {{
    html, body {{ background: #FFFFFF; }}
    .deck {{ padding: 0; gap: 0; display: block; }}
    .slide {{ box-shadow: none; margin: 0; }}
    .nav-bar {{ display: none !important; }}
  }}
</style>
</head>
<body>
<div class="deck">

<!-- ════════════════════════ SLAYT 1: KAPAK ════════════════════════ -->
<section class="slide cover-slide">
  <div class="top-stripe"></div>
  <div class="blob" style="width:420px;height:420px;right:-110px;top:-110px;background:radial-gradient(circle, rgba(201,138,146,0.22), transparent 70%);"></div>
  <div class="blob" style="width:460px;height:460px;left:-120px;bottom:-150px;background:radial-gradient(circle, rgba(61,122,98,0.18), transparent 70%);"></div>
  <div class="blob" style="width:360px;height:360px;right:180px;bottom:-120px;background:radial-gradient(circle, rgba(74,137,172,0.18), transparent 70%);"></div>

  <div class="cover-grid">
    <div>
      <div class="cover-badge">
        <span style="width:8px;height:8px;border-radius:50%;background:var(--rose-deep);display:inline-block;"></span>
        Water AI Hackathon 2026 · Wilo · Proje Fikri Sunumu
      </div>
      <div class="cover-logo">Flor<span>ify</span></div>
      <div class="cover-tagline">Belediyeler için Su Tasarruflu Peyzaj Karar ve İzleme Aracı</div>
      <p class="cover-desc">
        Parklardaki çim alanların yıllık su ve bütçe yükünü hesaplayan, gölge ve çeşitliliği koruyan kurakçıl bitki karışımı öneren, uydudan sulanan yeşili tespit eden ve <strong>Cumhurbaşkanı Kararı 10502 EK-1</strong> taslağını yalnızca açık verilerle üreten karar destek sistemi.
      </p>
      <div class="cover-pills">
        <span class="pill g">135 Tekil Bitki Türü (MILP)</span>
        <span class="pill b">81 İlde Uydu Analizi (İzmir’de Doğrulandı)</span>
        <span class="pill r">CB Kararı 10502 EK-1 Taslağı</span>
      </div>
      <div class="cover-meta">
        <div>Takım Adı<strong>Petrichor</strong></div>
        <div>Çalışma Alanı<strong>Kent — Park ve Peyzaj Sulaması</strong></div>
        <div>Veri İlkesi<strong>%100 Açık ve Ücretsiz Veri</strong></div>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;gap:14px;">
      <!-- Dekoratif & bilgi verici özet kart bloğu -->
      <div style="background:#FFFFFF;border:1px solid var(--green-border);border-radius:20px;padding:22px 24px;box-shadow:0 12px 30px rgba(27,77,62,0.09);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
          <span style="font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--green-deep);">Örnek Etki · Ankara 10.000 m² Park</span>
          <span class="tag hesap">FAO-56 Hesap</span>
        </div>
        <svg viewBox="0 0 360 150" width="100%" style="display:block;margin-bottom:12px;">
          <!-- Mevcut çim çubuğu -->
          <text x="0" y="20" font-size="12" font-weight="700" fill="#9E5563">Mevcut (%100 Çim · Yağmurlama)</text>
          <rect x="0" y="28" width="330" height="24" rx="8" fill="#F8E9EC" stroke="#E5C1C7"/>
          <rect x="0" y="28" width="330" height="24" rx="8" fill="#C98A92"/>
          <text x="320" y="44" font-size="12" font-weight="800" fill="#FFFFFF" text-anchor="end">11.903 m³/yıl</text>

          <!-- Florify önerisi çubuğu -->
          <text x="0" y="82" font-size="12" font-weight="700" fill="#1B4D3E">Florify Önerisi (%20 Oyun Çimi + %80 Kurakçıl)</text>
          <rect x="0" y="90" width="330" height="24" rx="8" fill="#E6F2EC" stroke="#BBD8CB"/>
          <rect x="0" y="90" width="131" height="24" rx="8" fill="#3D7A62"/>
          <text x="142" y="106" font-size="12" font-weight="800" fill="#1B4D3E">4.725 m³/yıl (−%60,3)</text>

          <!-- Kazanç şeridi -->
          <rect x="0" y="126" width="330" height="22" rx="6" fill="#E5F0F7"/>
          <text x="165" y="141" font-size="11.5" font-weight="700" fill="#245B7A" text-anchor="middle">7.178 m³/yıl tasarruf · ~40 hane · ~1,41 M TL/yıl (ASKİ)</text>
        </svg>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:6px;">
          <div style="background:var(--blue-soft);border-radius:12px;padding:11px 13px;">
            <div style="font-size:20px;font-weight:800;color:var(--blue-deep);">ρ = 0,85</div>
            <div style="font-size:11.5px;color:var(--muted);">İzmir 11 ilçe uydu–fatura uyumu</div>
          </div>
          <div style="background:var(--rose-soft);border-radius:12px;padding:11px 13px;">
            <div style="font-size:20px;font-weight:800;color:var(--rose-deep);">r = 0,96</div>
            <div style="font-size:11.5px;color:var(--muted);">SNWA sayaç testi (temkinli)</div>
          </div>
        </div>
      </div>

      <div style="background:rgba(255,255,255,0.84);border:1px solid var(--line);border-radius:14px;padding:12px 16px;font-size:12.5px;color:var(--muted);line-height:1.45;">
        <strong style="color:var(--green-deep);">Bilimsel Dürüstlük İlkesi:</strong> Sunumdaki her sayı <em>ölçüm / fatura</em>, <em>hesap</em> ya da <em>varsayım</em> etiketiyle ayrıştırılmıştır; başarısız denemeler (AI-1) açıkça raporlanmıştır.
      </div>
    </div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 2: 01 PROBLEM ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker rose">01 · Problem</span>
        <h1 class="slide-title">Parklardaki Çim, Kentin En Çok Su İsteyen Bitki Örtüsü</h1>
        <p class="slide-sub">Özellikle sıcak ve kurak yaz aylarında park çimleri yüksek şebeke suyu tüketiyor; yerel veriler sorunun ölçeğini açıkça ortaya koyuyor.</p>
      </div>
    </div>

    <div class="grid-2-wide-r">
      <div style="display:flex;flex-direction:column;gap:14px;justify-content:space-between;">
        <div class="card rose">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:12px;font-weight:700;color:var(--rose-deep);text-transform:uppercase;">Ankara · 1 m² Çim (Yıllık)</span>
            <span class="tag hesap">FAO-56 Hesap</span>
          </div>
          <div class="kpi-num" style="color:var(--rose-deep);">1.190 L/m²</div>
          <div class="kpi-label">Serin iklim çim karışımı (Kc 0,95, yağmurlama %70, 2020–2024 ERA5). Kurakçıl lavantanın <strong>~3,4 katı</strong> su ister.</div>
        </div>

        <div class="card blue">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:12px;font-weight:700;color:var(--blue-deep);text-transform:uppercase;">İzmir · 11 Merkez İlçe (2023)</span>
            <span class="tag olcum">İZSU Fatura</span>
          </div>
          <div class="kpi-num" style="color:var(--blue-deep);">8,37 milyon m³</div>
          <div class="kpi-label">Park ve mezarlık aboneliklerinin bir yıllık şebeke suyu tüketimi (İZSU açık verisi).</div>
        </div>

        <div class="card green">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:12px;font-weight:700;color:var(--green-deep);text-transform:uppercase;">Toplumsal Ölçek</span>
            <span class="tag olcum">Hane Eşdeğeri</span>
          </div>
          <div class="kpi-num" style="color:var(--green-deep);">~46.500 hane</div>
          <div class="kpi-label">İzmir’in yalnız 11 merkez ilçesindeki park/mezarlık suyu, <strong>46 binden fazla hanenin</strong> bir yıllık su tüketimine (180 m³/yıl) eşdeğerdir.</div>
        </div>
      </div>

      <div class="chart-frame">
        <img src="{img_ankara}" alt="Ankara aylık sulama ihtiyacı grafiği" />
      </div>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>01 Problem · Kaynak: Open-Meteo/ERA5, Konca vd. (2026), İZSU Açık Veri (CC BY 4.0)</div>
    <div>02 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 3: 02 HEDEF KULLANICI ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker green">02 · Hedef Kullanıcı ve İhtiyaç</span>
        <h1 class="slide-title">Belediye Park ve Bahçe Birimleri İçin Yeni Yasal Yükümlülük</h1>
        <p class="slide-sub">Ekim 2025’te yürürlüğe giren Cumhurbaşkanı Kararı 10502, belediyelerden hem çimi azaltmalarını hem de her yıl veri raporlamalarını istiyor.</p>
      </div>
    </div>

    <div class="card green" style="margin-bottom:18px;display:flex;align-items:center;justify-content:space-between;gap:24px;">
      <div>
        <div style="font-size:12px;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:var(--green-deep);margin-bottom:4px;">Yasal Dayanak · Resmî Gazete 18.10.2025 / 33051</div>
        <div style="font-size:20px;font-weight:800;color:var(--green-deep);">Cumhurbaşkanı Kararı 10502 — Kentsel Peyzajda Su Verimliliği</div>
        <div style="font-size:14px;color:var(--ink);margin-top:4px;">Belediyelerin çim alanlarını daraltması, kurakçıl peyzaja geçmesi ve her yıl <strong>Peyzaj İzleme Sistemi (EK-1)</strong> üzerinden 23 maddelik form doldurması gerekiyor.</div>
      </div>
      <div style="background:#FFFFFF;border:1px solid var(--green-border);border-radius:14px;padding:12px 18px;text-align:center;flex-shrink:0;">
        <div style="font-size:26px;font-weight:900;color:var(--green-deep);">23 Madde</div>
        <div style="font-size:12px;color:var(--muted);">Yıllık EK-1 İzleme Formu</div>
      </div>
    </div>

    <div class="grid-3" style="flex:1;">
      <div class="card" style="display:flex;flex-direction:column;justify-content:space-between;border-top:4px solid var(--blue);">
        <div>
          <div class="card-title" style="color:var(--blue-deep);">01 · Kim Kullanacak?</div>
          <p style="font-size:14px;line-height:1.5;color:var(--ink);margin-bottom:12px;">
            İlçe ve büyükşehir belediyelerinin <strong>Park ve Bahçeler Müdürlükleri</strong>, peyzaj mimarları, su yönetimi ve strateji geliştirme ekipleri.
          </p>
        </div>
        <div style="background:var(--blue-soft);border-radius:10px;padding:10px 12px;font-size:12.5px;color:var(--blue-deep);font-weight:600;">
          Öncelikli karar anı: Yıllık peyzaj ihalesi, park yenileme ve bütçe planlaması.
        </div>
      </div>

      <div class="card" style="display:flex;flex-direction:column;justify-content:space-between;border-top:4px solid var(--rose);">
        <div>
          <div class="card-title" style="color:var(--rose-deep);">02 · Nerede Zorlanıyorlar?</div>
          <ul class="clean rose" style="margin-top:4px;">
            <li>Hangi parkta çimin yerine <strong>hangi bitki</strong> dikilirse kaç m³ su ve kaç TL tasarruf edileceğini hesaplayamıyorlar.</li>
            <li>Park envanteri eksik ilçelerde öncelikli yüksek tüketimli alanları görmek zor.</li>
            <li>Gölge ve park estetiğini bozmadan tür seçimi uzmanlık ve zaman gerektiriyor.</li>
          </ul>
        </div>
        <div style="background:var(--rose-soft);border-radius:10px;padding:10px 12px;font-size:12.5px;color:var(--rose-deep);font-weight:600;">
          Somut karar aracı eksikliği dönüşümü yavaşlatıyor.
        </div>
      </div>

      <div class="card" style="display:flex;flex-direction:column;justify-content:space-between;border-top:4px solid var(--green);">
        <div>
          <div class="card-title" style="color:var(--green-deep);">03 · Ne İstiyorlar?</div>
          <ul class="clean" style="margin-top:4px;">
            <li>İl iklimi ve güncel belediye tarifesiyle <strong>m³, TL ve hane</strong> cinsinden şeffaf hesap.</li>
            <li>Tek rakam değil, belirsizlik aralığı (<strong>P10–P90</strong>) ve basit geri ödeme süresi.</li>
            <li>Mevzuatın istediği <strong>EK-1 formuna</strong> doğrudan aktarılabilir taslak çıktı.</li>
          </ul>
        </div>
        <div style="background:var(--green-soft);border-radius:10px;padding:10px 12px;font-size:12.5px;color:var(--green-deep);font-weight:600;">
          Belediye meclisi ve bütçe onayında savunulabilir sayısal gerekçe.
        </div>
      </div>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>02 Hedef Kullanıcı ve İhtiyaç · Dayanak: CB Kararı 10502 (RG 18.10.2025/33051)</div>
    <div>03 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 4: 03 MEVCUT YAKLAŞIM ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker blue">03 · Mevcut Yaklaşım ve Eksikliği</span>
        <h1 class="slide-title">Bugünkü Kararlar Genel Söylemler ve Sabit Takvimlerle Veriliyor</h1>
        <p class="slide-sub">Gerçek belediye fatura verileri ve literatür incelememiz, mevcut uygulamada dört temel boşluk olduğunu gösteriyor.</p>
      </div>
    </div>

    <div class="grid-2" style="gap:20px;">
      <div style="display:flex;flex-direction:column;gap:16px;">
        <div class="card rose" style="flex:1;">
          <div class="card-title">1. Park Bazında Hesap Yok, Yurt Dışı Genellemeler Var</div>
          <p style="font-size:14px;line-height:1.5;color:var(--ink);">
            Kararlar <em>“kuraklığa dayanıklı bitkiler %20–80 tasarruf sağlar”</em> gibi çok geniş ve çoğu yurt dışından (ör. Arizona) gelen oranlarla veriliyor. Belirli bir parkta, belirli bir bitki türüyle kaç m³ su kazanılacağı hesaplanmıyor.
          </p>
        </div>

        <div class="card blue" style="flex:1;">
          <div class="card-title">2. Sulama İklime Göre Ayarlanmıyor Görünüyor</div>
          <p style="font-size:14px;line-height:1.5;color:var(--ink);">
            İzmir’in 10 yıllık (129 ay) İZSU park/mezarlık faturalarında, yıllar arası iklim sapması ile yaz tüketimi arasındaki ilişki zayıf: <strong>r = 0,33</strong> (trend çıkarılmış, n = 11 yıl, anlamlı değil) <span class="tag olcum">İZSU Fatura</span>. Bu, sulamanın kurak ya da serin yıla göre pek değişmediğine <em>işaret ediyor</em>; kesin kanıt değil, yorumumuz.
          </p>
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:16px;">
        <div class="card" style="flex:1;border-left:5px solid var(--green);">
          <div class="card-title">3. Eski İklim Normalleri İhtiyacı Düşük Gösteriyor</div>
          <p style="font-size:14px;line-height:1.5;color:var(--ink);">
            10 ilde yaptığımız ERA5 karşılaştırması, <strong>son 10 yıl ortalamasının</strong> eski 1991–2014 normaline göre sulama ihtiyacını <strong>%5 daha isabetli</strong> öngördüğünü gösterdi <span class="tag hesap">Hesap</span>. Eski normallerle yapılan planlama sulama ihtiyacını düşük gösteriyor.
          </p>
        </div>

        <div class="card" style="flex:1;border-left:5px solid var(--rose);">
          <div class="card-title">4. Envanter ve Raporlama Kopukluğu</div>
          <p style="font-size:14px;line-height:1.5;color:var(--ink);">
            Birçok belediyenin ilçe genelinde güncel, sayısallaştırılmış sulanan çim envanteri yok. Peyzaj tasarımı, su faturası ve CB 10502 EK-1 izleme raporu birbirinden kopuk manuel tablolarda yürüyor.
          </p>
        </div>
      </div>
    </div>

    <div style="margin-top:16px;background:var(--green-deep);color:#FFFFFF;border-radius:14px;padding:13px 22px;display:flex;align-items:center;justify-content:space-between;font-size:14px;">
      <div><strong>Farkımız:</strong> Mevcut bitki su ihtiyacı listeleri ve sulama hesaplayıcıları (ör. ABD’deki WUCOLS) tek bir parçayı veriyor. Türkiye’de <em>il iklimi + bitki katsayısı + belediye tarifesi + uydu envanteri + EK-1 raporu</em> parçalarını tek yerde birleştiren açık bir araç bulamadık.</div>
      <span style="background:rgba(255,255,255,0.16);padding:5px 12px;border-radius:999px;font-weight:700;font-size:12px;white-space:nowrap;">Florify’ın Çıkış Noktası</span>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>03 Mevcut Yaklaşım ve Eksikliği · İZSU 2014–2024 analizi & ERA5 10 il karşılaştırması</div>
    <div>04 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 5: 04 ÇÖZÜM ÖNERİSİ ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker green">04 · Çözüm Önerisi</span>
        <h1 class="slide-title">Florify: Tek Web Panelinde Hesap, Bitki Önerisi, Uydu ve EK-1</h1>
        <p class="slide-sub">Belediye çalışanı parkın ilini, büyüklüğünü ve mevcut bitkilerini girer; Florify saniyeler içinde karar ve rapor çıktısı üretir.</p>
      </div>
    </div>

    <div class="grid-4" style="margin-bottom:18px;">
      <div class="step-box" style="border-top:4px solid var(--blue);">
        <div class="step-num" style="background:var(--blue-deep);">1</div>
        <div style="font-size:15.5px;font-weight:800;color:var(--blue-deep);">Park & İl Seçimi</div>
        <p style="font-size:13px;line-height:1.45;color:var(--muted);">81 il için önbellekli ERA5 iklim verisi (son 10 yıl / 5 yıl / 30 yıl), park m²’si, sulama yöntemi ve ASKİ/İZSU/İSKİ tarifesi seçilir.</p>
      </div>

      <div class="step-box" style="border-top:4px solid var(--green);">
        <div class="step-num" style="background:var(--green-deep);">2</div>
        <div style="font-size:15.5px;font-weight:800;color:var(--green-deep);">FAO-56 + Belirsizlik</div>
        <p style="font-size:13px;line-height:1.45;color:var(--muted);">Aylık su ihtiyacı (<code>ET₀·Kc·kd − Peff ÷ randıman</code>), 1.000 çekilişli Monte Carlo <strong>P10–P90</strong> bandı, m³/TL/hane ve basit geri ödeme (ROI) hesaplanır.</p>
      </div>

      <div class="step-box" style="border-top:4px solid var(--rose);">
        <div class="step-num" style="background:var(--rose-deep);">3</div>
        <div style="font-size:15.5px;font-weight:800;color:var(--rose-deep);">Akıllı Bitki Karışımı</div>
        <p style="font-size:13px;line-height:1.45;color:var(--muted);">135 tekil türden oyun çimini, gerçek gölge ağacını ve çalı/çiçek çeşitliliğini koruyan en az sulu karışım tek tıkla park hesabına aktarılır.</p>
      </div>

      <div class="step-box" style="border-top:4px solid var(--green-deep);">
        <div class="step-num" style="background:var(--green);">4</div>
        <div style="font-size:15.5px;font-weight:800;color:var(--green-deep);">EK-1 Taslak Formu</div>
        <p style="font-size:13px;line-height:1.45;color:var(--muted);">CB Kararı 10502’nin 23 maddelik resmî Peyzaj İzleme Formu, hesaplanan ve idarece doldurulacak alanlar açıkça ayrıştırılarak üretilir.</p>
      </div>
    </div>

    <div class="grid-2" style="flex:1;">
      <div class="card blue" style="display:flex;flex-direction:column;justify-content:center;">
        <div class="card-title">Park Envanteri Olmasa Bile İlçe Ölçeğinde Görünürlük</div>
        <p style="font-size:14px;line-height:1.5;color:var(--ink);">
          Florify’ın <strong>Uydu Haritası</strong> sekmesi, 81 il/ilçe için Sentinel-2 ve ESA WorldCover verisinden yazın sulanan yeşil alanları 10×10 m çözünürlükle çıkarır. Böylece belediye önce en çok sulanan bölgeleri görür, ardından park bazında dönüşüm senaryosu çalıştırır.
        </p>
      </div>

      <div class="card rose" style="display:flex;flex-direction:column;justify-content:center;">
        <div class="card-title">Resmî EK-1 Çıktısında Uydurma Yok</div>
        <ul class="clean rose">
          <li><strong>Otomatik dolan maddeler (1–4, 7, 11–14, 17, 22):</strong> Hesap çekirdeğinden türetilir ve açıkça <code>[Hesap / Tahmin]</code> etiketi taşır.</li>
          <li><strong>Saha / kurum kaydı gerektirenler (5–6, 8–10, 15–16, 18–21, 23):</strong> Uydurulmaz, <code>[İdare tarafından doldurulur]</code> olarak boş bırakılır.</li>
        </ul>
      </div>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>04 Çözüm Önerisi · Çalışan web arayüzü (web/sunucu.py) ve Streamlit paneli (app/panel.py)</div>
    <div>05 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 6: 05 YAPAY ZEKÂNIN ROLÜ ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker blue">05 · Yapay Zekânın Rolü</span>
        <h1 class="slide-title">Uydu ile Sulanan Yeşil Tespiti + Kısıtlı Karışım Optimizasyonu</h1>
        <p class="slide-sub">Yapay zekânın işi: park envanteri olmayan belediyeye, uydudan yazın sulanan yeşilin haritasını çıkarmak ve bunu gerçek su faturasıyla sınamak.</p>
      </div>
    </div>

    <div class="grid-2-wide-l">
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div class="chart-frame" style="flex:1;">
          <img src="{img_uydu_scatter}" alt="İzmir 11 ilçe uydu vs İZSU fatura grafiği" />
        </div>
        <div style="background:var(--blue-soft);border:1px solid var(--blue-border);border-radius:12px;padding:10px 14px;font-size:12.8px;color:var(--blue-deep);line-height:1.42;">
          <strong>Uydu katmanı (10×10 m):</strong> ESA WorldCover (ESA’nın makine öğrenmesiyle ürettiği arazi örtüsü haritası; ağaç/su elenir) + kentsel maske (&gt;%40 yapı) + Sentinel-2 Ağustos NDVI &gt; 0,5. <strong>Basit yöntemle kıyas:</strong> İlçenin yalnız kentsel alan büyüklüğü sabit tutulsa bile faturayla ilişki sürüyor (kısmi <strong>ρ = 0,70</strong>, p = 0,015).<br/>
          <strong>Hackathon’da:</strong> Kendi eğittiğimiz çok mevsimli sınıflandırıcıyı bu kuralla aynı fatura testinde kıyaslayacağız.
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:14px;">
        <div class="card green">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <div class="card-title" style="margin:0;">Bitki Karışımı Optimizasyonu (F4)</div>
            <span class="tag olcum">MILP · &lt;0,1 sn</span>
          </div>
          <ul class="clean">
            <li>Karma tamsayılı doğrusal programlama (<code>scipy.optimize.milp</code>) — <em>optimizasyondur, ML değildir.</em></li>
            <li>Oyun çimi, <strong>gerçek gölge ağacı</strong> (ardıçlar gölgeye sayılmaz), çalı/çiçek katmanı ve tür çeşitliliği kısıtlarını koruyarak suyu en aza indirir.</li>
            <li>Yapay çim ve yüksek sulu (Kc ≥ 0,9) yonca/çayır önerilmez.</li>
          </ul>
        </div>

        <div class="card rose" style="flex:1;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <div class="card-title" style="margin:0;">Dürüstlük Notu: Denenip Bırakılan AI-1</div>
            <span class="tag uyari">Elenen Deneme</span>
          </div>
          <p style="font-size:13.4px;line-height:1.48;color:var(--ink);margin-bottom:8px;">
            <strong>LightGBM ile 1–3 aylık sezon tahmini</strong> 10 ilde 1991–2025 ERA5 verisiyle denendi (760 test örneği). Model, son 10 yıl ortalamasından <strong>%5–7 daha kötü</strong> çıktı (MAE 26,2 vs 24,8 mm/ay).
          </p>
          <p style="font-size:13px;line-height:1.42;color:var(--rose-deep);font-weight:600;">
            → Bu yüzden “AI sezonu tahmin ediyor” iddiasını bıraktık; panelde test edilen en iyi yöntem olan son 10 yıl ortalamasını kullanıyoruz.
          </p>
        </div>
      </div>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>05 Yapay Zekânın Rolü · Denenen 3 uydu kuralı (ρ = 0,08 / 0,61 / 0,85) ve AI-1 elenmesi repoda raporlandı</div>
    <div>06 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 7: 06 VERİ VE UYGULANABİLİRLİK ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker green">06 · Veri ve Uygulanabilirlik</span>
        <h1 class="slide-title">%100 Açık, Ücretsiz ve Tekrarlanabilir Veri Mimarisi</h1>
        <p class="slide-sub">Kurum içi kapalı veri ya da ücretli lisans gerekmeden 81 ilde çalışır; henüz doğrulanmayan noktalar açıkça belirtilir.</p>
      </div>
    </div>

    <div style="margin-bottom:16px;">
      <table class="data-tbl">
        <thead>
          <tr>
            <th style="width:23%;">Veri Katmanı</th>
            <th style="width:33%;">Kaynak</th>
            <th style="width:24%;">Kullanım Amacı</th>
            <th style="width:20%;">Durum & Lisans</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Geçmiş İklim (ERA5)</strong></td>
            <td>Open-Meteo Archive API (1981–2025)</td>
            <td>81 il günlük ET₀, yağış, sıcaklık, nem</td>
            <td><span class="tag olcum">Hazır</span> CC BY 4.0*</td>
          </tr>
          <tr>
            <td><strong>2040’lar İklim Projeksiyonu</strong></td>
            <td>Open-Meteo Climate (7 CMIP6 HighResMIP)</td>
            <td>Yüksek emisyon (RCP8.5 benzeri) delta hesabı</td>
            <td><span class="tag olcum">Hazır</span> CC BY 4.0*</td>
          </tr>
          <tr>
            <td><strong>Uydu & Arazi Örtüsü</strong></td>
            <td>ESA WorldCover 2021 + Sentinel-2 L2A (AWS) + OSM</td>
            <td>10 m çözünürlükte yazın sulanan yeşil tespiti</td>
            <td><span class="tag olcum">Hazır</span> CC BY 4.0 / ODbL</td>
          </tr>
          <tr>
            <td><strong>Bitki Su Katsayıları (Kc)</strong></td>
            <td>Konca, Ahmad & Apaydın (2026) + Bakanlık Rehberi 2024</td>
            <td>135 tekil tür, Türkçe adlar, EK-1 kategorisi</td>
            <td><span class="tag olcum">Hazır</span> CC BY / Kamu</td>
          </tr>
          <tr>
            <td><strong>Gerçek Fatura & Tarifeler</strong></td>
            <td>İZSU Açık Veri (2014–2024) · ASKİ / İZSU / İSKİ PDF</td>
            <td>Doğrulama + TL tasarruf (197,04 / 71,83 / 85,78 TL/m³)</td>
            <td><span class="tag olcum">Hazır</span> CC BY 4.0 / Resmî</td>
          </tr>
        </tbody>
      </table>
      <div style="font-size:11px;color:var(--muted);margin-top:5px;">* Open-Meteo ücretsiz API ticari olmayan kullanım içindir; üretim belediye kurulumunda Copernicus CDS / MGM verisiyle doğrudan değiştirilebilir.</div>
    </div>

    <div class="grid-2" style="flex:1;">
      <div class="card rose">
        <div class="card-title">Henüz Doğrulamadıklarımız (Açık Varsayımlar)</div>
        <ul class="clean rose">
          <li><strong>ERA5 vs. MGM İstasyon Sapması:</strong> ERA5, Las Vegas’ta ET₀’ı ~%20 düşük verdi. Türkiye’deki MGM istasyon normalleriyle il bazında sapma henüz ölçülmedi.</li>
          <li><strong>Türkiye Saha Sayacı:</strong> Model ABD sayaçlı çalışması ve İzmir faturalarıyla sınandı; Türkiye’de sayaçlı tekil bir parkta henüz pilot yapılmadı.</li>
          <li><strong>Kurulum & Bakım Maliyeti:</strong> Türkiye için karşılaştırılabilir açık birim maliyet verisi yok; ROI modülünde kullanıcı varsayımı olarak giriliyor.</li>
        </ul>
      </div>

      <div class="card blue">
        <div class="card-title">Neden Bugün Uygulanabilir?</div>
        <ul class="clean blue">
          <li><strong>Sıfır veri engeli:</strong> Başvuru, abonelik veya belediye içi gizli veri beklemeden 81 ilde ilk günden çalışıyor.</li>
          <li><strong>Hafif açık kaynak yığın:</strong> Python (<code>scipy</code>, <code>rasterio</code>, standart kütüphane HTTP sunucusu) + düz HTML/JS arayüz; standart bir belediye sunucusunda çalışır.</li>
          <li><strong>Kademeli derinleşme:</strong> Belediye kendi park sayaçlarını ve OSM/CBS sınırlarını ekledikçe kalibrasyon doğrudan iyileşir.</li>
        </ul>
      </div>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>06 Veri ve Uygulanabilirlik · Tüm veri kaynakları atıf şartıyla açık lisanslıdır</div>
    <div>07 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 8: 07 BEKLENEN SU ETKİSİ ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker green">07 · Beklenen Su Etkisi</span>
        <h1 class="slide-title">Tek Parkta %60 Su Tasarrufu; 2040’larda Çimin Ek Yükü Kurakçılın 2,7 Katı</h1>
        <p class="slide-sub">Ankara’da 10.000 m² çim parkın %20’si oyun çimi kalıp %80’i MILP Dengeli kurakçıl karışıma dönünce oluşan etki (2020–2024 ERA5).</p>
      </div>
    </div>

    <div class="grid-2-wide-l">
      <div style="display:flex;flex-direction:column;gap:14px;justify-content:space-between;min-height:0;">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
          <div class="card green" style="padding:16px 16px;">
            <div style="font-size:11.5px;font-weight:700;color:var(--green-deep);">Yıllık Su Tasarrufu</div>
            <div class="kpi-num" style="font-size:28px;color:var(--green-deep);margin-top:4px;">%60,3</div>
            <div class="kpi-label" style="font-size:12px;"><strong>7.178 m³/yıl</strong> (11.903 → 4.725 m³)<br/>P10–P90: 5.276–9.467 m³</div>
          </div>

          <div class="card blue" style="padding:16px 16px;">
            <div style="font-size:11.5px;font-weight:700;color:var(--blue-deep);">Yıllık Bütçe Kazancı</div>
            <div class="kpi-num" style="font-size:28px;color:var(--blue-deep);margin-top:4px;">1,41 M TL</div>
            <div class="kpi-label" style="font-size:12px;">ASKİ Kasım 2026 park tarifesi (197,04 TL/m³, KDV hariç)</div>
          </div>

          <div class="card rose" style="padding:16px 16px;">
            <div style="font-size:11.5px;font-weight:700;color:var(--rose-deep);">Hane Eşdeğeri</div>
            <div class="kpi-num" style="font-size:28px;color:var(--rose-deep);margin-top:4px;">~40 hane</div>
            <div class="kpi-label" style="font-size:12px;">40 hanenin bir yıllık şebeke suyu (180 m³/yıl) <span class="tag hesap">Hesap</span></div>
          </div>
        </div>

        <div class="card" style="padding:18px 20px;flex:1;display:flex;flex-direction:column;justify-content:center;">
          <div class="card-title" style="font-size:15px;margin-bottom:10px;">Önerilen MILP Dengeli Karışım (10.000 m² · 7 Tür)</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 18px;font-size:13px;color:var(--ink);">
            <div>• <strong>İğde</strong> (<em>E. angustifolia</em>, gölge): 2.000 m²</div>
            <div>• <strong>Meksika tüy otu</strong> (<em>S. tenuissima</em>): 2.000 m²</div>
            <div>• <strong>Oyun çimi</strong> (zorunlu çim): 2.000 m²</div>
            <div>• <strong>Yayılıcı Çin ardıcı</strong> (<em>J. pfitzeriana</em>): 1.700 m²</div>
            <div>• <strong>Civanperçemi</strong> (<em>A. millefolium</em>): 1.500 m²</div>
            <div>• <strong>Arizona servisi</strong> + <strong>Mavi ardıç</strong>: 800 m²</div>
          </div>
        </div>

        <div style="background:var(--green-deep);color:#FFFFFF;border-radius:14px;padding:15px 18px;display:flex;align-items:center;justify-content:space-between;gap:14px;">
          <div>
            <div style="font-size:11.5px;text-transform:uppercase;letter-spacing:0.08em;opacity:0.82;font-weight:700;">Tek Takip Göstergesi (KPI)</div>
            <div style="font-size:16.5px;font-weight:800;margin-top:2px;">Parkta m² başına yıllık sulama suyu (L/m²·yıl, sayaçtan)</div>
          </div>
          <span style="background:rgba(255,255,255,0.18);padding:6px 12px;border-radius:10px;font-size:12px;font-weight:700;white-space:nowrap;">Öncesi vs. Sonrası</span>
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:8px;min-height:0;">
        <div class="chart-frame" style="flex:1;">
          <img src="{img_2040}" alt="2040'lar iklim senaryosu grafiği" />
        </div>
        <div style="font-size:12px;color:var(--muted);line-height:1.4;">
          <strong>Okuma notu:</strong> 2,7 kat, m² başına <em>litre</em> artışının oranı (Ankara: çim +73 L, kurakçıl +27 L). Yüzde artışlar benzer (+%6 / +%8); fark, çimin zaten çok su istemesinden geliyor. <span class="tag hesap">Hesap</span>
        </div>
      </div>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>07 Beklenen Su Etkisi · Ankara 10.000 m² MILP + 7 CMIP6 HighResMIP (yüksek emisyon) hesabı</div>
    <div>08 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 9: 08 İLK TEST VE DOĞRULAMA ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker rose">08 · İlk Test ve Doğrulama</span>
        <h1 class="slide-title">Temel Varsayımımız: Hesabımız Su Tasarrufunu Abartmıyor</h1>
        <p class="slide-sub">Hesap çekirdeğini üç bağımsız kaynakla (ABD sayaç ölçümü, İzmir 10 yıllık fatura, Ankara hakemli çalışma) sınadık.</p>
      </div>
    </div>

    <div class="grid-3" style="margin-bottom:14px;">
      <div class="card rose" style="padding:13px 16px;">
        <div style="font-size:11.5px;font-weight:700;color:var(--rose-deep);">Test 1 · Las Vegas Sayaç (SNWA)</div>
        <div style="font-size:21px;font-weight:800;color:var(--rose-deep);margin:3px 0;">r = 0,96 · %62 vs %76</div>
        <div style="font-size:12.4px;color:var(--ink);line-height:1.38;">Aylık profil tutuyor; hesabımız %62 tasarruf öngörürken gerçek sayaç ölçümü <strong>%76</strong>. Yani <strong>temkinliyiz</strong>.</div>
      </div>

      <div class="card blue" style="padding:13px 16px;">
        <div style="font-size:11.5px;font-weight:700;color:var(--blue-deep);">Test 2 · İzmir Fatura (İZSU, 129 Ay)</div>
        <div style="font-size:21px;font-weight:800;color:var(--blue-deep);margin:3px 0;">r = 0,89 (gecikmeli 0,97)</div>
        <div style="font-size:12.4px;color:var(--ink);line-height:1.38;">Türkiye’deki gerçek park/mezarlık faturalarının mevsimselliğini yakalıyor (1 ay fatura gecikmesi hipotezi ayrı belirtildi).</div>
      </div>

      <div class="card green" style="padding:13px 16px;">
        <div style="font-size:11.5px;font-weight:700;color:var(--green-deep);">Test 3 · Ankara Hakemli Çalışma (Konca vd. 2026)</div>
        <div style="font-size:21px;font-weight:800;color:var(--green-deep);margin:3px 0;">1.190 vs 1.140 L/m²</div>
        <div style="font-size:12.4px;color:var(--ink);line-height:1.38;">Çim için +%4. Batıkent’teki iki satırda −%11 / +%14; <strong>±%10 eşiği sonucu gördükten sonra ±%15’e gevşettik</strong>. Türkiye’de sayaçlı parkta henüz denenmedi.</div>
      </div>
    </div>

    <div class="chart-frame" style="flex:1;min-height:0;max-height:385px;">
      <img src="{img_dogrulama}" alt="Las Vegas SNWA ve İzmir İZSU doğrulama grafikleri" style="max-height:365px;" />
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>08 İlk Test · Not: Tüm su hacmi çıktıları FAO-56 hesabıdır; saha ölçümüyle farkları açıkça raporlanmıştır</div>
    <div>09 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 10: 08 İLK TEST PLANI & GELİŞİM ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker rose">08 · İlk Test Planı ve Gelişim</span>
        <h1 class="slide-title">Hackathon Günü Neyi Sınayacağız, Sonra Nasıl Büyüyecek?</h1>
        <p class="slide-sub">Kabul ölçütlerini sonucu görmeden önce yazıyoruz; geçemeyen yöntem, AI-1’de olduğu gibi açıkça raporlanır.</p>
      </div>
    </div>

    <div class="grid-2" style="gap:20px;">
      <div class="card rose" style="display:flex;flex-direction:column;">
        <div class="card-title">Hackathon Günü · 3 Test</div>
        <ul class="clean rose" style="font-size:13.4px;line-height:1.45;">
          <li><strong>Yapay zekâ: kendi sınıflandırıcımız vs. basit kural.</strong> Sentinel-2 ilkbahar–yaz–sonbahar bantları, etiketler OSM’den. <em>Ölçüt:</em> İzmir 11 ilçede faturayla ρ &gt; 0,85 ve kısmi ρ &gt; 0,70 değilse kural kalır.</li>
          <li><strong>Uydu, ikinci şehir (Ankara).</strong> Batıkent Rekreasyon Alanı (431.600 m², çim+çayır ~%77, Konca vd.) uydu çıktısıyla karşılaştırılır. <em>Ölçüt:</em> fark ±15 puan içinde; değilse İzmir’e aşırı uyum var demektir.</li>
          <li><strong>İklim verisi: ERA5 vs. MGM.</strong> 5–10 ilde MGM 1991–2020 il normalleri (sıcaklık, yağış) ile karşılaştırma. <em>Ölçüt:</em> sapma il il raporlanır ve hesabın belirsizlik bandına eklenir.</li>
        </ul>
      </div>

      <div class="card blue" style="display:flex;flex-direction:column;">
        <div class="card-title">İlk Testten Sonra · Gelişim Yol Haritası</div>
        <ul class="clean blue" style="font-size:13.4px;line-height:1.45;">
          <li><strong>Sayaçlı pilot park:</strong> Bir belediyeyle 1–2 parkta önce/sonra m² başına yıllık sulama ölçülür (tek KPI). Hesap–ölçüm farkıyla bitki katsayısı ve randıman varsayımları kalibre edilir.</li>
          <li><strong>İlçe ölçeği:</strong> Uydu envanterinden “en çok sulanan parklar” öncelik listesi; dönüşüm sırası buna göre planlanır.</li>
          <li><strong>Raporlama:</strong> Peyzaj İzleme Sistemi’nin veri biçimi yayımlanınca EK-1 çıktısı doğrudan aktarılabilir hale getirilir.</li>
          <li><strong>Üretim verisi:</strong> Ücretsiz Open-Meteo API yerine Copernicus CDS / MGM verisi (ticari olmayan kullanım şartı nedeniyle).</li>
        </ul>
      </div>
    </div>

    <div style="margin-top:16px;background:var(--green-deep);color:#FFFFFF;border-radius:14px;padding:13px 22px;display:flex;align-items:center;justify-content:space-between;gap:16px;font-size:14px;">
      <div><strong>Ölçek örneği:</strong> İzmir’in 11 merkez ilçesindeki park/mezarlık suyu (8,37 milyon m³/yıl) yalnız %10 azalsa ≈ 837 bin m³ ≈ <strong>4.650 hanenin</strong> yıllık suyu. %10 bir örnek, hedef değil.</div>
      <span style="background:rgba(255,255,255,0.16);padding:5px 12px;border-radius:999px;font-weight:700;font-size:12px;white-space:nowrap;">Hesap</span>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>08 İlk Test Planı ve Gelişim · Kabul ölçütleri sonuçtan önce yazıldı</div>
    <div>10 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 11: ÇALIŞAN ÜRÜN & CANLI DEMO ════════════════════════ -->
<section class="slide">
  <div class="top-stripe"></div>
  <div class="slide-inner">
    <div class="slide-head">
      <div>
        <span class="kicker blue">Çalışan Prototip · Canlı Demo</span>
        <h1 class="slide-title">Bugün Çalışan 4 Ekranlı Web Uygulaması ve 3 Dakikalık Demo</h1>
        <p class="slide-sub">Yalnızca fikir aşamasında değil: hesap çekirdeği, MILP öneri motoru, 81 il canlı uydu haritası, 2040 projeksiyonu ve EK-1 üreticisi hazır.</p>
      </div>
    </div>

    <div class="grid-2-wide-l" style="min-height:0;">
      <div style="display:flex;flex-direction:column;gap:8px;min-height:0;">
        <div class="chart-frame" style="flex:1;padding:6px;max-height:280px;">
          <img src="{img_izmir_harita}" alt="İzmir merkez uydu sulanan yeşil haritası" style="max-height:266px;" />
        </div>
        <div style="font-size:11.5px;color:var(--muted);text-align:center;">
          İzmir merkez 11 ilçe uydu çıktısı (3,38 km² sulanan kentsel yeşil · ESA WorldCover 2021 &amp; Sentinel-2 2023)
        </div>
        <div class="card green" style="padding:12px 16px;">
          <div class="card-title" style="font-size:14.5px;margin-bottom:6px;">Demoyu Kendiniz Çalıştırın</div>
          <div style="font-size:12.6px;color:var(--ink);line-height:1.45;">
            <strong>Kod:</strong> <a href="{DEMO_LINK}" style="color:var(--green-deep);font-weight:700;">{DEMO_LINK_YAZI}</a> · Python 3 yeterli, hesap için kayıt ya da anahtar gerekmez.
          </div>
          <div style="font-family:Consolas,monospace;font-size:11.8px;background:#FFFFFF;border:1px solid var(--green-border);border-radius:8px;padding:7px 10px;margin-top:7px;line-height:1.55;color:var(--ink);">
            git clone {DEMO_LINK}<br/>
            cd florify<br/>
            python -m pip install -r requirements.txt<br/>
            python web/sunucu.py
          </div>
          <div style="font-size:11.5px;color:var(--muted);margin-top:6px;line-height:1.4;">Komutları satır satır çalıştırın, sonra tarayıcıda <strong style="color:var(--ink);">http://localhost:8000</strong> adresini açın. İlk açılışta ilin iklim verisi internetten iner (birkaç dakika sürebilir); İzmir uydu sonucu repoda hazır.</div>
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:12px;justify-content:space-between;min-height:0;">
        <div class="card" style="padding:14px 18px;border-left:4px solid var(--blue);flex:1;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:14px;font-weight:800;color:var(--blue-deep);">1 · Uydu Haritası (45 sn)</div>
          <div style="font-size:13px;color:var(--muted);margin-top:4px;line-height:1.4;">İzmir’de İZSU doğrulaması (ρ = 0,85), ilçe yakınlaştırma ve 81 il için canlı sulanan yeşil analizi.</div>
        </div>

        <div class="card" style="padding:14px 18px;border-left:4px solid var(--green);flex:1;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:14px;font-weight:800;color:var(--green-deep);">2 · Bitki Önerisi · MILP (45 sn)</div>
          <div style="font-size:13px;color:var(--muted);margin-top:4px;line-height:1.4;">“Dengeli” ayarla gölge ağacı + çalı karışımı üret, tek tıkla <strong>“Park Hesabına Aktar”</strong>.</div>
        </div>

        <div class="card" style="padding:14px 18px;border-left:4px solid var(--rose);flex:1;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:14px;font-weight:800;color:var(--rose-deep);">3 · Park Hesabı &amp; EK-1 Formu (50 sn)</div>
          <div style="font-size:13px;color:var(--muted);margin-top:4px;line-height:1.4;">P10–P90 belirsizlik bandı, m³/TL/hane, ROI ve <strong>CB Kararı 10502 EK-1</strong> taslak çıktısı.</div>
        </div>

        <div class="card" style="padding:14px 18px;border-left:4px solid var(--green-deep);flex:1;display:flex;flex-direction:column;justify-content:center;">
          <div style="font-size:14px;font-weight:800;color:var(--green-deep);">4 · 2040 Senaryosu (40 sn)</div>
          <div style="font-size:13px;color:var(--muted);margin-top:4px;line-height:1.4;">7 CMIP6 modeliyle 2040’lar: çimin m² başına ek su ihtiyacı kurakçılınkinin ~2,7 katı (litre olarak) ile kapanış.</div>
        </div>
      </div>
    </div>
  </div>
  <div class="slide-foot">
    <div class="foot-brand"><span class="foot-dots"><span style="background:var(--green-deep)"></span><span style="background:var(--rose)"></span><span style="background:var(--blue)"></span></span> Florify · Takım Petrichor</div>
    <div>Canlı arayüz: HTML/JS (web/sunucu.py) + Streamlit (app/panel.py) · Otomatik test paketi (pytest)</div>
    <div>11 / 12</div>
  </div>
</section>

<!-- ════════════════════════ SLAYT 12: TAKIM & TEŞEKKÜRLER ════════════════════════ -->
<section class="slide cover-slide">
  <div class="top-stripe"></div>
  <div class="blob" style="width:400px;height:400px;right:-100px;bottom:-120px;background:radial-gradient(circle, rgba(74,137,172,0.20), transparent 70%);"></div>
  <div class="blob" style="width:360px;height:360px;left:-90px;top:-90px;background:radial-gradient(circle, rgba(201,138,146,0.20), transparent 70%);"></div>

  <div class="slide-inner" style="justify-content:space-between;padding:38px 54px 28px;">
    <div style="text-align:center;">
      <span class="kicker green">Takım Petrichor · Water AI Hackathon 2026</span>
      <h1 class="slide-title" style="font-size:40px;margin-top:6px;">
        <span style="color:var(--green-deep);">Flor</span><span style="color:var(--rose-deep);">ify</span> ile Her Damla Veriyle Korunur
      </h1>
      <p class="slide-sub" style="font-size:16px;max-width:740px;margin:8px auto 0;">
        Çimden kurakçıl peyzaja geçişte belediyeler için şeffaf, doğrulanmış ve mevzuata uyumlu karar desteği.
      </p>
    </div>

    <div class="grid-3" style="margin:24px 0;">
      <div class="card" style="text-align:center;padding:24px 20px;border-top:5px solid var(--blue);">
        <div style="width:58px;height:58px;border-radius:50%;background:var(--blue-soft);color:var(--blue-deep);font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">KD</div>
        <div style="font-size:18px;font-weight:800;color:var(--ink);">Kader Demircan</div>
        <div style="font-size:13.5px;color:var(--blue-deep);font-weight:600;margin-top:6px;">Açık Veri &amp; Mekânsal Veri</div>
        <div style="font-size:12.5px;color:var(--muted);margin-top:6px;">Uydu görüntüleri (Sentinel-2, WorldCover), OpenStreetMap ve mekânsal analiz</div>
      </div>

      <div class="card" style="text-align:center;padding:24px 20px;border-top:5px solid var(--rose);">
        <div style="width:58px;height:58px;border-radius:50%;background:var(--rose-soft);color:var(--rose-deep);font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">GNA</div>
        <div style="font-size:18px;font-weight:800;color:var(--ink);">Gül Nihal Arıkaymak</div>
        <div style="font-size:13.5px;color:var(--rose-deep);font-weight:600;margin-top:6px;">Literatür &amp; Botanik Veri</div>
        <div style="font-size:12.5px;color:var(--muted);margin-top:6px;">Akademik makale tabloları, bitki kataloğu (135 tür), mevzuat ve rehber eşleştirme</div>
      </div>

      <div class="card" style="text-align:center;padding:24px 20px;border-top:5px solid var(--green);">
        <div style="width:58px;height:58px;border-radius:50%;background:var(--green-soft);color:var(--green-deep);font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">RA</div>
        <div style="font-size:18px;font-weight:800;color:var(--ink);">Recep Altıntaş</div>
        <div style="font-size:13.5px;color:var(--green-deep);font-weight:600;margin-top:6px;">Kod, Hesap Çekirdeği &amp; Plan</div>
        <div style="font-size:12.5px;color:var(--muted);margin-top:6px;">FAO-56 motoru, MILP optimizasyonu, EK-1 üreticisi, web paneli ve doğrulama testleri</div>
      </div>
    </div>

    <div style="background:rgba(255,255,255,0.88);border:1px solid var(--line);border-radius:16px;padding:16px 24px;display:flex;justify-content:space-between;align-items:center;gap:20px;">
      <div style="font-size:12px;color:var(--muted);line-height:1.5;">
        <strong style="color:var(--green-deep);">Açık Veri Atıfları:</strong> ESA WorldCover 2021 (CC BY 4.0) · Copernicus Sentinel-2 · OpenStreetMap (ODbL) · İZSU / İzmir BB Açık Veri (CC BY 4.0) · Open-Meteo / ERA5 &amp; CMIP6 (CC BY 4.0) · Konca, Ahmad &amp; Apaydın (2026) Water 18:1362 · Sovocool (2005) SNWA · CB Kararı 10502.
      </div>
      <div style="text-align:right;flex-shrink:0;">
        <div style="font-size:14px;font-weight:800;color:var(--green-deep);">Teşekkürler!</div>
        <div style="font-size:12px;color:var(--muted);">Water AI Hackathon · Petrichor</div>
      </div>
    </div>
  </div>
</section>

</div>

<!-- Tarayıcıda sunum gezinme çubuğu (PDF baskıda gizlenir) -->
<div class="nav-bar" id="nav-bar">
  <button onclick="go(-1)">← Önceki</button>
  <span id="counter">1 / 12</span>
  <button onclick="go(1)">Sonraki →</button>
  <button onclick="window.print()">PDF Kaydet</button>
</div>

<script>
  const slides = Array.from(document.querySelectorAll('.slide'));
  let idx = 0;
  const counter = document.getElementById('counter');

  function updateCounter() {{
    counter.textContent = (idx + 1) + ' / ' + slides.length;
  }}
  function go(delta) {{
    idx = Math.max(0, Math.min(slides.length - 1, idx + delta));
    slides[idx].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    updateCounter();
  }}
  window.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{ e.preventDefault(); go(1); }}
    if (e.key === 'ArrowLeft'  || e.key === 'PageUp') {{ e.preventDefault(); go(-1); }}
  }});
  const obs = new IntersectionObserver((entries) => {{
    entries.forEach((en) => {{
      if (en.isIntersecting) {{
        idx = slides.indexOf(en.target);
        updateCounter();
      }}
    }});
  }}, {{ threshold: 0.6 }});
  slides.forEach((s) => obs.observe(s));
</script>
</body>
</html>
"""
    return html


def main():
    html_yol = TESLIM_DIR / "Florify_Sunum.html"
    pdf_yol = TESLIM_DIR / "Florify_Sunum.pdf"
    html_yol.write_text(build_html(), encoding="utf-8")
    print(f"HTML: {html_yol.relative_to(KOK)}")

    # Headless Chrome / Edge ile birebir 16:9 PDF üret
    tarayici = None
    for aday in (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ):
        if aday.exists():
            tarayici = aday
            break

    if tarayici is not None:
        cmd = [
            str(tarayici),
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_yol}",
            html_yol.as_uri(),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and pdf_yol.exists():
            print(f"PDF:  {pdf_yol.relative_to(KOK)} ({pdf_yol.stat().st_size // 1024} KB)")
        else:
            print("Tarayici PDF uretimi basarisiz:", r.returncode, r.stderr[:400])
    else:
        print("Chrome/Edge bulunamadi; HTML uretildi.")

    # Kanvas PDF'ini ayni formatta teslim klasorune kopyala
    kanvas_kaynak = KOK / "kaynaklar" / "hackathon" / "proje_fikri_kanvasi_dolu.pdf"
    kanvas_hedef = TESLIM_DIR / "Florify_Proje_Fikri_Kanvasi.pdf"
    if kanvas_kaynak.exists():
        shutil.copy2(kanvas_kaynak, kanvas_hedef)
        print(f"Kanvas: {kanvas_hedef.relative_to(KOK)} ({kanvas_hedef.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
