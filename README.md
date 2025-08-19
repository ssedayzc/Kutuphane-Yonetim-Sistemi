# 📚 Kütüphane Yönetim Sistemi

<p align="center">
  <img src="https://dummyimage.com/1200x300/16697A/FFFFFF&text=K%C3%BCt%C3%BCphane+Y%C3%B6netim+Sistemi" alt="Library Banner" />
</p>

<p align="center">
  <a href="#kurulum"><img src="https://img.shields.io/badge/Kurulum-Kolay-489FB5?style=for-the-badge" /></a>
  <a href="#ozellikler"><img src="https://img.shields.io/badge/%C3%96zellikler-Zengin-82C0CC?style=for-the-badge" /></a>
  <a href="#kullanim"><img src="https://img.shields.io/badge/Kullan%C4%B1m-H%C4%B1zl%C4%B1-FFA62B?style=for-the-badge" /></a>
  <a href="#api"><img src="https://img.shields.io/badge/API-FastAPI-16697A?style=for-the-badge" /></a>
</p>

Modern, mobil uyumlu, admin ve kullanıcı rolleri olan; kişisel kitap listeleri ve Open Library entegrasyonlu bir sistem.

---

## 🎨 Tema
Ocean Breeze paleti (projede uygulanmıştır):
- `#16697A` (koyu teal)
- `#489FB5` (mavi)
- `#82C0CC` (açık mavi)
- `#EDE7E3` (açık kum)
- `#FFA62B` (vurgu turuncu)

---

## 🚀 Hızlı Başlangıç {#kullanim}
```bash
pip install -r requirements.txt
uvicorn api:app --reload
```
- Web Arayüzü: `http://localhost:8000`
- Swagger Doküman: `http://localhost:8000/docs`

### Giriş Bilgileri
- Admin: `admin` / `admin123`
- Demo Kullanıcı: `demo` / `demo123`

---

## ✨ Özellikler {#ozellikler}
- 📱 Mobil uyumlu modern UI (Ocean Breeze renkleri)
- 👤 Roller: Admin ve normal kullanıcı
  - Admin: Kütüphaneye kitap ekleme/silme/güncelleme, kütüphaneyi görüntüleme
  - Kullanıcı: Kişisel listeye ekleme, Okunacaklar ve Okuduklarım listeleri, okundu/okunmadı, listeden kaldırma
- 🔍 ISBN ile arama (Open Library API)
- 💾 JSON tabanlı veri kalıcılığı
- ✅ 48+ test ile doğrulanmış çekirdek fonksiyonlar

---

## 🧭 Arayüz

### Admin Paneli
- ISBN ile “Kitap Ara ve Ekle”
- Başlık/Yazar güncelleme
- Kütüphane listesinde silme/görüntüleme

### Kullanıcı Paneli
- ISBN ile kendi listene ekle
- Okunacaklar ve Okuduklarım listeleri
- Okundu/Okunmadı durumunu değiştir, listeden kaldır

---

## 🔌 API {#api}
Örnekler:
```bash
# Giriş
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'

# Admin: Kitap Ekle
curl -X POST "http://localhost:8000/admin/books" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <TOKEN>" \
     -d '{"isbn":"978-0199535675"}'

# Admin: Kitap Güncelle (başlık/yazar)
curl -X PATCH "http://localhost:8000/admin/books/978-0199535675" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <TOKEN>" \
     -d '{"title":"Yeni Başlık","author":"Yeni Yazar"}'

# Kullanıcı: Listeye Ekle
curl -X POST "http://localhost:8000/me/books" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <TOKEN>" \
     -d '{"isbn":"978-0199535675"}'
```
---

## 📁 Proje Yapısı
```
library_project/
├── api.py
├── main.py
├── models.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── tests/
└── requirements.txt
```

---

## 🧪 Test
```bash
pytest -q
```

---

## 📜 Lisans
MIT
