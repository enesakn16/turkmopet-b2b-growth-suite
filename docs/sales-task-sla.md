# B2B satış görevi SLA raporu

Görevler önceliğe göre aşağıdaki sürelerde tamamlanmalıdır:

- P1: 24 saat
- P2: 72 saat
- P3: 168 saat

Geciken açık görevleri Excel uyumlu CSV olarak dışa aktar:

```bash
b2b-sla \
  --database data/b2b-sales-tasks.db \
  --output reports/overdue-sales-tasks.csv
```

Belirli bir çalışanın geciken görevlerini filtrelemek için:

```bash
b2b-sla \
  --database data/b2b-sales-tasks.db \
  --assignee enes \
  --output reports/enes-overdue.csv
```

Komut geciken görev yoksa `0`, geciken görev varsa uyarı amacıyla `1`, veri veya dosya hatasında `2` koduyla çıkar. Çözülmüş görevler SLA raporuna alınmaz. Son tarih, görevin ilk oluşturulma zamanı üzerinden hesaplanır; raporların tekrar senkronize edilmesi süreyi sıfırlamaz.
