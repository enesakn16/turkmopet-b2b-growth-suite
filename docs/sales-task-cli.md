# B2B satış görevi yönetimi

`b2b-trend --task-database` ile oluşturulan kalıcı görevler `b2b-task` komutuyla SQLite dosyasına elle girmeden yönetilir.

## Açık görevleri listeleme

```bash
b2b-task --database data/b2b-sales-tasks.db list --status OPEN
```

Sorumluya göre filtreleme:

```bash
b2b-task --database data/b2b-sales-tasks.db list --assignee enes
```

Excel uyumlu CSV çıktısı:

```bash
b2b-task --database data/b2b-sales-tasks.db list \
  --status OPEN \
  --output reports/open-sales-tasks.csv
```

Görevler açık durum, öncelik, müşteri ve aksiyon türüne göre deterministik sırada gösterilir.

## Görev atama

```bash
b2b-task --database data/b2b-sales-tasks.db assign B2B-001:win_back enes
```

Boş sorumlu kabul edilmez.

## Görevi başlatma

```bash
b2b-task --database data/b2b-sales-tasks.db start B2B-001:win_back
```

Bu işlem görevi `IN_PROGRESS` durumuna geçirir. Çözülmüş bir görev yanlışlıkla tekrar başlatılamaz.

## Görevi çözme

```bash
b2b-task --database data/b2b-sales-tasks.db resolve B2B-001:win_back \
  --note "Müşteriyle görüşüldü, yeni fiyat listesi gönderildi"
```

Çözüm notu zorunludur. Boş notla görev kapatılamaz.

## Güvenlik davranışı

- Var olmayan görev anahtarı kontrollü hata üretir.
- Var olmayan veritabanı otomatik boş dosyaya çevrilmez; yanlış dosya yolu açıkça bildirilir.
- Durum alanı yalnızca `OPEN`, `IN_PROGRESS` veya `RESOLVED` olabilir.
- Liste dışa aktarımı UTF-8 BOM içerir ve Excel ile doğrudan açılabilir.
- Trend raporu tekrar çalıştırıldığında manuel sorumlu, durum ve çözüm notu korunmaya devam eder.
