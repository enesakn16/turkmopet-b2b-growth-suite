# Türkmopet B2B Growth Suite

Türkmopet'in toptan satış müşterilerini daha düzenli değerlendirmek, segmentlere ayırmak ve büyüme fırsatlarını ölçmek için geliştirilen açık kaynak araç seti.

İlk sürüm; aylık sipariş hacmi, aktif müşteri süresi, ödeme gecikmesi, iade oranı ve vergi levhası doğrulamasına göre deterministik ve test edilebilir bir B2B müşteri puanı üretir.

## Özellikler

- 0–100 arası açıklanabilir müşteri puanı
- `starter`, `growth` ve `pro` segmentleri
- Ödeme ve iade riski için negatif puanlar
- Her puanın nedenlerini döndüren `ScoreBreakdown`
- Toplu müşteri sıralama desteği
- Python 3.11, 3.12 ve 3.13 için otomatik CI

## Kurulum

```bash
python -m pip install -e .
```

## Kullanım

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
```

## Mimari

```text
WholesaleAccount
      ↓
validation
      ↓
score_account
      ↓
ScoreBreakdown(total, tier, reasons)
```

Puanlama çekirdeği dış servislere bağlı değildir. Böylece aynı kurallar CLI, FastAPI veya yönetim paneli içinde tekrar kullanılabilir.

## Yol haritası

- Segment bazlı aksiyon önerileri
- CSV içe aktarma ve raporlama
- FastAPI servis katmanı
- Basit yönetim paneli
- Gerçek sipariş verileriyle kalibrasyon

## AI destekli geliştirme

Kod tabanı yapay zekâ destekli geliştirilebilir; ancak puanlama kararları deterministik, açıklanabilir ve testlerle doğrulanabilir kalmalıdır. Bu model otomatik kredi kararı vermek için değil, satış ekibine önceliklendirme sinyali üretmek için tasarlanmıştır.
