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

Mevcut SQLite veritabanlarında eski `sales_task_events` tablosu varsa yeni yapısal alanlar uygulama açılışında güvenli biçimde eklenir. Var olan denetim satırları silinmez veya yeniden yazılmaz; eski kayıtların yeni alanları boş kalır.

Denetim kayıtları Python API üzerinden okunabilir:

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

Bu sayede rapor veya operasyon ekranları metin ayrıştırmak zorunda kalmadan önceki çözümü ve yeniden açma gerekçesini ayrı alanlar olarak kullanabilir.

Bu akış otomatik olarak görev açmaz veya müşteri durumunu değiştirmez. Satış ekibinin bilinçli kararı gerekir.
