# Türkmopet B2B Growth Suite

Türkmopet'in toptan satış müşterilerini daha düzenli değerlendirmek, segmentlere ayırmak ve büyüme fırsatlarını ölçmek için geliştirilen açık kaynak araç seti.

Bu depo şu anda başlangıç aşamasındadır. İlk hedef; aylık sipariş hacmi, aktif müşteri süresi, ödeme gecikmesi, iade oranı ve vergi levhası doğrulamasına göre deterministik ve test edilebilir bir B2B müşteri puanlama çekirdeği oluşturmaktır.

## İlk yol haritası

- B2B müşteri puanlama modeli
- Segment bazlı aksiyon önerileri
- CSV içe aktarma ve raporlama
- FastAPI servis katmanı
- Basit yönetim paneli
- Otomatik test ve CI

## Geliştirme yaklaşımı

Kod tabanı küçük, test edilebilir ve açıklanabilir bileşenlerle ilerler. Puanlama kuralları yapay zekâ destekli geliştirilebilir ancak sonuçlar deterministik olmalı ve her kural testlerle doğrulanmalıdır.
