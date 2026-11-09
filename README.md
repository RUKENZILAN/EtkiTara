# PharmaIntelligence AI - MVP v0.4

> **Önemli uyarı:** Bu yazılım yalnızca eğitim ve bilimsel bilgilendirme amaçlı bir
> prototiptir. **Tıbbi cihaz değildir; tıbbi tavsiye, tanı veya tedavi sunmaz.**
> İlaç, besin ve takviye kararları için mutlaka doktorunuza veya eczacınıza danışın.
> PubMed'de kayıt bulunmaması etkileşim olmadığı anlamına gelmez. Yapay zekâ özetleri
> hatalı veya eksik olabilir. Yazılım "olduğu gibi" sunulur, garanti verilmez
> (bkz. [LICENSE](LICENSE)). Hasta kimliği veya kişisel sağlık verisi girmeyin.

## v0.4 ile gelenler

- **Ad normalizasyonu:** Türkçe/ticari adlar PubMed'den önce İngilizce etkin madde adına eşleştirilir
  (yerleşik sözlük → ilaçlar için RxNorm → sözlükte yoksa isteğe bağlı model önerisi). Eşleşme tablosu
  ekranda ve raporda gösterilir; kısmi eşleşme, model önerisi ve çevrilmemiş adlar uyarıyla işaretlenir.
- **Kaynak yoksa model çağrılmaz:** PubMed kaydı olmayan ikililer için yapay zekâ çağrısı yapılmaz,
  sabit bir "kayıt bulunamadı, etkileşim yok anlamına gelmez" metni verilir. Başarısız sorgular ayrıca işaretlenir.
- **Hız sınırı, yeniden deneme, önbellek:** NCBI isteklerinde istek aralığı, 429/5xx için yeniden deneme ve
  24 saatlik süreç içi önbellek vardır.
- **Prompt enjeksiyonuna karşı:** Kaynak metinleri `<kaynaklar>` içinde veri olarak sunulur; model bunları talimat olarak yorumlamamalıdır.
- Mantık `core.py` içine ayrıldı; `tests/` altında ağ gerektirmeyen birim testleri var.

## Neler eklendi? (v0.2)

- İlaç, besin ve takviyeleri tek analizde kabul eder.
- Girilen maddelerin tüm ikili kombinasyonlarını oluşturur.
- Her ikili için ayrı PubMed literatür sorgusu yapar.
- PMID, yayın başlığı, yıl, özet ve PubMed bağlantısını gösterir.
- OpenAI (GPT) veya Qwen API anahtarı tanımlıysa her ikiliyi ayrı ayrı, kaynaklarla sınırlı biçimde özetler.
- CYP450 substrat/inhibitör/indükleyici rollerini yalnızca kaynak desteklediğinde raporlamasını ister.
- Kaynak bulunmamasının etkileşim yokluğu anlamına gelmediğini açıkça belirtir.
- Tüm değerlendirmeyi Markdown raporu olarak indirir.
- Eğitim amaçlı uyarıyı ekranda ve raporda tekrarlar.

## Kurulum

Python 3.10+ önerilir.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Yapay zekâ sağlayıcısı (OpenAI veya Qwen)

AI sentezi isteğe bağlıdır. Sağlayıcıyı kenar çubuğundan seçebilir veya `LLM_PROVIDER`
ortam değişkeniyle belirleyebilirsiniz (`openai`, `qwen`, `ollama`, `custom`).
Belirtilmezse tanımlı olan anahtara göre otomatik seçilir.

**OpenAI (GPT)**
```bash
export OPENAI_API_KEY="API_ANAHTARINIZ"
export OPENAI_MODEL="gpt-4.1-mini"        # isteğe bağlı
```

**Qwen (Alibaba Cloud DashScope)**
```bash
export LLM_PROVIDER="qwen"
export DASHSCOPE_API_KEY="API_ANAHTARINIZ"
export QWEN_MODEL="qwen-plus"             # isteğe bağlı (qwen-max, qwen-turbo, qwen3-... )
# Çin bölgesi hesabı için:
# export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
```
Varsayılan uç nokta uluslararası bölgedir (`dashscope-intl`). API anahtarı bölgeyle eşleşmelidir.

**Qwen yerel (Ollama, anahtarsız)**
```bash
ollama pull qwen3:8b
export LLM_PROVIDER="ollama"
export OLLAMA_MODEL="qwen3:8b"            # isteğe bağlı
```
Veri makinenizden çıkmaz. Küçük modellerde kaynak dışı bilgi üretme riski daha yüksektir;
çıktıları PubMed kayıtlarıyla karşılaştırın.

**Özel OpenAI uyumlu uç nokta (vLLM, LM Studio vb.)**
```bash
export LLM_PROVIDER="custom"
export LLM_BASE_URL="http://localhost:8000/v1"
export LLM_MODEL="Qwen/Qwen3-8B"
export LLM_API_KEY="anahtar-veya-bos-olmayan-bir-deger"
```

Windows PowerShell'de `export` yerine `$env:DASHSCOPE_API_KEY="..."` biçimini kullanın.

**PubMed hız sınırı (önerilir)**
```bash
export NCBI_API_KEY="..."      # ücretsiz, ncbi.nlm.nih.gov/account üzerinden; 3 yerine 10 istek/sn
export NCBI_EMAIL="siz@ornek.com"
```
Anahtarsız da çalışır, ancak çok maddeli analizlerde daha yavaştır.

Başlatma:
```bash
streamlit run app.py
```

Yapay zekâ anahtarı olmadan PubMed taraması çalışır. Anahtar tanımlandığında kaynak özetleme de etkinleşir.

## Testler

```bash
python -m unittest discover -s tests -v
```

## Normalizasyon hakkında

Yerleşik sözlük küçüktür ve örnek amaçlıdır; `core.py` içindeki `_RAW_SYNONYMS` listesini genişletin ve düzenli güncelleyin (bkz. "Sözlük bakımı ve güncelleme").
Sözlükte bulunmayan bir ad için sonuç çıkmıyorsa adı İngilizce etkin madde adıyla yazın.
Model önerileri doğrulanmamıştır ve yalnızca arama terimi üretmek için kullanılır; sonuç değerlendirmesine girmez.
RxNorm eşleşme eşiği (`RXNORM_MIN_SCORE`) gerçek verilerle ayarlanmalıdır.

## Sözlük bakımı ve güncelleme

Yerleşik sözlük (`core.py` içindeki `_RAW_SYNONYMS`, yaklaşık 130 giriş) elle derlenmiş bir **başlangıç setidir;
kapsamlı değildir ve durağan kalamaz.** Yeni ilaçlar, markalar ve takviye ürünleri sürekli çıkar; sözlük
güncellenmezse uygulama sessizce zayıf sonuç verir:

- Sözlükte olmayan bir ad için arama çoğunlukla boş döner. Bu, etkileşim olmadığı anlamına gelmez.
- Hatalı bir giriş, yanlış maddenin literatürünü getirir ve bunu fark etmek zordur.

**Yeni giriş eklerken**

1. Anahtar Türkçe yazımdır (büyük/küçük harf ve Türkçe karakter farkı otomatik yok sayılır); değer, İngilizce
   etkin madde adının (INN) başta olduğu listedir. Bitkilerde Latince tür adını da ekleyin.
2. İngilizce adı bir referansla doğrulayın (örn. RxNorm, WHO INN listesi, MeSH). Tahminle eklemeyin.
3. Bir adın birden fazla maddeyi anlatabildiği durumlara dikkat edin ("süt otu" ile "süt" gibi). Belirsiz ya da
   kısa (5 harften kısa) anahtarlar kısmi eşleşmede zaten kullanılmaz, ama tam eşleşmede yanlış sonuç verebilir.
4. Eklenen girişler için `tests/test_core.py` içine bir test ekleyin.
5. Mümkünse bir eczacı veya klinik farmakolog yeni girişleri gözden geçirsin.

**Önerilen bakım düzeni:** sözlüğü kod dışına (JSON/CSV) taşıyın, her girişe kaynak ve ekleme tarihi ekleyin ve
düzenli aralıklarla (örn. her ay veya yeni sürümden önce) gözden geçirin. Bu iş yol haritasında C1 maddesidir.

## Önemli sınırlar

Bu uygulama yalnızca eğitim ve bilimsel bilgilendirme amaçlı bir MVP prototipidir.
Doğrulanmış bir etkileşim veri tabanı, klinik karar destek sistemi veya tıbbi cihaz
olarak tasarlanmamıştır. PubMed araması eksiksiz değildir; arama sonucu bulunmaması
etkileşim bulunmadığını göstermez. Yapay zekâ özeti, kaynakların doğruluğunu veya
klinik uygulanabilirliğini garanti etmez.

Hasta kimliği veya kişisel sağlık verisi girmeyin. Gerçek klinik kullanım öncesinde
farmakolog/eczacı doğrulaması, yapılandırılmış ve lisansı uygun ilaç/takviye veri
kaynakları, kapsamlı testler, güvenlik kontrolleri ve mevzuat değerlendirmesi gerekir.

## Yol haritası: yapılanlar, yapılmayanlar ve yapılabilecekler

Bu bölüm projenin bugünkü durumunu ve sonraki adımların öncelik sırasını gösterir.
Efor tahminleri kabadır: **S** ≈ bir gün, **M** ≈ birkaç gün, **L** ≈ hafta veya daha fazla.
Etki, "sonucun güvenilirliğine ve kullanılabilirliğine katkı" anlamındadır.

### Bugünkü durum (v0.4)

| Konu | Durum | Not |
|---|---|---|
| PubMed ikili taraması | Yapıldı | Yalnızca başlık ve özet taranır; tam metin yok |
| OpenAI ve Qwen desteği | Yapıldı | Qwen/DashScope ve Ollama yolları gerçek anahtarla **denenmedi**, sahte istemciyle test edildi |
| Ad normalizasyonu | Kısmen | Küçük örnek sözlük; RxNorm eşiği (`RXNORM_MIN_SCORE = 70`) tahmindir, gerçek veriyle ayarlanmadı |
| Kaynak yoksa model çağrılmaz | Yapıldı | |
| Hız sınırı, yeniden deneme, önbellek | Kısmen | Önbellek süreç içidir; uygulama yeniden başlayınca silinir |
| Prompt enjeksiyonu önlemi | Kısmen | Etiket sınırlaması var; modelin uymasını garanti etmez, çıktı doğrulanmıyor |
| Testler | Kısmen | 21 birim testi (ağ yok); canlı API ve uçtan uca değerlendirme testi yok |
| Yapılandırılmış etkileşim/CYP verisi | **Yapılmadı** | CYP rolleri hâlâ yalnızca literatür özetinden gelir |
| Klinik önem sınıflandırması | **Bilerek yapılmadı** | Küratörlü kaynak olmadan derece vermek yanıltıcı olur |
| Kullanıcının eşleşmeleri düzeltmesi | **Yapılmadı** | Eşleşme tablosu yalnızca gösterilir, düzenlenemez |
| Üçlü ve daha büyük kombinasyonlar | **Yapılmadı** | Yalnızca ikili tarama |
| Kimlik doğrulama, kalıcı depolama, kayıt tutma | **Yapılmadı** | |

### Önerilen sıra

1. Küratörlü kaynak ekleme (A1, A2): en büyük güvenilirlik sıçraması.
2. Çıktı doğrulama (B1): modelin kaynak dışına çıkmasını kodla engellemek.
3. Normalizasyonu onaylanabilir hale getirme (C2) ve sözlüğü genişletme (C1).
4. Değerlendirme seti (E1): her değişikliğin ve her modelin ölçülebilmesi için.
5. Gizlilik/mevzuat kararları (F), gerçek kullanıcıya açılmadan önce.

### A. Kanıt altyapısı (en yüksek etki)

| # | Yapılabilecek | Neden | Efor |
|---|---|---|---|
| A1 | **DailyMed / openFDA ilaç etiketlerinin "Drug Interactions" bölümünü** çekip kaynak olarak göstermek | Resmî, kamuya açık ve sürümlü; PubMed'de kayıt çıkmayan birçok etkileşimi yakalar | M |
| A2 | **FDA'nın CYP substrat/inhibitör/indükleyici tablosunu** sürümlü bir veri dosyasına (JSON/CSV) çevirip enzim-rol modeli kurmak | CYP bilgisini LLM'e çıkarttırmak yerine tablodan okumak; her kayıt için kaynak ve tarih tutulur | M |
| A3 | Diğer kamu kaynakları: PharmGKB/CPIC (farmakogenetik), LiverTox (karaciğer), NIH ODS ve NCCIH (takviye/bitki) | Takviye tarafı en zayıf noktadır; kullanım koşullarını her kaynak için ayrıca kontrol edin | M |
| A4 | Ticari/lisanslı kaynaklar (DrugBank, Natural Medicines vb.) veya DDInter gibi açık veri kümeleri | En geniş kapsam; **lisans ve kullanım şartları** önce netleşmeli | L |
| A5 | Kaynak hiyerarşisi: etiket > klinik çalışma > vaka raporu > in vitro, ekranda kanıt düzeyiyle birlikte | Kullanıcı "kaç kayıt var"dan çok "ne kadar sağlam" sorusunu görür | M |

### B. Arama ve çıktı kalitesi

| # | Yapılabilecek | Neden | Efor |
|---|---|---|---|
| B1 | **Çıktıyı JSON olarak istemek** (bulgu, tip, enzim, her iddia için PMID) ve kodla doğrulamak: atıf yapılan PMID verilen kayıtlar arasında mı, enzim adı kaynak metinde geçiyor mu | Uydurma riskini kodla azaltır; uyuşmayan iddia gösterilmez | M |
| B2 | MeSH tabanlı sorgular (`Herb-Drug Interactions`, `Drug Interactions`), yayın türü filtresi ve sıralaması | Daha az gürültü; vaka raporu ile klinik çalışma ayrışır | S |
| B3 | Europe PMC'yi ek kaynak yapmak (açık erişim tam metin) | Özetin yetmediği durumlarda daha fazla bağlam | M |
| B4 | Geri çekilmiş yayın kontrolü (PubMed "Retracted Publication" türü) | Geri çekilmiş çalışmaya dayalı özet üretmemek | S |
| B5 | **Üçlü ve sınıf bazlı farmakodinamik tarama**: serotonin sendromu, QT uzaması, kanama, CNS depresyonu, hiperkalemi | Birçok risk ikili değil kombinasyon sorunudur | L |
| B6 | Aynı soruyu iki modele sorup farklılık varsa işaretlemek | Basit bir tutarlılık kontrolü | M |

### C. Madde adı normalizasyonu

| # | Yapılabilecek | Neden | Efor |
|---|---|---|---|
| C1 | Sözlüğü genişletmek ve **düzenli güncellemek**: TİTCK ilaç listesi, ATC kodları, marka → etkin madde, tuz/form eşleştirme; sözlüğü kod dışına (JSON/CSV) taşıyıp her girişe kaynak ve tarih eklemek | Sözlükte olmayan ad bugün sessizce zayıf sonuç verir; yeni ürünler çıktıkça sözlük eskir | M |
| C2 | **İki adımlı akış**: önce eşleşme tablosu düzenlenebilir gösterilir, kullanıcı onaylar, sonra arama yapılır | Yanlış eşleşmeyi aramadan önce yakalar | M |
| C3 | Yazım hatası düzeltme ve bulanık eşleşme (yalnızca sözlük içinde) | "greyfurt/greyfurut" gibi hatalar | S |
| C4 | Bitkilerde Latince tür adı ve ekstrakt/standardizasyon alanları | "Sarı kantaron" ile standardize ekstrakt aynı risk profilinde değildir | M |
| C5 | RxNorm eşiğini ve eşleşme mantığını gerçek ilaç listesiyle kalibre etmek | Şu anki eşik tahmindir | S |

### D. Kullanıcı deneyimi

| # | Yapılabilecek | Neden | Efor |
|---|---|---|---|
| D1 | Özet matris: hangi çiftlerde kanıt var, kaç kayıt, hangi türden | 28 çiftte tek tek gezmek zor | S |
| D2 | PDF/DOCX rapor, İngilizce arayüz | Eczacı ve hekimle paylaşım kolaylaşır | M |
| D3 | Dozlar, kullanım süresi ve form için yapılandırılmış alanlar (serbest metin yerine) | Prompt'a daha temiz bağlam gider | M |
| D4 | 8 maddelik sınırı arka plan kuyruğuyla kaldırmak | Büyük listeler uzun sürer | L |

### E. Mühendislik ve test

| # | Yapılabilecek | Neden | Efor |
|---|---|---|---|
| E1 | **Altın değerlendirme seti**: bilinen etkileşimler (örn. sarı kantaron + siklosporin, greyfurt + simvastatin) ve bilinen "etkileşim yok" çiftleri; GPT ile Qwen'in kaynağa sadakatini ölçmek | Model veya prompt değişikliğinin etkisini ölçmenin tek yolu | M |
| E2 | Canlı entegrasyon testleri (CI'da isteğe bağlı): PubMed, RxNorm, DashScope | Şu anki testler ağ çağrılarını taklit eder | S |
| E3 | Kalıcı önbellek (SQLite/Redis) ve paralel sorgu | Yeniden başlatmada hız ve çok kullanıcılı kullanım | M |
| E4 | Bağımlılıkları sabitleme, Docker, CI (GitHub Actions), lint ve tip denetimi | Tekrarlanabilir kurulum | S |
| E5 | Kaynak sürümü ve erişim tarihi kaydı; raporda "bu veriler şu tarihte çekildi" | İzlenebilirlik | S |
| E6 | Günlük kaydı ve hata izleme (kişisel veri içermeden) | Sorun ayıklama | S |
| E7 | Olgunlaşırsa Streamlit'ten API (FastAPI) + ayrı ön yüze geçiş | Streamlit prototip için uygundur, ürün için sınırlıdır | L |

### F. Gizlilik, güvenlik ve mevzuat (gerçek kullanıcıdan önce)

| # | Yapılacak / değerlendirilecek | Neden | Efor |
|---|---|---|---|
| F1 | **Veri akışı ve KVKK**: OpenAI ve Qwen (DashScope) kullanıldığında girdi üçüncü taraf sunuculara gider. Aydınlatma metni, yerel model (Ollama) seçeneğinin öne çıkarılması, hukuki görüş | Kişisel veri girilmese bile sorulması gereken bir sorudur | M |
| F2 | Girdide kişisel veri (ad, TC kimlik, tarih) tespiti ve uyarısı | Kullanıcı hataen yazabilir | S |
| F3 | **Tıbbi cihaz yazılımı değerlendirmesi** (TİTCK / AB MDR): amaçlanan kullanım beyanı | "Karar destek" iddiası taşımaya başlayan ürün düzenlemeye girebilir; eğitim amaçlı çerçeve ve şiddet derecesi vermemek bu riski azaltır | M |
| F4 | **Eczacı/klinik farmakolog incelemesi**: çıktı şablonu, uyarı metinleri, örnek vakalar | Gerçek kullanıcıya açmadan önce zorunlu sayın | M |
| F5 | API anahtarı yönetimi (gizli yönetici), kötüye kullanım ve hız sınırı koruması, kimlik doğrulama | Herkese açık dağıtımda gerekir | M |

### Bilinen sınırlamalar

- PubMed yalnızca başlık ve özet verir; ayrıntı çoğu zaman tam metindedir.
- "Kayıt yok" sonucu etkileşim olmadığını göstermez; arama terimleri veya indeksleme yetersiz kalabilir.
- Yapay zekâ özeti kaynağı yanlış yorumlayabilir; bugün çıktı kodla doğrulanmıyor (bkz. B1).
- Sözlük kısmi eşleşmeleri yanlış olabilir; bu yüzden işaretlenir ama engellenmez.
- RxNorm yalnızca ilaçlar için kullanılır; besin ve takviyeler sözlük veya model önerisine kalır.
- Madde adı sözlüğü küçüktür, elle derlenmiştir ve güncel tutulması gerekir; eksik veya eski girişler boş ya da yanlış sonuç doğurabilir (bkz. "Sözlük bakımı ve güncelleme").
- Analiz başına en fazla 8 madde ve her çift için en fazla 8 kayıt.

## Lisans

MIT Lisansı; ayrıntılar için [LICENSE](LICENSE) dosyasına bakın.

## Üçüncü taraf hizmetler ve veriler

Bu depo yalnızca kaynak kodu içerir; herhangi bir PubMed kaydı, RxNorm verisi veya model çıktısı barındırmaz.
Uygulamayı çalıştırdığınızda aşağıdaki hizmetlere **kendi anahtarınız ve kendi sorumluluğunuzla** bağlanırsınız;
her birinin kullanım şartları geçerlidir:

- **NCBI E-utilities (PubMed):** kullanım politikası ve hız sınırları için NCBI'nin yayımladığı şartlara bakın.
- **NLM RxNav / RxNorm:** NLM'nin kullanım şartlarına bakın.
- **OpenAI, Alibaba Cloud (DashScope/Qwen) veya yerel modeller:** ilgili sağlayıcının şartları ve gizlilik politikası.
  Bulut sağlayıcılarına gönderilen metin makinenizden çıkar; gizlilik gerektiren bir ortamda yerel model (Ollama) kullanın.

Uygulamayı başkalarının kullanımına açık bir hizmet olarak yayımlamadan önce KVKK, tıbbi cihaz mevzuatı ve
sorumluluk konularında hukuki görüş alın (bkz. yol haritası, bölüm F).
