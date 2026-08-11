# Satış görevi başlatma güvenliği

`b2b-task start` yalnızca `OPEN` durumundaki bir görevi `IN_PROGRESS` durumuna geçirir.

Geçiş veritabanında tek koşullu `UPDATE` ile uygulanır:

```text
OPEN -> IN_PROGRESS
```

Aynı görev ikinci kez başlatılırsa işlem kontrollü hata üretir ve mevcut `updated_at` değeri değiştirilmez. Böylece tekrarlı otomasyon çağrıları veya aynı görevi eşzamanlı işleyen worker'lar bir görevi yeniden başlatılmış gibi gösteremez.

`RESOLVED` görevler doğrudan başlatılamaz. Tekrar çalışılması gerekiyorsa önce zorunlu gerekçeyle `reopen` akışı kullanılmalıdır; bu sayede önceki çözüm denetim geçmişinde korunur.
