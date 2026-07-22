# Türkmopet B2B Growth Suite

Türkmopet'in toptan satış müşterilerini düzenli değerlendirmek, segmentlere ayırmak ve satış ekibine uygulanabilir aksiyonlar üretmek için geliştirilen açık kaynak araç seti.

## Özellikler

- 0–100 arası açıklanabilir müşteri puanı
- `starter`, `growth` ve `pro` segmentleri
- Ödeme gecikmesi ve yüksek iade oranı için risk sinyalleri
- Vergi levhası doğrulama kontrolü
- CSV müşteri listesi içe aktarma
- Excel uyumlu UTF-8 BOM raporu üretme
- Her müşteri için deterministik satış aksiyonu önerisi
- Python 3.11, 3.12 ve 3.13 için otomatik CI

## Kurulum

```bash
python -m pip install -e .
```

## Komut satırı kullanımı

Girdi CSV'si şu kolonları içermelidir:

```csv
account_id,monthly_order_value,active_months,payment_delay_days,return_rate,has_tax_certificate
B2B-001,35000,6,20,0.20,true
B2B-002,120000,18,0,0.01,evet
```

Rapor üretmek için:

```bash
b2b-score --input accounts.csv --output reports/scored-accounts.csv
```

Çıktı kolonları:

```text
account_id,score,tier,recommended_action,reasons
```

Örnek aksiyonlar:

- `review-payment-risk`
- `review-return-pattern`
- `offer-key-account-plan`
- `schedule-growth-call`
- `request-tax-certificate`
- `nurture-account`

## Python API kullanımı

```python
from turkmopet_b2b import WholesaleAccount, score_account

result = score_account(
    WholesaleAccount(
        monthly_order_value=50_000,
        active_months=12,
        payment_delay_days=0,
        return_rate=0.01,
        has_tax_certificate=True,
    )
)

print(result.total)
print(result.tier)
print(result.reasons)
```

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

## Mimari

```text
CSV
 ↓
load_accounts
 ↓
WholesaleAccount validation
 ↓
score_account
 ↓
AccountReport + recommended action
 ↓
Excel uyumlu CSV
```

Puanlama ve aksiyon üretimi dış servislere bağlı değildir. Aynı çekirdek ileride CLI, FastAPI veya yönetim paneli içinde tekrar kullanılabilir.

## Tasarım kararları

- Puanlama kuralları deterministiktir; aynı veri aynı sonucu üretir.
- Her hesap `account_id` ile tekil olmak zorundadır.
- Hatalı satırlar sessizce atlanmaz; satır numarasıyla açık hata üretilir.
- `payment-risk`, diğer büyüme aksiyonlarından önce gelir.
- Çıktı dosyası Türkçe Excel kurulumlarında sorunsuz açılması için UTF-8 BOM ile yazılır.

## Yol haritası

- FastAPI servis katmanı
- Basit yönetim paneli
- Gerçek sipariş verileriyle eşik kalibrasyonu
- Müşteri geçmişine göre zaman serisi analizi
- CRM entegrasyonu

## AI destekli geliştirme

Kod tabanı yapay zekâ destekli geliştirilebilir; ancak puanlama ve aksiyon kararları deterministik, açıklanabilir ve testlerle doğrulanabilir kalmalıdır. Bu araç otomatik kredi kararı vermek için değil, satış ekibine önceliklendirme sinyali üretmek için tasarlanmıştır.
