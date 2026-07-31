# B2B satış aksiyonu öncelikleri

`turkmopet_b2b.actions`, dönemsel skor değişimlerini satış ekibinin doğrudan çalışabileceği deterministik görevlere dönüştürür.

## Kurallar

| Hareket | Öncelik | Aksiyon |
|---|---:|---|
| Müşteri güncel raporda yok | 1 | Hesap/veri kontrolü ve pasif müşteri araması |
| Skor en az 15 puan düştü | 1 | Bir iş günü içinde geri kazanım araması |
| Segment düştü | 1 | Bir iş günü içinde geri kazanım araması |
| Daha küçük skor düşüşü | 2 | Neden analizi ve takip araması |
| Skor yükseldi | 3 | Yeni segmente uygun üst satış teklifi |
| Yeni müşteri | 3 | İlk sipariş ve B2B onboarding teması |
| Skor sabit | Görev yok | Gereksiz görev üretilmez |

## Python kullanımı

```python
from turkmopet_b2b.actions import build_sales_actions, write_sales_actions
from turkmopet_b2b.history import compare_score_snapshots, load_score_snapshot

trends = compare_score_snapshots(
    load_score_snapshot("reports/2026-06-scored.csv"),
    load_score_snapshot("reports/2026-07-scored.csv"),
)
actions = build_sales_actions(trends)
write_sales_actions("reports/2026-07-actions.csv", actions)
```

CSV kolonları:

```text
account_id,priority,action_type,recommended_action,reason
```

Dosya UTF-8 BOM ile ve atomik olarak yayımlanır. Başarısız yazma mevcut sağlam raporu bozmaz ve geçici dosya bırakmaz.
