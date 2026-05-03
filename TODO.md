# TODO

## 1. Fotoğraftan ürün tanıma + ürün veritabanı

- [ ] MCP tool description / system prompt'unda model'e açıkça belirt: **yalnızca yiyecek görselleri** kabul edilir, yiyecek olmayan görsellerde tool çağrılmadan kullanıcıya açıklama yapılır.
  - İkinci bir doğrulama adımı (sampling) yok; filtreleme model'in kendi muhakemesiyle, tool çağrısı öncesinde olur.
- [ ] Yeni tablo: `products` (marka, ürün adı, besin değerleri, kaynak fotoğraf referansı, `last_verified_at`).
- [ ] Akış:
  - Kullanıcı ürünün ön yüzünü çeker → veritabanında varsa bilgileri direkt döndür.
  - Veritabanında yoksa → model kullanıcıdan içerikler/besin değerleri kısmının fotoğrafını ister, parse edip `products` tablosuna ekler.
- [ ] Geçerlilik süresi: ürün kayıtları 6 ayda bir invalidate edilecek (`last_verified_at` + 180 gün). Süresi geçenler kullanıcıdan yeniden çekim isteyecek ve güncellenecek.

## 2. Kayıt amacı (onboarding) + yeme alışkanlığı memory'si

- [ ] Kullanıcı kaydı sırasında "ne amaçla kayıt tutuyorsun?" sorusu (kilo verme, kas kazanma, sağlık takibi, sadece kayıt vb.).
- [ ] `users` tablosuna `goal` / `tracking_purpose` kolonu ekle.
- [ ] Sonradan ayarlardan değiştirilebilsin.
- [ ] Onboarding'in devamında **yeme durumuna dair memory tutulmasına izin** istenecek (opt-in, açık consent).
  - `users` tablosuna `eating_memory_consent: bool` (+ `consent_granted_at` timestamp) kolonu.
  - Sonradan ayarlardan açıp kapatılabilsin; kapatınca memory verisi **kalıcı olarak (hard delete)** silinsin.
- [ ] İzin verildiyse aktifleşecek özellikler:
  - **Gün sonu feedback**: günlük yenenleri özetleyip kullanıcı amacına göre değerlendiren kısa bir mesaj.
  - **Sonraki öğün önerisi**: o güne kadar yenilenler + amaç + (varsa) günlük makro hedefi bağlamında bir sonraki öğün için öneri.
- [ ] Memory içeriği ayrı bir tabloda tutulacak: `user_eating_memory` (user_id FK, içerik, oluşturma/güncelleme zamanları). Consent kapatılınca bu tablodaki ilgili kullanıcı satırları hard delete edilir.

## 3. AI not özeti (her kayıtta)

- [ ] Her yiyecek kaydında AI gidişatla ve kullanıcı amacıyla ilgili kısa bir not üretsin (ör. "Bugün protein hedefinin %70'indesin, akşam yemeğinde tavuk düşünebilirsin").
- [ ] Notlar kayda bağlı saklansın (entry-level note) veya günlük özet olarak (daily summary) — hangisi daha mantıklı, karar ver.
- [ ] Kullanıcı amacını (madde 2) bağlam olarak prompt'a dahil et.

## 4. Kullanıcı adı (username)

- [ ] `users` tablosuna `username` kolonu (unique, nullable=False, lowercase).
- [ ] Register flow'unda email + password'e ek olarak username iste.
- [ ] Login email **veya** username ile yapılabilsin (ikisinden biri).
- [ ] Mevcut kullanıcılar için Alembic migration: nullable olarak ekle, backfill, sonra NOT NULL'a çevir.
