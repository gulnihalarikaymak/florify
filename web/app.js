/* Florify — Web Arayüzü (vanilla JS + SVG grafikler, sıfır harici CDN) */
const GRUP_AD = {
  cim: "çim",
  agac_cali: "ağaç / büyük çalı",
  cali_otsu: "çalı / otsu",
  yer_ortucu: "yer örtücü",
  cayir_yonca: "çayır / yonca",
};
const REHBER_AD = {
  ulke_geneli: "Ülke geneli",
  trakya_akdeniz: "Trakya/Akdeniz",
  "ulke_geneli+trakya_akdeniz": "Ülke + Trakya/Akdeniz",
  "": "—",
};
const PRESETS = {
  az_su: { agac: 10, cali: 0, maxpay: 30, minsay: 4 },
  dengeli: { agac: 25, cali: 20, maxpay: 20, minsay: 6 },
  zengin: { agac: 20, cali: 30, maxpay: 12, minsay: 9 },
};

const state = {
  meta: null,
  il: "Ankara",
  aktifView: "park",
  sonPark: null,
  sonOneri: null,
  uydu: null,
  uyduMod: "izmir", // "izmir" | "bolge"
  uyduBolge: null,
  senaryo: null,
  haric: [],
};

const $ = (id) => document.getElementById(id);
const tr = (n, d = 0) =>
  Number(n).toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });

function banner(msg, tip = "error") {
  const el = $("global-banner");
  if (!msg) {
    el.className = "banner hidden";
    el.textContent = "";
    return;
  }
  el.className = `banner ${tip}`;
  el.textContent = msg;
}

async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.hata || `HTTP ${res.status}`);
  return data;
}

/* ────────────────── Tooltip ────────────────── */
const tipEl = $("tooltip");
function showTip(ev, html) {
  tipEl.innerHTML = html;
  tipEl.classList.remove("hidden");
  tipEl.style.left = Math.min(window.innerWidth - 220, ev.clientX + 12) + "px";
  tipEl.style.top = Math.max(10, ev.clientY - 34) + "px";
}
function hideTip() {
  tipEl.classList.add("hidden");
}

function indirCSV(dosyaAdi, basliklar, satirlar) {
  const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const csv = [basliklar.map(esc).join(","), ...satirlar.map((r) => r.map(esc).join(","))].join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = dosyaAdi;
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ────────────────── Başlatma ────────────────── */
async function init() {
  try {
    state.meta = await api("/api/meta");
  } catch (e) {
    banner("Sunucudan başlangıç verisi alınamadı: " + e.message);
    return;
  }

  // Global il seçici + Uydu il seçici senkronu
  const ilSec = $("global-il-sec");
  const uyIlSec = $("uy-il-sec");
  const ilOpts = state.meta.iller.map((il) => `<option value="${il}">${il}</option>`).join("");
  ilSec.innerHTML = ilOpts;
  uyIlSec.innerHTML = ilOpts;
  ilSec.value = "Ankara";
  uyIlSec.value = "İzmir";
  ilSec.addEventListener("change", () => {
    state.il = ilSec.value;
    uyIlSec.value = state.il;
    tarifeGuncelleIl(state.il);
    if (state.aktifView === "park") parkHesapla();
    if (state.aktifView === "oneri") oneriHesapla();
    if (state.aktifView === "senaryo") senaryoYukle();
  });
  uyIlSec.addEventListener("change", () => {
    state.il = uyIlSec.value;
    ilSec.value = state.il;
    tarifeGuncelleIl(state.il);
    if (state.il === "İzmir" && !$("uy-ilce-text").value.trim()) {
      uyduIzmirModu();
    }
  });

  // Tarifeler
  const tSec = $("park-tarife-sec");
  tSec.innerHTML =
    state.meta.tarifeler
      .map(
        (t, idx) =>
          `<option value="${idx}">${t.kurum} · ${t.kategori} (${t.gecerlilik}) · ${tr(t.tl_m3, 2)} TL</option>`
      )
      .join("") + `<option value="elle">Elle gir</option>`;
  tSec.addEventListener("change", () => {
    if (tSec.value !== "elle") {
      const val = state.meta.tarifeler[Number(tSec.value)].tl_m3;
      $("park-tarife-val").value = val;
    }
  });
  tarifeGuncelleIl("Ankara");

  // Hariç tutulacak tür seçici
  const hSec = $("on-haric-sec");
  const tekil = state.meta.bitkiler.slice(2).sort((a, b) => a.turkce_ad.localeCompare(b.turkce_ad, "tr"));
  hSec.innerHTML = tekil
    .map((b) => `<option value="${b.tur}">${b.turkce_ad} (${b.tur})</option>`)
    .join("");

  // Varsayılan park tabloları
  satirEkle("mevcut", { tur: "Çim karışımı, serin iklim (Lolium/Poa/Festuca)", alan: 6000, yontem: "yagmurlama", kd: 1.0 });
  satirEkle("mevcut", { tur: "Buxus sempervirens", alan: 2000, yontem: "damla", kd: 1.0 });

  satirEkle("oneri", { tur: "Çim karışımı, serin iklim (Lolium/Poa/Festuca)", alan: 2000, yontem: "yagmurlama", kd: 1.0 });
  satirEkle("oneri", { tur: "Lavandula angustifolia", alan: 4000, yontem: "damla", kd: 1.0 });
  satirEkle("oneri", { tur: "Buxus sempervirens", alan: 2000, yontem: "damla", kd: 1.0 });

  // Olay dinleyicileri
  document.querySelectorAll(".nav-btn").forEach((btn) =>
    btn.addEventListener("click", () => viewGec(btn.dataset.view))
  );
  document.querySelectorAll("[data-add-row]").forEach((btn) =>
    btn.addEventListener("click", () => satirEkle(btn.dataset.addRow))
  );
  $("btn-park-hesapla").addEventListener("click", parkHesapla);
  $("btn-park-ek1").addEventListener("click", parkEk1Ac);
  $("btn-park-csv").addEventListener("click", () => {
    if (!state.sonPark) return;
    indirCSV(
      `peyzaj_su_${state.il}.csv`,
      ["Peyzaj", "Bölge", "Grup", "Kc", "Yöntem", "Alan (m²)", "L/m²·yıl", "m³/yıl"],
      state.sonPark.bolgeler.map((b) => [
        b.peyzaj,
        b.bolge,
        GRUP_AD[b.grup] || b.grup,
        b.kc,
        b.yontem,
        b.alan_m2,
        b.l_m2_yil,
        b.m3_yil,
      ])
    );
  });

  // Öneri olayları
  $("btn-oneri-hesapla").addEventListener("click", oneriHesapla);
  $("btn-oneri-aktar").addEventListener("click", oneriParkaAktar);
  $("btn-oneri-csv").addEventListener("click", () => {
    if (!state.sonOneri) return;
    indirCSV(
      `bitki_onerisi_${state.il}.csv`,
      ["Tür", "Latince", "EK-1", "Gölge", "Bakanlık 2024", "Kc", "Sulama", "Alan (m²)", "L/m²·yıl", "m³/yıl"],
      state.sonOneri.secim.map((s) => [
        s.turkce_ad,
        s.tur,
        s.ek1_kategori,
        s.golge ? "Evet" : "Hayır",
        REHBER_AD[s.bakanlik_rehberi || ""] || "—",
        s.kc,
        s.yontem,
        Math.round(s.alan_m2),
        Math.round(s.l_m2),
        Math.round(s.m3_yil),
      ])
    );
  });

  document.querySelectorAll("[data-preset]").forEach((btn) =>
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-preset]").forEach((b) => b.classList.toggle("active", b === btn));
      const p = PRESETS[btn.dataset.preset];
      $("on-agac").value = p.agac;
      $("on-cali").value = p.cali;
      $("on-maxpay").value = p.maxpay;
      $("on-minsay").value = p.minsay;
      sliderEtiketleri();
      oneriHesapla();
    })
  );
  ["on-agac", "on-cali", "on-maxpay", "on-minsay"].forEach((id) =>
    $(id).addEventListener("input", sliderEtiketleri)
  );
  $("btn-haric-ekle").addEventListener("click", () => {
    const val = $("on-haric-sec").value;
    if (val && !state.haric.includes(val)) {
      state.haric.push(val);
      haricCiz();
    }
  });

  // Uydu senaryo ve canlı bölge analizi
  $("uy-ilce-sec").addEventListener("change", () => {
    uyduIzmirHaritaGuncelle();
    uyduSenaryoGuncelle();
  });
  $("uy-oran").addEventListener("input", uyduSenaryoGuncelle);
  $("uy-tarife").addEventListener("input", uyduSenaryoGuncelle);
  $("btn-uydu-analiz").addEventListener("click", uyduBolgeAnalizYukle);
  $("btn-uydu-izmir-mod").addEventListener("click", () => {
    $("uy-il-sec").value = "İzmir";
    $("uy-ilce-text").value = "";
    uyduIzmirModu();
  });

  // 2040 senaryo
  $("btn-sen-yukle").addEventListener("click", senaryoYukle);
  $("s2-alan").addEventListener("input", senaryoParkGuncelle);
  $("s2-tarife").addEventListener("input", senaryoParkGuncelle);

  // İlk açılışta Park Hesabını çalıştır
  parkHesapla();
}

function tarifeGuncelleIl(il) {
  const kurum = state.meta.il_kurum[il];
  const tSec = $("park-tarife-sec");
  let val = 100.0;
  if (kurum) {
    let bestIdx = -1, bestTarih = "";
    state.meta.tarifeler.forEach((t, i) => {
      if (t.kurum === kurum && !t.kategori.toLowerCase().includes("geri kazanım") && t.gecerlilik >= bestTarih) {
        bestTarih = t.gecerlilik;
        bestIdx = i;
      }
    });
    if (bestIdx >= 0) {
      tSec.value = String(bestIdx);
      val = state.meta.tarifeler[bestIdx].tl_m3;
    }
  } else {
    tSec.value = "elle";
  }
  $("park-tarife-val").value = val;
  $("on-tarife").value = val;
  $("s2-tarife").value = val;
}

function viewGec(view) {
  state.aktifView = view;
  banner("");
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + view));
  if (view === "oneri" && !state.sonOneri) oneriHesapla();
  if (view === "uydu" && !state.uydu) uyduYukle();
  if (view === "senaryo") senaryoYukle();
}

/* ────────────────── 1. PARK HESABI ────────────────── */
function bitkiSecenekHTML(seciliTur) {
  return state.meta.bitkiler
    .map((b) => {
      const ad = b.tur.startsWith("Çim karışımı") ? b.tur : `${b.turkce_ad} (${b.tur})`;
      const sel = b.tur === seciliTur ? "selected" : "";
      return `<option value="${b.tur}" ${sel}>${ad} · Kc ${String(b.kc_max.toFixed(2)).replace(".", ",")}</option>`;
    })
    .join("");
}

function satirEkle(tabloAd, varsayilan = {}) {
  const tbody = $("tbody-" + tabloAd);
  const b = state.meta.bitkiler.find((x) => x.tur === varsayilan.tur) || state.meta.bitkiler[0];
  const yontem = varsayilan.yontem || (b.grup === "cim" || b.grup === "cayir_yonca" ? "yagmurlama" : "damla");
  const trEl = document.createElement("tr");
  trEl.innerHTML = `
    <td class="col-bitki"><select class="f-tur">${bitkiSecenekHTML(b.tur)}</select></td>
    <td class="col-alan"><input class="f-alan" type="number" min="0" step="100" value="${varsayilan.alan ?? 1000}" /></td>
    <td class="col-yontem">
      <select class="f-yontem">
        <option value="yagmurlama" ${yontem === "yagmurlama" ? "selected" : ""}>Yağmurlama (%70)</option>
        <option value="damla" ${yontem === "damla" ? "selected" : ""}>Damla (%90)</option>
      </select>
    </td>
    <td class="col-kd"><input class="f-kd" type="number" min="0.3" max="1.3" step="0.1" value="${varsayilan.kd ?? 1.0}" /></td>
    <td><button class="btn icon-del" type="button" title="Sil">✕</button></td>
  `;
  trEl.querySelector(".icon-del").addEventListener("click", () => trEl.remove());
  tbody.appendChild(trEl);
}

function tabloOku(tabloAd) {
  const satirlar = [];
  document.querySelectorAll(`#tbody-${tabloAd} tr`).forEach((row) => {
    const tur = row.querySelector(".f-tur").value;
    const b = state.meta.bitkiler.find((x) => x.tur === tur);
    if (!b) return;
    satirlar.push({
      ad: b.tur.startsWith("Çim karışımı") ? b.turkce_ad : `${b.turkce_ad} (${b.tur})`,
      tur: b.tur,
      grup: b.grup,
      kc_max: b.kc_max,
      alan_m2: Number(row.querySelector(".f-alan").value) || 0,
      yontem: row.querySelector(".f-yontem").value,
      kd: Number(row.querySelector(".f-kd").value) || 1.0,
    });
  });
  return satirlar;
}

function parkGovde() {
  return {
    il: state.il,
    ilce: $("park-ilce").value.trim(),
    idare_adi: $("park-idare").value.trim(),
    donem: $("park-donem").value,
    sezon_mart_kasim: $("park-sezon").checked,
    toplam_alan: Number($("park-toplam-alan").value) || 0,
    // Boş alan 0 TL değil: null gönderilir, sunucu ilin varsayılan tarifesini kullanır
    tarife: $("park-tarife-val").value.trim() === "" ? null : Number($("park-tarife-val").value),
    birim_maliyet_tl_m2: Number($("park-maliyet").value) || 0,
    hane: Number($("park-hane").value) || 180,
    mevcut: tabloOku("mevcut"),
    oneri: tabloOku("oneri"),
  };
}

async function parkEk1Ac() {
  banner("");
  const btn = $("btn-park-ek1");
  btn.disabled = true;
  btn.textContent = "Hazırlanıyor…";
  try {
    const res = await fetch("/api/ek1_html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parkGovde()),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.hata || `HTTP ${res.status}`);
    }
    const html = await res.text();
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  } catch (e) {
    banner("EK-1 formu oluşturulamadı: " + e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "📄 EK-1 Formu (CB 10502)";
  }
}

async function parkHesapla() {
  banner("");
  const btn = $("btn-park-hesapla");
  btn.disabled = true;
  btn.textContent = "Hesaplanıyor…";
  try {
    const veri = await api("/api/park", {
      method: "POST",
      body: JSON.stringify(parkGovde()),
    });
    state.sonPark = veri;
    $("park-sub").textContent = `${veri.yer.ad} (${veri.yer.lat.toFixed(2)}, ${veri.yer.lon.toFixed(2)}) · iklim ${veri.yer.y1}–${veri.yer.y2} · FAO-56 hesabı, saha ölçümü değildir.`;

    const uy = $("park-uyari");
    if (veri.uyarilar.length) {
      uy.textContent = veri.uyarilar.join(" ");
      uy.classList.remove("hidden");
    } else {
      uy.classList.add("hidden");
    }

    const o = veri.ozet;
    const bel = veri.belirsizlik;
    $("pk-mevcut").textContent = tr(o.mevcut_m3);
    $("pk-mevcut-bant").textContent = bel ? `P10–P90: ${tr(bel.mevcut_m3.p10)}–${tr(bel.mevcut_m3.p90)}` : "";
    $("pk-oneri").textContent = tr(o.oneri_m3);
    $("pk-oneri-bant").textContent = bel ? `P10–P90: ${tr(bel.oneri_m3.p10)}–${tr(bel.oneri_m3.p90)}` : "";
    $("pk-tasarruf").textContent = tr(o.tasarruf_m3);
    $("pk-yuzde").textContent = bel
      ? `%${tr(o.tasarruf_yuzde, 1)} · P10–P90: ${tr(bel.tasarruf_m3.p10)}–${tr(bel.tasarruf_m3.p90)} m³`
      : `%${tr(o.tasarruf_yuzde, 1)} azalma`;
    $("pk-tl").textContent = tr(o.tasarruf_tl) + " TL";
    $("pk-tl-not").textContent = `${tr(Number($("park-tarife-val").value), 2)} TL/m³, KDV hariç`;
    $("pk-hane").textContent = tr(o.hane_esdegeri);
    $("pk-hane-not").textContent = `Hane başına ${tr(Number($("park-hane").value))} m³/yıl`;

    const roiEl = $("park-roi-bar");
    if (veri.roi && veri.roi.yatirim_tl > 0) {
      const yilMetin = veri.roi.geri_odeme_yil != null ? `≈ ${tr(veri.roi.geri_odeme_yil, 1)} yıl` : "hesaplanamıyor (tasarruf yok)";
      roiEl.innerHTML = `<strong>Tahmini geri ödeme (kullanıcı varsayımı):</strong> ${tr(veri.roi.donusen_alan_m2)} m² dönüşüm × ${tr(veri.roi.birim_maliyet_tl_m2)} TL/m² = <strong>${tr(veri.roi.yatirim_tl)} TL</strong> yatırım · yalnız su tasarrufuyla basit geri ödeme: <strong>${yilMetin}</strong>. <span class="muted">(Bakım ve enerji tasarrufu dahil değildir.)</span>`;
      roiEl.classList.remove("hidden");
    } else {
      roiEl.classList.add("hidden");
    }

    cizCizgiGrafik("chart-park-su", veri.aylik.aylar, [
      { ad: "Mevcut", data: veri.aylik.mevcut_m3, color: "#2563eb" },
      { ad: "Önerilen", data: veri.aylik.oneri_m3, color: "#e05a24" },
    ], "m³ / ay");

    cizGrupBarGrafik("chart-park-iklim", veri.aylik.aylar, [
      { ad: "ET₀", data: veri.aylik.et0_mm, color: "#8a94a6" },
      { ad: "Efektif yağış", data: veri.aylik.peff_mm, color: "#1baf7a" },
    ], "mm / ay");

    $("tbody-park-sonuc").innerHTML = veri.bolgeler
      .map(
        (b) => `<tr>
        <td>${b.peyzaj}</td><td>${b.bolge}</td><td>${GRUP_AD[b.grup] || b.grup}</td>
        <td>${tr(b.kc, 2)}</td><td>${b.yontem === "damla" ? "Damla" : "Yağmurlama"}</td>
        <td>${tr(b.alan_m2)}</td><td>${tr(b.l_m2_yil)}</td><td><strong>${tr(b.m3_yil)}</strong></td>
      </tr>`
      )
      .join("");
  } catch (e) {
    banner(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Hesapla";
  }
}

/* ────────────────── 2. BİTKİ ÖNERİSİ (MILP) ────────────────── */
function sliderEtiketleri() {
  $("lbl-agac").textContent = "%" + $("on-agac").value;
  $("lbl-cali").textContent = "%" + $("on-cali").value;
  $("lbl-maxpay").textContent = "%" + $("on-maxpay").value;
  $("lbl-minsay").textContent = $("on-minsay").value;
}

function haricCiz() {
  $("on-haric-chips").innerHTML = state.haric
    .map((tur) => {
      const b = state.meta.bitkiler.find((x) => x.tur === tur);
      const ad = b ? `${b.turkce_ad} (${b.tur})` : tur;
      return `<span class="tag-chip">${ad}<button type="button" data-del-haric="${tur}">×</button></span>`;
    })
    .join("");
  document.querySelectorAll("[data-del-haric]").forEach((btn) =>
    btn.addEventListener("click", () => {
      state.haric = state.haric.filter((t) => t !== btn.dataset.delHaric);
      haricCiz();
    })
  );
}

async function oneriHesapla() {
  banner("");
  const btn = $("btn-oneri-hesapla");
  btn.disabled = true;
  btn.textContent = "Optimize ediliyor…";
  try {
    const alan = Number($("on-alan").value) || 10000;
    const veri = await api("/api/oneri", {
      method: "POST",
      body: JSON.stringify({
        il: state.il,
        alan_m2: alan,
        zorunlu_cim_m2: Number($("on-zorunlu").value) || 0,
        cim_kc: Number($("on-cim-kc").value),
        min_agac_pay: Number($("on-agac").value) / 100,
        min_cali_pay: Number($("on-cali").value) / 100,
        max_tur_pay: Number($("on-maxpay").value) / 100,
        min_tur_sayisi: Number($("on-minsay").value),
        haric: state.haric,
        tarife: $("on-tarife").value.trim() === "" ? null : Number($("on-tarife").value),
      }),
    });
    state.sonOneri = veri;
    $("btn-oneri-aktar").disabled = false;

    const notEl = $("oneri-ankara-not");
    if (veri.ankara_uyari) {
      notEl.textContent = `Tür havuzu Konca vd. (2026) Ankara çalışmasından derlendi. ${state.il} için su ihtiyacı ${state.il} iklimiyle hesaplanıyor; 81 il için doğrulanmış resmi eşik bulunmadığından otomatik eleme yapılmıyor.`;
      notEl.classList.remove("hidden");
    } else {
      notEl.classList.add("hidden");
    }

    const o = veri.ozet;
    $("on-k-mevcut").textContent = tr(o.mevcut_m3);
    $("on-k-oneri").textContent = tr(o.oneri_m3);
    $("on-k-yuzde").textContent = `−%${tr(o.tasarruf_yuzde, 1)} su`;
    $("on-k-tl").textContent = tr(o.tasarruf_tl) + " TL";
    $("on-k-hane").textContent = tr(o.hane_esdegeri);

    cizYatayPayGrafik("chart-oneri", veri.secim, veri.alan_m2, o.oneri_m3);

    $("tbody-oneri-sonuc").innerHTML = veri.secim
      .map((s) => {
        const ad = s.tur.startsWith("Çim (zorunlu") ? s.turkce_ad : `${s.turkce_ad} <span class="muted">(${s.tur})</span>`;
        const golge = s.golge ? `<span class="badge-mini yes">Evet</span>` : `<span class="muted">—</span>`;
        const rehber = s.bakanlik_rehberi
          ? `<span class="badge-mini ref">${REHBER_AD[s.bakanlik_rehberi] || s.bakanlik_rehberi}</span>`
          : `<span class="muted">—</span>`;
        return `<tr>
          <td>${ad}</td><td>${s.ek1_kategori || "—"}</td><td>${golge}</td><td>${rehber}</td>
          <td>${tr(s.kc, 2)}</td><td>${tr(s.alan_m2)}</td><td><strong>${tr(s.m3_yil)}</strong></td>
        </tr>`;
      })
      .join("");
  } catch (e) {
    banner(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Karışım Öner";
  }
}

function oneriParkaAktar() {
  if (!state.sonOneri) return;
  const alan = Math.round(state.sonOneri.alan_m2);
  $("park-toplam-alan").value = alan;
  $("tbody-mevcut").innerHTML = "";
  satirEkle("mevcut", {
    tur: "Çim karışımı, serin iklim (Lolium/Poa/Festuca)",
    alan: alan,
    yontem: "yagmurlama",
    kd: 1.0,
  });
  $("tbody-oneri").innerHTML = "";
  const cimTur =
    Number($("on-cim-kc").value) <= 0.85
      ? "Çim karışımı, kurağa dayanıklı 5'li (Cynodon/Zoysia katkılı)"
      : "Çim karışımı, serin iklim (Lolium/Poa/Festuca)";
  state.sonOneri.secim.forEach((s) => {
    satirEkle("oneri", {
      tur: s.tur.startsWith("Çim (zorunlu") ? cimTur : s.tur,
      alan: Math.round(s.alan_m2),
      yontem: s.yontem,
      kd: 1.0,
    });
  });
  viewGec("park");
  parkHesapla();
}

/* ────────────────── 3. UYDU HARİTASI (81 İL + İZMİR DOĞRULAMA) ────────────────── */
async function uyduYukle() {
  banner("");
  try {
    const veri = await api("/api/uydu");
    state.uydu = veri;
    const sel = $("uy-ilce-sec");
    sel.innerHTML =
      `<option value="__tum__">Tüm merkez ilçeler (11 ilçe)</option>` +
      veri.ilceler.map((x) => `<option value="${x.ilce}">${x.ilce}</option>`).join("");
    $("tbody-uydu").innerHTML = veri.ilceler
      .map(
        (x) => `<tr>
        <td><strong>${x.ilce}</strong></td><td>${tr(x.sulanan_yesil_m2)}</td>
        <td>${tr(x.izsu_2023_m3)}</td><td>${tr(x.kentsel_m2)}</td><td>%${tr(x.kapsama, 1)}</td>
      </tr>`
      )
      .join("");
    cizUyduScatter("chart-uydu-scatter", veri.ilceler);
    uyduIzmirModu();
  } catch (e) {
    banner("Uydu verisi yüklenemedi: " + e.message, "error");
  }
}

function uyduIzmirModu() {
  if (!state.uydu) return;
  state.uyduMod = "izmir";
  const o = state.uydu.ozet;
  $("uydu-baslik").textContent = "Uydudan sulanan yeşil — İzmir (İZSU doğrulamalı)";
  $("uydu-altbaslik").textContent = "Merkez 11 ilçe · ESA WorldCover 2021 + Sentinel-2 Ağustos 2023 (NDVI > 0,5) · envanter olmadan";
  $("uy-uyari").classList.add("hidden");
  $("uy-bilgi").classList.add("hidden");
  $("uy-scatter-card").classList.remove("hidden");
  $("uy-ilce-sec-wrap").classList.remove("hidden");
  $("uy-ilce-tablo-card").classList.remove("hidden");
  $("uy-grid").className = "two-col";

  $("uy-k1-lbl").textContent = "Sulanan kentsel yeşil";
  $("uy-alan").textContent = tr(o.toplam_yesil_m2 / 1e6, 2) + " km²";
  $("uy-alan-sub").textContent = "11 merkez ilçe toplamı";
  $("uy-hesap").textContent = tr(o.hesaplanan_su_m3 / 1e6, 1) + " milyon m³";
  $("uy-hesap-not").textContent = `Çim varsayımıyla ${tr(o.cim_l_m2)} L/m²·yıl`;
  $("uy-k3-lbl").textContent = "İZSU 2023 faturası";
  $("uy-fatura").textContent = tr(o.toplam_izsu_m3 / 1e6, 1) + " milyon m³";
  $("uy-fatura-sub").textContent = "Park + mezarlık aboneleri";
  $("uy-k4-lbl").textContent = "Fatura ile uyum (Spearman ρ)";
  $("uy-rho").textContent = tr(o.spearman_rho, 2);
  $("uy-rho-not").textContent = `p = ${tr(o.spearman_p, 3)} · kısmi ρ = ${tr(o.kismi_rho, 2)}`;
  $("uy-tarife").value = o.izsu_tarife;
  $("uydu-atif").textContent = state.uydu.atif;

  uyduIzmirHaritaGuncelle();
  uyduSenaryoGuncelle();
}

function uyduIzmirHaritaGuncelle() {
  const sec = $("uy-ilce-sec").value;
  if (!sec || sec === "__tum__") {
    $("uy-harita-baslik").textContent = "İzmir Merkez Haritası (11 ilçe · Yaz 2023)";
    $("uy-harita-alt").textContent = "10×10 m piksel analizi";
    $("uydu-img").src = "/assets/uydu_izmir_harita.png";
  } else {
    $("uy-harita-baslik").textContent = `İzmir / ${sec} — Yakınlaştırılmış Harita`;
    $("uy-harita-alt").textContent = "OSM ilçe sınırı + 10×10 m sulanan yeşil";
    $("uydu-img").src = `/assets/uydu_izmir_ilce.png?ilce=${encodeURIComponent(sec)}`;
  }
}

async function uyduBolgeAnalizYukle() {
  banner("");
  const il = $("uy-il-sec").value;
  const ilce = $("uy-ilce-text").value.trim();
  const yaricap = $("uy-yaricap").value;

  // İzmir'in doğrulanmış 11 ilçesinden biri yazıldıysa anında yakınlaştır
  if (il === "İzmir" && state.uydu) {
    if (!ilce) {
      $("uy-ilce-sec").value = "__tum__";
      uyduIzmirModu();
      return;
    }
    const eslesen = state.uydu.ilceler.find((x) => x.ilce.toLocaleLowerCase("tr") === ilce.toLocaleLowerCase("tr"));
    if (eslesen) {
      $("uy-ilce-sec").value = eslesen.ilce;
      uyduIzmirModu();
      return;
    }
  }

  const btn = $("btn-uydu-analiz");
  btn.disabled = true;
  btn.textContent = "Uydu verisi okunuyor (~15–30 sn)…";
  try {
    const qs = new URLSearchParams({ il, ilce, yaricap });
    const veri = await api(`/api/uydu_bolge?${qs.toString()}`);
    state.uyduMod = "bolge";
    state.uyduBolge = veri;

    const o = veri.ozet;
    const cap = 2 * veri.analiz.yaricap_km;
    $("uydu-baslik").textContent = `Uydudan sulanan yeşil — ${veri.yer.ad}`;
    $("uydu-altbaslik").textContent =
      `${cap}×${cap} km merkez penceresi (${veri.yer.lat.toFixed(2)}, ${veri.yer.lon.toFixed(2)}) · ${veri.analiz.sahne_sayisi} Sentinel-2 sahnesi · yaz ${veri.analiz.yil}`;

    const uyEl = $("uy-uyari");
    if (veri.yaz_yagis_uyari) {
      uyEl.textContent = veri.yaz_yagis_uyari;
      uyEl.classList.remove("hidden");
    } else {
      uyEl.classList.add("hidden");
    }
    const bEl = $("uy-bilgi");
    bEl.textContent =
      "Not: Belediye sulama faturası doğrulaması yalnız İzmir (İZSU, ρ = 0,85) için mevcuttur. Bu görünüm açık uydu görüntüsü ve o ilin ERA5 iklimiyle yapılan FAO-56 hesabını gösterir.";
    bEl.classList.remove("hidden");

    $("uy-scatter-card").classList.add("hidden");
    $("uy-ilce-sec-wrap").classList.add("hidden");
    $("uy-ilce-tablo-card").classList.add("hidden");
    $("uy-grid").className = "";

    $("uy-k1-lbl").textContent = "Sulanan kentsel yeşil";
    $("uy-alan").textContent =
      o.sulanan_yesil_m2 >= 1e6 ? tr(o.sulanan_yesil_m2 / 1e6, 2) + " km²" : tr(o.sulanan_yesil_m2) + " m²";
    $("uy-alan-sub").textContent = `${cap}×${cap} km merkez penceresinde`;
    $("uy-hesap").textContent = tr(o.hesaplanan_su_m3) + " m³/yıl";
    $("uy-hesap-not").textContent = `${il} iklimiyle ${tr(o.cim_l_m2)} L/m²·yıl`;
    $("uy-k3-lbl").textContent = "Kentsel alan (pencere)";
    $("uy-fatura").textContent = tr(o.kentsel_m2 / 1e6, 2) + " km²";
    $("uy-fatura-sub").textContent = `Kuru çim: ${tr(o.kuru_cim_m2 / 1e3)} bin m²`;
    $("uy-k4-lbl").textContent = "Temmuz–Ağustos yağışı";
    $("uy-rho").textContent = tr(o.yaz_yagis_mm, 0) + " mm";
    $("uy-rho-not").textContent = o.yaz_yagis_mm >= 60 ? "Yüksek — doğal yeşil karışabilir" : "Kurak yaz — kural uygun";

    $("uy-harita-baslik").textContent = `${veri.yer.ad} — Sulanan Kentsel Yeşil (${cap}×${cap} km)`;
    $("uy-harita-alt").textContent = "ESA WorldCover 2021 + Sentinel-2 L2A (10×10 m)";
    $("uydu-img").src = `${veri.harita_url}?t=${Date.now()}`;
    $("uy-tarife").value = o.varsayilan_tarife;
    $("uydu-atif").textContent = veri.atif;

    uyduSenaryoGuncelle();
  } catch (e) {
    banner("Canlı uydu analizi başarısız: " + e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Uydu Haritasını Çıkar";
  }
}

function uyduSenaryoGuncelle() {
  const oran = Number($("uy-oran").value);
  const tarife = Number($("uy-tarife").value) || 0;
  $("lbl-uy-oran").textContent = "%" + oran;

  let alan = 0, cim_l = 0, kurak_l = 0, hane_m3 = 180, yerEtiket = "İzmir";
  if (state.uyduMod === "bolge" && state.uyduBolge) {
    const o = state.uyduBolge.ozet;
    alan = o.sulanan_yesil_m2;
    cim_l = o.cim_l_m2;
    kurak_l = o.kurak_l_m2;
    hane_m3 = o.hane_m3_yil;
    yerEtiket = state.uyduBolge.yer.ad;
  } else if (state.uydu) {
    const sec = $("uy-ilce-sec").value;
    const o = state.uydu.ozet;
    alan =
      sec === "__tum__"
        ? o.toplam_yesil_m2
        : state.uydu.ilceler.find((x) => x.ilce === sec)?.sulanan_yesil_m2 || 0;
    cim_l = o.cim_l_m2;
    kurak_l = o.kurak_l_m2;
    hane_m3 = o.hane_m3_yil;
    yerEtiket = sec === "__tum__" ? "İzmir merkez" : `İzmir / ${sec}`;
  } else {
    return;
  }

  const mevcut = (alan * cim_l) / 1000;
  const sonra = (alan * (1 - oran / 100) * cim_l + alan * (oran / 100) * kurak_l) / 1000;
  const fark = mevcut - sonra;
  const yuzde = mevcut ? (100 * fark) / mevcut : 0;

  $("uy-s-mevcut").textContent = tr(mevcut);
  $("uy-s-sonra").textContent = tr(sonra);
  $("uy-s-yuzde").textContent = `−%${tr(yuzde, 1)} su`;
  $("uy-s-tl").textContent = tr(fark * tarife) + " TL";
  $("uy-s-hane").textContent = tr(fark / hane_m3);
  $("uy-senaryo-not").textContent =
    `${yerEtiket} varsayımı: mevcut sulanan yeşilin tamamı çim (Kc 0,95, yağmurlama, ${tr(cim_l)} L/m²); dönüşen kısım kurakçıl (Kc 0,50, damla, ${tr(kurak_l)} L/m²). Bir kısmı zaten çalı olabileceği için tasarruf üst sınırdır.`;
}

/* ────────────────── 4. 2040 SENARYOSU ────────────────── */
async function senaryoYukle() {
  banner("");
  const btn = $("btn-sen-yukle");
  btn.disabled = true;
  btn.textContent = "Modeller alınıyor…";
  try {
    const veri = await api(`/api/senaryo2040?il=${encodeURIComponent(state.il)}`);
    state.senaryo = veri;
    const o = veri.ozet;
    $("sen-sub").textContent = `${veri.yer.ad} · 7 CMIP6 HighResMIP modeli (yüksek emisyon) · ${veri.gelecek[0]}–${veri.gelecek[1]} vs ${veri.taban[0]}–${veri.taban[1]} normali`;
    $("s2-cim-bugun").textContent = tr(o.cim_bugun_l);
    $("s2-cim-2040").textContent = tr(o.cim_2040_l);
    $("s2-cim-artis").textContent = `+${tr(o.cim_artis_l)} L (+%${tr(o.cim_artis_yuzde, 1)})`;
    $("s2-kur-2040").textContent = tr(o.kurak_2040_l);
    $("s2-kur-artis").textContent = `+${tr(o.kurak_artis_l)} L (bugün ${tr(o.kurak_bugun_l)} L)`;
    $("s2-mod-say").textContent = `${o.artis_model_sayisi} / ${o.toplam_model}`;

    const msj = $("sen-mesaj");
    if (o.kat_fark) {
      msj.innerHTML = `<strong>Çimin m² başına artışı, kurakçıl peyzajınkinin yaklaşık ${tr(o.kat_fark, 1)} katı.</strong> Çimi dönüştürmek bugün su kazandırmanın yanında gelecekteki iklim riskini de azaltıyor.`;
      msj.classList.remove("hidden");
    } else {
      msj.classList.add("hidden");
    }

    ciz2040Grafik("chart-2040", veri.aylik);

    $("tbody-2040").innerHTML = veri.modeller
      .map(
        (m) => `<tr>
        <td><strong>${m.model}</strong></td>
        <td>${m.et0_degisim_yuzde >= 0 ? "+" : ""}${tr(m.et0_degisim_yuzde, 1)}%</td>
        <td>${m.yagis_degisim_yuzde >= 0 ? "+" : ""}${tr(m.yagis_degisim_yuzde, 1)}%</td>
        <td>${tr(m.cim_2040)}</td><td>${tr(m.kurak_2040)}</td>
      </tr>`
      )
      .join("");

    senaryoParkGuncelle();
  } catch (e) {
    banner("2040 senaryosu alınamadı: " + e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Güncelle";
  }
}

function senaryoParkGuncelle() {
  if (!state.senaryo) return;
  const alan = Number($("s2-alan").value) || 0;
  const tarife = Number($("s2-tarife").value) || 0;
  const o = state.senaryo.ozet;
  const ek = (alan * o.cim_artis_l) / 1000;
  const cimTop = (alan * o.cim_2040_l) / 1000;
  const kurTop = (alan * o.kurak_2040_l) / 1000;
  const fark = cimTop - kurTop;
  $("s2-p-ek").textContent = "+" + tr(ek);
  $("s2-p-cim").textContent = tr(cimTop);
  $("s2-p-kur").textContent = tr(kurTop);
  $("s2-p-fark").textContent = `−${tr(fark)} m³ · ${tr(fark * tarife)} TL/yıl`;
}

/* ────────────────── SVG GRAFİKLER ────────────────── */
function cizCizgiGrafik(hostId, labels, series, yTitle) {
  const W = 560, H = 250, P = { l: 50, r: 16, t: 16, b: 30 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const maxY = Math.max(10, ...series.flatMap((s) => s.data)) * 1.12;
  const sx = (i) => P.l + (i / (labels.length - 1)) * iw;
  const sy = (v) => P.t + ih - (v / maxY) * ih;

  let grid = "";
  for (let k = 0; k <= 4; k++) {
    const val = (maxY * k) / 4;
    const y = sy(val);
    grid += `<line x1="${P.l}" y1="${y}" x2="${W - P.r}" y2="${y}" stroke="#e6ebf1" />
             <text x="${P.l - 8}" y="${y + 4}" text-anchor="end" font-size="10.5" fill="#64748b">${tr(val)}</text>`;
  }
  const xLabels = labels
    .map((l, i) => `<text x="${sx(i)}" y="${H - 8}" text-anchor="middle" font-size="10.5" fill="#64748b">${l}</text>`)
    .join("");

  let paths = "", dots = "";
  series.forEach((s) => {
    const d = s.data.map((v, i) => `${i === 0 ? "M" : "L"}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
    paths += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2.4" />`;
    s.data.forEach((v, i) => {
      dots += `<circle cx="${sx(i).toFixed(1)}" cy="${sy(v).toFixed(1)}" r="4" fill="${s.color}" stroke="#fff" stroke-width="1.5"
        data-tip="<strong>${s.ad} · ${labels[i]}</strong><br/>${tr(v)} ${yTitle}" />`;
    });
  });

  $(hostId).innerHTML = `<svg viewBox="0 0 ${W} ${H}">${grid}${xLabels}${paths}${dots}</svg>`;
  baglaTip($(hostId));
}

function cizGrupBarGrafik(hostId, labels, series, yTitle) {
  const W = 440, H = 250, P = { l: 44, r: 12, t: 16, b: 30 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const maxY = Math.max(10, ...series.flatMap((s) => s.data)) * 1.12;
  const sy = (v) => P.t + ih - (v / maxY) * ih;
  const step = iw / labels.length;
  const bw = Math.max(6, (step - 8) / series.length);

  let grid = "";
  for (let k = 0; k <= 4; k++) {
    const val = (maxY * k) / 4;
    const y = sy(val);
    grid += `<line x1="${P.l}" y1="${y}" x2="${W - P.r}" y2="${y}" stroke="#e6ebf1" />
             <text x="${P.l - 6}" y="${y + 4}" text-anchor="end" font-size="10.5" fill="#64748b">${tr(val)}</text>`;
  }
  let bars = "", xLabels = "";
  labels.forEach((l, i) => {
    const gx = P.l + i * step + 4;
    xLabels += `<text x="${P.l + (i + 0.5) * step}" y="${H - 8}" text-anchor="middle" font-size="10" fill="#64748b">${l}</text>`;
    series.forEach((s, j) => {
      const v = s.data[i];
      const y = sy(v);
      const h = Math.max(0, P.t + ih - y);
      bars += `<rect x="${(gx + j * bw).toFixed(1)}" y="${y.toFixed(1)}" width="${(bw - 1).toFixed(1)}" height="${h.toFixed(1)}"
        rx="2" fill="${s.color}" data-tip="<strong>${s.ad} · ${l}</strong><br/>${tr(v)} ${yTitle}" />`;
    });
  });

  $(hostId).innerHTML = `<svg viewBox="0 0 ${W} ${H}">${grid}${xLabels}${bars}</svg>`;
  baglaTip($(hostId));
}

function cizYatayPayGrafik(hostId, secim, topAlan, topSu) {
  const rowH = 38, P = { l: 175, r: 42, t: 10, b: 22 };
  const W = 520, H = P.t + P.b + secim.length * rowH;
  const iw = W - P.l - P.r;
  const maxP = Math.max(25, ...secim.flatMap((s) => [(100 * s.alan_m2) / topAlan, topSu ? (100 * s.m3_yil) / topSu : 0])) * 1.1;
  const sx = (p) => P.l + (p / maxP) * iw;

  let grid = "";
  [0, 20, 40, 60, 80].filter((v) => v <= maxP).forEach((v) => {
    const x = sx(v);
    grid += `<line x1="${x}" y1="${P.t}" x2="${x}" y2="${H - P.b}" stroke="#e6ebf1" />
             <text x="${x}" y="${H - 5}" text-anchor="middle" font-size="10" fill="#64748b">%${v}</text>`;
  });

  let rows = "";
  secim.forEach((s, i) => {
    const y = P.t + i * rowH;
    const pAlan = (100 * s.alan_m2) / topAlan;
    const pSu = topSu ? (100 * s.m3_yil) / topSu : 0;
    const lbl = s.turkce_ad.length > 23 ? s.turkce_ad.slice(0, 22) + "…" : s.turkce_ad;
    rows += `
      <text x="${P.l - 8}" y="${y + 19}" text-anchor="end" font-size="11.5" fill="#18202c">${lbl}</text>
      <rect x="${P.l}" y="${y + 5}" width="${Math.max(2, sx(pAlan) - P.l).toFixed(1)}" height="11" rx="3" fill="#2563eb"
        data-tip="<strong>${s.turkce_ad}</strong><br/>Alan: ${tr(s.alan_m2)} m² (%${tr(pAlan, 1)})" />
      <rect x="${P.l}" y="${y + 18}" width="${Math.max(2, sx(pSu) - P.l).toFixed(1)}" height="11" rx="3" fill="#e05a24"
        data-tip="<strong>${s.turkce_ad}</strong><br/>Su: ${tr(s.m3_yil)} m³/yıl (%${tr(pSu, 1)})" />`;
  });

  $(hostId).innerHTML = `<svg viewBox="0 0 ${W} ${H}">${grid}${rows}</svg>`;
  baglaTip($(hostId));
}

function cizUyduScatter(hostId, ilceler) {
  const W = 500, H = 330, P = { l: 58, r: 26, t: 18, b: 42 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const maxX = Math.max(...ilceler.map((d) => d.sulanan_yesil_m2 / 1e3)) * 1.15;
  const maxY = Math.max(...ilceler.map((d) => d.izsu_2023_m3 / 1e3)) * 1.15;
  const sx = (v) => P.l + (v / maxX) * iw;
  const sy = (v) => P.t + ih - (v / maxY) * ih;

  let grid = "";
  for (let k = 0; k <= 4; k++) {
    const xv = (maxX * k) / 4, yv = (maxY * k) / 4;
    grid += `<line x1="${P.l}" y1="${sy(yv)}" x2="${W - P.r}" y2="${sy(yv)}" stroke="#e6ebf1" />
             <text x="${P.l - 8}" y="${sy(yv) + 4}" text-anchor="end" font-size="10.5" fill="#64748b">${tr(yv)}</text>
             <text x="${sx(xv)}" y="${H - 22}" text-anchor="middle" font-size="10.5" fill="#64748b">${tr(xv)}</text>`;
  }
  const axes = `
    <text x="${P.l + iw / 2}" y="${H - 4}" text-anchor="middle" font-size="11" fill="#5b6778">Uydudan sulanan yeşil (bin m²)</text>
    <text x="14" y="${P.t + ih / 2}" text-anchor="middle" font-size="11" fill="#5b6778" transform="rotate(-90 14 ${P.t + ih / 2})">İZSU 2023 faturası (bin m³)</text>`;

  const pts = ilceler
    .map((d) => {
      const cx = sx(d.sulanan_yesil_m2 / 1e3).toFixed(1);
      const cy = sy(d.izsu_2023_m3 / 1e3).toFixed(1);
      return `<g class="scatter-pt" data-ilce="${d.ilce}" style="cursor:pointer;">
        <circle cx="${cx}" cy="${cy}" r="6.5" fill="#2563eb" fill-opacity="0.88" stroke="#fff" stroke-width="1.5"
          data-tip="<strong>${d.ilce}</strong><br/>Sulanan yeşil: ${tr(d.sulanan_yesil_m2)} m²<br/>İZSU 2023: ${tr(d.izsu_2023_m3)} m³" />
        <text x="${Number(cx) + 9}" y="${Number(cy) + 3}" font-size="10.5" fill="#475569">${d.ilce}</text>
      </g>`;
    })
    .join("");

  $(hostId).innerHTML = `<svg viewBox="0 0 ${W} ${H}">${grid}${axes}${pts}</svg>`;
  baglaTip($(hostId));
  $(hostId).querySelectorAll(".scatter-pt").forEach((g) =>
    g.addEventListener("click", () => {
      $("uy-ilce-sec").value = g.dataset.ilce;
      uyduIzmirHaritaGuncelle();
      uyduSenaryoGuncelle();
    })
  );
}

function ciz2040Grafik(hostId, aylik) {
  const W = 780, H = 290, P = { l: 50, r: 20, t: 18, b: 30 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const maxY = Math.max(20, ...aylik.map((d) => Math.max(d.cim_max, d.cim_bugun))) * 1.1;
  const sx = (i) => P.l + (i / (aylik.length - 1)) * iw;
  const sy = (v) => P.t + ih - (v / maxY) * ih;

  let grid = "";
  for (let k = 0; k <= 4; k++) {
    const val = (maxY * k) / 4;
    const y = sy(val);
    grid += `<line x1="${P.l}" y1="${y}" x2="${W - P.r}" y2="${y}" stroke="#e6ebf1" />
             <text x="${P.l - 8}" y="${y + 4}" text-anchor="end" font-size="10.5" fill="#64748b">${tr(val)}</text>`;
  }
  const xLabels = aylik
    .map((d, i) => `<text x="${sx(i)}" y="${H - 8}" text-anchor="middle" font-size="11" fill="#64748b">${d.ay}</text>`)
    .join("");

  function band(minK, maxK, color) {
    const top = aylik.map((d, i) => `${sx(i).toFixed(1)},${sy(d[maxK]).toFixed(1)}`).join(" ");
    const bot = [...aylik].reverse().map((d, idx) => `${sx(aylik.length - 1 - idx).toFixed(1)},${sy(d[minK]).toFixed(1)}`).join(" ");
    return `<polygon points="${top} ${bot}" fill="${color}" fill-opacity="0.16" />`;
  }
  function line(key, color, dash = "") {
    const d = aylik.map((r, i) => `${i === 0 ? "M" : "L"}${sx(i).toFixed(1)},${sy(r[key]).toFixed(1)}`).join(" ");
    return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${dash ? 1.6 : 2.6}" ${dash ? `stroke-dasharray="${dash}"` : ""} />`;
  }

  let dots = "";
  aylik.forEach((d, i) => {
    dots += `<circle cx="${sx(i).toFixed(1)}" cy="${sy(d.cim_medyan).toFixed(1)}" r="4.5" fill="#2563eb" stroke="#fff" stroke-width="1.5"
      data-tip="<strong>Çim · ${d.ay}</strong><br/>Bugün: ${tr(d.cim_bugun)} L/m²<br/>2040'lar: ${tr(d.cim_medyan)} L/m² (${tr(d.cim_min)}–${tr(d.cim_max)})" />`;
    dots += `<circle cx="${sx(i).toFixed(1)}" cy="${sy(d.kurak_medyan).toFixed(1)}" r="4.5" fill="#e05a24" stroke="#fff" stroke-width="1.5"
      data-tip="<strong>Kurakçıl · ${d.ay}</strong><br/>Bugün: ${tr(d.kurak_bugun)} L/m²<br/>2040'lar: ${tr(d.kurak_medyan)} L/m² (${tr(d.kurak_min)}–${tr(d.kurak_max)})" />`;
  });

  $(hostId).innerHTML = `<svg viewBox="0 0 ${W} ${H}">
    ${grid}${xLabels}
    ${band("cim_min", "cim_max", "#2563eb")}
    ${band("kurak_min", "kurak_max", "#e05a24")}
    ${line("cim_bugun", "#2563eb", "5 4")}
    ${line("kurak_bugun", "#e05a24", "5 4")}
    ${line("cim_medyan", "#2563eb")}
    ${line("kurak_medyan", "#e05a24")}
    ${dots}
  </svg>`;
  baglaTip($(hostId));
}

function baglaTip(container) {
  container.querySelectorAll("[data-tip]").forEach((el) => {
    el.addEventListener("mousemove", (ev) => showTip(ev, el.dataset.tip));
    el.addEventListener("mouseleave", hideTip);
  });
}

init();
