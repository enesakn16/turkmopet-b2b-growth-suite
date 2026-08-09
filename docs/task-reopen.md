# Çözümlenmiş satış görevini yeniden açma

Aynı müşteri riski yeni bir dönemde tekrar ortaya çıktığında çözümlenmiş görev doğrudan `start` komutuyla başlatılmaz. Önce zorunlu bir gerekçeyle yeniden açılır:

```bash
b2b-task \
  --database data/b2b-sales-tasks.db \
  reopen B2B-001:win_back \
  --reason "Ağustos skor raporunda ödeme riski tekrarlandı"
```

Bu işlem:

- yalnızca `RESOLVED` durumundaki görevlerde çalışır,
- görevi `OPEN` durumuna getirir,
- yeni çalışma döngüsü için aktif `resolution_note` alanını temizler,
- önceki çözüm notunu `previous_resolution` alanında saklar,
- yeniden açma gerekçesini `reopen_reason` alanında ayrı olarak saklar,
- insan tarafından okunabilir birleşik `note` alanını geriye dönük uyumluluk için korur,
- sorumlu atamasını ve görev kimliğini korur,
- geçmiş çözüm bilgisini sessizce kaybetmez.

Açık veya devam eden bir görevi yeniden açma girişimi kontrollü hata üretir. Yeniden açma gerekçesi boş bırakılamaz.

Bir görev zaten `RESOLVED` durumundaysa `resolve` komutu ikinci kez çalıştırılamaz. Bu koruma mevcut `resolution_note` değerinin sessizce ezilmesini engeller. Çözüm gerçekten değişecekse önce `reopen --reason ...` ile yeni çalışma döngüsü açılmalı, ardından görev tekrar çözümlenmelidir; böylece eski çözüm denetim geçmişinde korunur.

Mevcut SQLite veritabanlarında eski `sales_task_events` tablosu varsa yeni yapısal alanlar uygulama açılışında güvenli biçimde eklenir. Var olan denetim satırları silinmez veya yeniden yazılmaz; eski kayıtların yeni alanları boş kalır.

## Denetim geçmişini görüntüleme ve dışa aktarma

Bir görevin yeniden açılma geçmişi doğrudan CLI üzerinden okunabilir:

```bash
b2b-task \
  --database data/b2b-sales-tasks.db \
  audit B2B-001:win_back
```

Excel uyumlu UTF-8 BOM CSV çıktısı için:

```bash
b2b-task \
  --database data/b2b-sales-tasks.db \
  audit B2B-001:win_back \
  --output reports/B2B-001-win-back-audit.csv
```

CSV şu alanları ayrı sütunlarda taşır: `event_id`, `task_key`, `event_type`, `note`, `previous_resolution`, `reopen_reason`, `created_at`. Böylece operasyon veya raporlama tarafında birleşik `note` metnini ayrıştırmaya gerek kalmaz.

Denetim kayıtları Python API üzerinden de okunabilir:

```python
from turkmopet_b2b.tasks import list_task_events

events = list_task_events("data/b2b-sales-tasks.db", "B2B-001:win_back")
for event in events:
    print(
        event.event_type,
        event.previous_resolution,
        event.reopen_reason,
        event.created_at,
    )
```

Bu akış otomatik olarak görev açmaz veya müşteri durumunu değiştirmez. Satış ekibinin bilinçli kararı gerekir.
