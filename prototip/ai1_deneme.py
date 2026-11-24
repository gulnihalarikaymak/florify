"""AI-1 fizibilite denemesi: 1–3 ay sonrasının sulama ihtiyacını, basit kıyaslardan iyi tahmin edebilir miyiz?

Hedef:      ay t+h'nin net sulama ihtiyacı, Kc = 1 için (mm) = max(0, ET0 − Peff). Yalnız Nisan–Ekim ayları.
Tahmin:     t ayının sonunda, yalnız o güne kadar bilinen ERA5 verisiyle (h = 1, 2, 3).
Kıyaslar:   (1) sabit klimatoloji: 1991–2014 ortalaması
            (2) kayan klimatoloji: aynı ayın son 10 yıl ortalaması (ısınma trendini içerir, daha zor rakip)
            (3) persistence: kayan klimatoloji + t ayındaki sapma
Model:      tüm illerde ortak tek LightGBM; hedef = kayan klimatolojiden sapma.
Bölme:      eğitim 1991–2014, test 2015–2025/09 (yıl bazında; aynı yıl iki kümeye girmez).
Skor:       skill = 1 − MAE_model / MAE_kıyas; güven aralığı test yıllarının bootstrap'ıyla.

Çalıştırma: .venv\\Scripts\\python prototip\\ai1_deneme.py
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))
from src.hesap import efektif_yagis  # noqa: E402
from src.veri import aylik_seri, iklim_gunluk  # noqa: E402
from src.veri.konum import konum_bul  # noqa: E402

CIKTI = KOK / "prototip" / "cikti"
ILLER = ["Ankara", "İzmir", "İstanbul", "Antalya", "Konya", "Adana", "Diyarbakır", "Erzurum", "Kayseri",
         "Bursa", "Eskişehir", "Gaziantep", "Samsun", "Trabzon", "Van", "Denizli", "Şanlıurfa", "Sivas",
         "Edirne", "Mersin"]
if len(sys.argv) > 1:  # ör. "10": yalnız ilk 10 il (Open-Meteo saatlik sınırı nedeniyle)
    ILLER = ILLER[:int(sys.argv[1])]
BAS, BIT = "1981-01-01", "2025-09-30"
EGITIM_SON, TEST_BAS = 2014, 2015
HEDEF_AYLAR = range(4, 11)  # Nisan–Ekim
DEGISKEN = ["ihtiyac", "et0", "yagis", "sicaklik"]
PARAM = dict(objective="regression_l1", learning_rate=0.03, n_estimators=400, num_leaves=15,
             min_child_samples=40, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
             reg_lambda=1.0, verbose=-1, random_state=0)


def veri_hazirla():
    satirlar = []
    for il in ILLER:
        _, lat, lon = konum_bul(il)
        for (y, a), d in aylik_seri(iklim_gunluk(lat, lon, BAS, BIT)).items():
            satirlar.append({"il": il, "lat": lat, "lon": lon, "yil": y, "ay": a, "et0": d["et0"],
                             "yagis": d["yagis"], "sicaklik": d["sicaklik"],
                             "ihtiyac": max(0.0, d["et0"] - efektif_yagis(d["yagis"]))})
    df = pd.DataFrame(satirlar).sort_values(["il", "yil", "ay"]).reset_index(drop=True)
    df = df[(df.yil < 2025) | (df.ay <= 9)]  # son ay yarım olmasın

    # Kayan klimatoloji: aynı il ve ayın ÖNCEKİ 10 yılı (o tarihte bilinen bilgi)
    for v in DEGISKEN:
        df[f"k10_{v}"] = (df.groupby(["il", "ay"])[v]
                          .transform(lambda s: s.shift(1).rolling(10, min_periods=10).mean()))
        df[f"s_{v}"] = df[v] - df[f"k10_{v}"]  # sapma
    # Sabit klimatoloji: yalnız eğitim yılları (1991–2014)
    sabit = df[(df.yil >= 1991) & (df.yil <= EGITIM_SON)].groupby(["il", "ay"])["ihtiyac"].mean()
    df["k_sabit"] = df.set_index(["il", "ay"]).index.map(sabit)
    df["t"] = df.yil * 12 + df.ay - 1
    return df


def ornekler(df, h):
    """t ayı sonunda verilen tahmin → hedef t+h. Özellikler yalnız t ve öncesi."""
    g = df.set_index(["il", "t"])
    ozellik = {}
    for gecikme in range(0, 3):
        for v in DEGISKEN:
            ozellik[f"s_{v}_l{gecikme}"] = g.groupby(level=0)[f"s_{v}"].shift(gecikme)
    ozellik["yagis_s_3ay"] = g.groupby(level=0)["s_yagis"].transform(lambda s: s.rolling(3).sum())
    ozellik["yagis_s_6ay"] = g.groupby(level=0)["s_yagis"].transform(lambda s: s.rolling(6).sum())
    ozellik["sicaklik_s_3ay"] = g.groupby(level=0)["s_sicaklik"].transform(lambda s: s.rolling(3).mean())
    X = pd.DataFrame(ozellik)
    hedef = g.groupby(level=0)[["ihtiyac", "k10_ihtiyac", "k_sabit", "ay", "yil", "lat", "lon"]].shift(-h)
    hedef.columns = ["y", "k10", "k_sabit", "hedef_ay", "hedef_yil", "lat", "lon"]
    X = X.join(hedef).join(g[["s_ihtiyac"]].rename(columns={"s_ihtiyac": "simdiki_sapma"}))
    X = X.dropna(subset=["y", "k10", "s_ihtiyac_l2", "yagis_s_6ay"])
    X = X[X.hedef_ay.isin(HEDEF_AYLAR)]
    X["h"] = h
    return X.reset_index()


OZELLIKLER = None


def deney(df):
    global OZELLIKLER
    sonuc, tahminler = {}, []
    for h in (1, 2, 3):
        X = ornekler(df, h)
        OZELLIKLER = [c for c in X.columns if c.startswith(("s_", "yagis_s", "sicaklik_s"))] + \
                     ["hedef_ay", "lat", "lon", "k10"]
        egit = X[(X.hedef_yil >= 1991) & (X.hedef_yil <= EGITIM_SON)]
        test = X[X.hedef_yil >= TEST_BAS].copy()
        model = lgb.LGBMRegressor(**PARAM).fit(egit[OZELLIKLER], egit.y - egit.k10)
        test["p_model"] = test.k10 + model.predict(test[OZELLIKLER])
        test["p_model"] = test.p_model.clip(lower=0)
        test["p_k10"] = test.k10
        test["p_sabit"] = test.k_sabit
        test["p_pers"] = (test.k10 + test.simdiki_sapma).clip(lower=0)
        tahminler.append(test)
        onem = pd.Series(model.booster_.feature_importance("gain"), index=OZELLIKLER)
        sonuc[h] = {"n_egitim": len(egit), "n_test": len(test),
                    "ozellik_onemi_ilk5": (onem / onem.sum()).sort_values(ascending=False).head(5)
                    .round(3).to_dict()}
    return pd.concat(tahminler), sonuc


def skorla(T, rng=np.random.default_rng(0), B=2000):
    yontemler = {"model": "p_model", "kayan_klimatoloji": "p_k10", "sabit_klimatoloji": "p_sabit",
                 "persistence": "p_pers"}
    yillar = np.sort(T.hedef_yil.unique())
    tablo = {}
    for h, Th in T.groupby("h"):
        hata = {k: (Th[c] - Th.y).abs() for k, c in yontemler.items()}
        mae = {k: float(v.mean()) for k, v in hata.items()}
        # Yıl bazında bootstrap (aynı yılın illeri birbirine bağımlı)
        yil_gr = {y: Th.hedef_yil.values == y for y in yillar}
        skill_ornek = {"kayan_klimatoloji": [], "sabit_klimatoloji": []}
        for _ in range(B):
            secim = rng.choice(yillar, len(yillar))
            maske = np.concatenate([np.where(yil_gr[y])[0] for y in secim])
            m = hata["model"].values[maske].mean()
            for k in skill_ornek:
                skill_ornek[k].append(1 - m / hata[k].values[maske].mean())
        tablo[int(h)] = {
            "MAE_mm": {k: round(v, 2) for k, v in mae.items()},
            "skill_vs_kayan_klimatoloji": round(1 - mae["model"] / mae["kayan_klimatoloji"], 3),
            "skill_vs_kayan_klim_%90_GA": [round(float(np.percentile(skill_ornek["kayan_klimatoloji"], q)), 3)
                                           for q in (5, 95)],
            "skill_vs_sabit_klimatoloji": round(1 - mae["model"] / mae["sabit_klimatoloji"], 3),
            "skill_vs_sabit_klim_%90_GA": [round(float(np.percentile(skill_ornek["sabit_klimatoloji"], q)), 3)
                                          for q in (5, 95)],
            "skill_persistence_vs_kayan": round(1 - mae["persistence"] / mae["kayan_klimatoloji"], 3),
            "ortalama_ihtiyac_mm": round(float(Th.y.mean()), 1),
        }
    # İl bazında h=1 skill (kayan klimatolojiye göre)
    T1 = T[T.h == 1]
    il_skill = {il: round(1 - (g.p_model - g.y).abs().mean() / (g.p_k10 - g.y).abs().mean(), 3)
                for il, g in T1.groupby("il")}
    # Yaz bütçesi: Mayıs sonunda verilen Haziran+Temmuz+Ağustos toplamı (h=1,2,3)
    yaz = T[(T.hedef_ay.isin([6, 7, 8])) & ((T.hedef_ay - T.h) == 5)]
    yaz = yaz.groupby(["il", "hedef_yil"])[["y", "p_model", "p_k10", "p_sabit"]].sum()
    yaz_mae = {k: round(float((yaz[k] - yaz.y).abs().mean()), 1) for k in ("p_model", "p_k10", "p_sabit")}
    return tablo, il_skill, {"MAE_mm": yaz_mae, "ortalama_yaz_ihtiyaci_mm": round(float(yaz.y.mean()), 1),
                             "skill_vs_kayan": round(1 - yaz_mae["p_model"] / yaz_mae["p_k10"], 3),
                             "skill_vs_sabit": round(1 - yaz_mae["p_model"] / yaz_mae["p_sabit"], 3)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    df = veri_hazirla()
    T, bilgi = deney(df)
    tablo, il_skill, yaz = skorla(T)
    sonuc = {"tasarim": {"iller": ILLER, "egitim": f"1991–{EGITIM_SON}", "test": f"{TEST_BAS}–2025/09",
                         "hedef_aylar": "Nisan–Ekim", "hedef": "net ihtiyaç, Kc=1, mm/ay"},
             "ufuk": tablo, "model_bilgi": {int(k): v for k, v in bilgi.items()},
             "il_bazinda_skill_h1_vs_kayan": il_skill, "yaz_butcesi_mayis_sonu": yaz}
    metin = json.dumps(sonuc, ensure_ascii=False, indent=2)
    (CIKTI / "ai1_deneme_sonuc.json").write_text(metin, encoding="utf-8")
    print(metin)


if __name__ == "__main__":
    main()
