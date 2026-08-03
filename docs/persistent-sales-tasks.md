# Kalıcı B2B satış görevleri

Dönem karşılaştırmasından üretilen satış aksiyonları isteğe bağlı olarak SQLite veritabanına senkronize edilebilir. Böylece CSV her yeniden üretildiğinde görev ataması, çalışma durumu ve çözüm notu kaybolmaz.

## Kullanım

```bash
b2b-trend \
  --previous reports/2026-06-scored.csv \
  --current reports/2026-07-scored.csv \
  --output reports/2026-07-trends.csv \
  --actions-output reports/2026-07-actions.csv \
  --task-database data/b2b-sales-tasks.db
```

`--actions-output` zorunlu değildir. Yalnızca `--task-database` verilirse aksiyonlar bellekte üretilip doğrudan görev tablosuna yazılır.

## Görev kimliği ve tekrar güvenliği

Görev anahtarı `account_id:action_type` biçimindedir. Aynı müşteri ve aksiyon türü sonraki çalışmada tekrar oluşursa yeni kayıt açılmaz. Güncel öncelik, öneri ve neden yenilenir; aşağıdaki manuel alanlar korunur:

- `status`: `OPEN`, `IN_PROGRESS`, `RESOLVED`
- `assignee`
- `resolution_note`
- `created_at`

Bu davranış aynı raporun tekrar çalıştırılmasını güvenli ve idempotent hale getirir.

## Veritabanı şeması

`sales_tasks` tablosu şu alanları içerir:

```text
task_key,account_id,priority,action_type,recommended_action,reason,
status,assignee,resolution_note,created_at,updated_at
```

Açık işler `status`, `priority` ve `account_id` üzerinden indekslenir. SQLite dosyası ve üst klasörleri yoksa otomatik oluşturulur.

## Tasarım kararı

Senkronizasyon mevcut görev durumunu otomatik olarak tekrar `OPEN` yapmaz. Satış çalışanının ataması, ilerleme durumu ve notları veri üretim sürecinden daha yüksek önceliklidir. Yeni skor verisi yalnızca görevin güncel önceliğini ve açıklamasını yeniler.
