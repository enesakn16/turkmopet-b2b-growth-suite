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
- önceki çözüm notunu ve yeniden açma gerekçesini `sales_task_events` tablosuna kaydeder,
- sorumlu atamasını ve görev kimliğini korur,
- geçmiş çözüm bilgisini sessizce kaybetmez.

Açık veya devam eden bir görevi yeniden açma girişimi kontrollü hata üretir. Yeniden açma gerekçesi boş bırakılamaz.

Denetim kayıtları Python API üzerinden okunabilir:

```python
from turkmopet_b2b.tasks import list_task_events

events = list_task_events("data/b2b-sales-tasks.db", "B2B-001:win_back")
for event in events:
    print(event.event_type, event.note, event.created_at)
```

Bu akış otomatik olarak görev açmaz veya müşteri durumunu değiştirmez. Satış ekibinin bilinçli kararı gerekir.