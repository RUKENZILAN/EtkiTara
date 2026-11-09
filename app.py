import re
import streamlit as st

from core import (
    NO_SOURCE_TEXT, QUERY_FAILED_TEXT, PROVIDERS, default_provider, get_llm_config,
    llm_ready, llm_complete, normalize_items, unverified, pubmed_search_pair,
    unique_pairs, make_evidence_prompt, fold,
)

st.set_page_config(page_title="PharmaIntelligence AI", layout="wide")

DISCLAIMER = (
    "Bu uygulama yalnızca eğitim ve bilimsel bilgilendirme amaçlı geliştirilmiş bir MVP "
    "prototipidir. Sunulan analizler tıbbi tanı, tedavi veya ilaç kullanım önerisi niteliği "
    "taşımaz. İlaç, besin ve takviye etkileşimleriyle ilgili kararlar için mutlaka "
    "doktorunuza veya eczacınıza danışınız. Doktor veya eczacı görüşü olmadan ilaçlarınızı "
    "ya da takviyelerinizi başlatmayınız, bırakmayınız veya dozlarını değiştirmeyiniz."
)

st.title("PharmaIntelligence AI")
st.subheader("İlaç, besin ve takviye etkileşim analizörü")
st.warning(DISCLAIMER)
st.caption(
    "MVP v0.4 | Eğitim amaçlı prototip. Literatür taraması, doğrulanmış ve kapsamlı "
    "bir etkileşim veri tabanının yerine geçmez."
)


def parse_items(value):
    return [x.strip() for x in re.split(r"[\n,;]+", value or "") if x.strip()]


# --- Kenar çubuğu: yapay zekâ sağlayıcısı -----------------------------------
with st.sidebar:
    st.header("Yapay zekâ sağlayıcısı")
    _keys = list(PROVIDERS.keys())
    provider_choice = st.selectbox(
        "Sağlayıcı", _keys, index=_keys.index(default_provider()),
        format_func=lambda k: PROVIDERS[k]["label"],
    )
    _cfg = get_llm_config(provider_choice)
    model_override = st.text_input("Model", value=_cfg["model"])
    key_override = ""
    if provider_choice != "ollama":
        key_override = st.text_input("API anahtarı (boşsa ortam değişkeni kullanılır)", type="password")
    LLM_CONFIG = dict(_cfg)
    LLM_CONFIG["model"] = model_override.strip() or _cfg["model"]
    if key_override.strip():
        LLM_CONFIG["api_key"] = key_override.strip()
    if LLM_CONFIG["provider"] == "custom" and not LLM_CONFIG["base_url"]:
        LLM_CONFIG["base_url"] = st.text_input("Base URL", placeholder="http://localhost:8000/v1").strip() or None
    st.caption("Anahtar yalnızca bu oturumda bellekte tutulur; dosyaya yazılmaz.")
    use_rxnorm = st.checkbox("İlaç adlarını RxNorm ile doğrula", value=True)

LLM_READY = llm_ready(LLM_CONFIG)

# --- Form --------------------------------------------------------------------
with st.form("interaction_form"):
    col1, col2 = st.columns(2)
    with col1:
        medicines = st.text_area("İlaçlar", placeholder="Her satıra bir ilaç veya etkin madde", height=110)
        supplements = st.text_area(
            "Vitaminler, mineraller ve takviyeler",
            placeholder="Örn. sarı kantaron, magnezyum, D vitamini, ginkgo biloba", height=110,
        )
    with col2:
        foods = st.text_area("Besinler ve içecekler", placeholder="Örn. greyfurt, süt, kahve", height=110)
        details = st.text_area(
            "İsteğe bağlı ürün ayrıntıları",
            placeholder="Etkin madde formu, doz, bitki türü, ekstrakt standardizasyonu. Kişisel/hasta verisi girmeyin.",
            height=110,
        )
    scope = st.selectbox(
        "Analiz kapsamı",
        [
            "Kapsamlı: farmakokinetik, farmakodinamik ve CYP450",
            "Farmakokinetik ve CYP450",
            "Farmakodinamik",
            "Literatür ve kanıt değerlendirmesi",
        ],
    )
    max_per_pair = st.select_slider("Her madde çifti için en fazla PubMed kaydı", options=[3, 5, 8], value=5)
    submitted = st.form_submit_button("Etkileşim literatürünü tara", type="primary")

if submitted:
    # 1) Girdileri topla, tekrarları ele
    entries, seen = [], set()
    for category, raw_list in (
        ("ilac", parse_items(medicines)),
        ("takviye", parse_items(supplements)),
        ("besin", parse_items(foods)),
    ):
        for raw in raw_list:
            k = fold(raw)
            if k not in seen:
                seen.add(k)
                entries.append((raw, category))

    if len(entries) < 2:
        st.error("En az iki farklı madde girin.")
        st.stop()
    if len(entries) > 8:
        st.error("MVP sınırı: Bir analizde en fazla 8 madde girilebilir. Daha az maddeyle başlayın.")
        st.stop()

    # 2) Ad normalizasyonu
    with st.spinner("Madde adları İngilizce etkin madde adlarına eşleştiriliyor..."):
        normalized = normalize_items(entries, LLM_CONFIG if LLM_READY else None, use_rxnorm=use_rxnorm)
    terms_by_input = {n["input"]: tuple(n["terms"]) for n in normalized}
    all_items = [n["input"] for n in normalized]

    st.subheader("Madde adı eşleştirme")
    st.table([
        {"Girilen": n["input"], "Aranan terimler": ", ".join(n["terms"]), "Eşleşme kaynağı": n["source"]}
        for n in normalized
    ])
    if any(unverified(n) for n in normalized):
        st.warning(
            "Bazı adlar sözlükte tam eşleşmedi (kısmi eşleşme, model önerisi veya çevrilmemiş). "
            "Bu adlarla PubMed'de kayıt bulunamaması çeviri sorunundan kaynaklanabilir; "
            "adı İngilizce etkin madde adıyla yazıp yeniden deneyin."
        )
    for n in normalized:
        if n["note"]:
            st.caption(f"{n['input']}: {n['note']}")

    # 3) PubMed taraması
    pairs = unique_pairs(all_items)
    st.info(f"{len(all_items)} madde için {len(pairs)} ikili kombinasyon taranacak.")
    pair_records, failed = {}, set()
    progress = st.progress(0)
    status = st.empty()
    for index, pair in enumerate(pairs, start=1):
        status.write(f"PubMed taraması: {pair[0]} + {pair[1]}")
        try:
            pair_records[pair] = pubmed_search_pair(
                terms_by_input[pair[0]], terms_by_input[pair[1]], max_per_pair
            )
        except Exception as exc:
            pair_records[pair] = []
            failed.add(pair)
            st.warning(f"{pair[0]} + {pair[1]} için PubMed sorgusu tamamlanamadı: {exc}")
        progress.progress(index / len(pairs))
    status.empty()
    progress.empty()

    total_records = sum(len(v) for v in pair_records.values())
    st.subheader("İkili literatür taraması")
    st.write(f"Toplam {total_records} PubMed kaydı bulundu. Bu sayı etkileşimin varlığını veya yokluğunu kanıtlamaz.")
    for pair, records in pair_records.items():
        with st.expander(f"{pair[0]} + {pair[1]} | {len(records)} kayıt", expanded=False):
            if pair in failed:
                st.warning(QUERY_FAILED_TEXT)
            elif not records:
                st.info("Bu sorguda kayıt bulunamadı. Bu, etkileşim olmadığı anlamına gelmez.")
            for rec in records:
                st.markdown(f"**{rec['title']}** ({rec['year']})")
                st.caption(f"PMID: {rec['pmid']} | [PubMed kaydı]({rec['url']})")
                st.write(rec["abstract"])

    # 4) Değerlendirme: kaynak yoksa model ÇAĞRILMAZ
    has_sources = any(pair_records.values())
    if has_sources and not LLM_READY:
        st.info(
            "Literatür taraması tamamlandı. Kaynak sentezi için kenar çubuğundan bir sağlayıcı seçip "
            "API anahtarı girin veya OPENAI_API_KEY / DASHSCOPE_API_KEY ortam değişkenini tanımlayın."
        )
    st.subheader("Kaynaklarla sınırlı farmakolojik ön değerlendirme")
    if LLM_READY and has_sources:
        st.caption(f"Model: {LLM_CONFIG['model']} ({PROVIDERS[LLM_CONFIG['provider']]['label']})")

    outputs = []
    for index, (pair, records) in enumerate(pair_records.items(), start=1):
        if pair in failed:
            text = QUERY_FAILED_TEXT
        elif not records:
            text = NO_SOURCE_TEXT
        elif LLM_READY:
            with st.spinner(f"Yapay zekâ kaynakları özetliyor: {pair[0]} + {pair[1]}"):
                try:
                    text = llm_complete(LLM_CONFIG, make_evidence_prompt(pair, records, scope, details))
                except Exception as exc:
                    text = f"Bu ikili için yapay zekâ özeti oluşturulamadı: {exc}"
        else:
            text = "Yapay zekâ özeti oluşturulmadı (sağlayıcı yapılandırılmadı). Kaynaklar listelenmiştir."
        outputs.append((pair, text))
        with st.expander(f"Değerlendirme {index}: {pair[0]} + {pair[1]}", expanded=bool(records)):
            st.markdown(text)

    # 5) Rapor
    report = [
        "# PharmaIntelligence AI - Etkileşim ön değerlendirmesi",
        f"> {DISCLAIMER}",
        "",
        "## Girilen maddeler ve aranan terimler",
        *[f"- {n['input']} → {', '.join(n['terms'])} ({n['source']})" for n in normalized],
        "",
        f"Analiz kapsamı: {scope}",
        "",
    ]
    for pair, text in outputs:
        report.extend([f"## {pair[0]} + {pair[1]}", text, ""])
        for rec in pair_records[pair]:
            report.append(f"- PMID {rec['pmid']}: {rec['title']} ({rec['url']})")
        report.append("")
    report.extend(["---", DISCLAIMER])

    st.download_button(
        "Tüm analiz raporunu indir",
        data="\n".join(report),
        file_name="pharmaintelligence_etkilesim_raporu.md",
        mime="text/markdown",
        type="primary",
    )

st.divider()
st.caption("PharmaIntelligence AI MVP v0.4")
st.caption(DISCLAIMER)
