# Ecommerce Scraper — Setup & Panduan

Sistem scraping terjadwal untuk Shopee, Lazada, Tokopedia, Blibli, OLX menggunakan Beanstalkd sebagai job queue.

## Arsitektur

```
[Linux Cron / APScheduler]
        │
        ▼
  push_jobs.py  ──────────────────────────────────────┐
        │                                              │
        ▼                                              │
  [Beanstalkd Queue]                                   │
  ┌──────────────────────────────────────┐             │
  │  ecommerce_crawler_shopee_keyword    │             │
  │  ecommerce_crawler_lazada_keyword    │             │
  │  ecommerce_crawler_tokopedia_keyword │             │
  │  ecommerce_crawler_blibli_keyword    │             │
  │  ecommerce_crawler_olx_keyword       │             │
  └──────────────────────────────────────┘             │
        │                                              │
   [Workers]                                           │
   worker_shopee ──── CookieManager ─── [Redis]        │
   worker_lazada ──── CookieManager ─── [Redis]        │
   worker_tokopedia                                     │
   worker_blibli                                        │
   worker_olx                                           │
                                                        │
[cookie_manager/login_handler.py] ─────────────────────┘
  (dijalankan manual saat cookie expired)
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
python -m camoufox fetch  # Download Camoufox browser
```

### 2. Jalankan infrastruktur
```bash
docker-compose up -d beanstalkd
docker-compose ps
```

### 3. Login dan kumpulkan cookie (WAJIB untuk Shopee & Lazada)
```bash
# Login Shopee
python cookie_manager/login_handler.py --platform shopee

# Login Lazada
python cookie_manager/login_handler.py --platform lazada

# Cek status semua cookie
python cookie_manager/login_handler.py --platform status
```

Browser Camoufox akan terbuka. Login secara manual, lalu **tutup browser** — cookie otomatis tersimpan ke Redis.

### 4. Jalankan semua service
```bash
docker-compose up -d
```

### 5. Atau jalankan worker manual (untuk development)
```bash
# Terminal 1 — Worker Shopee
python -m workers.worker_shopee

# Terminal 2 — Worker Tokopedia
python -m workers.worker_tokopedia

# Dst...
```

### 6. Push job manual (untuk testing)
```bash
# Push semua platform
python push_jobs.py

# Push platform tertentu
python push_jobs.py --platform shopee

# Push dengan keyword custom
python push_jobs.py --platform shopee --keywords "Dancow" "SGM"

# Force push meskipun cookie tidak valid (untuk testing)
python push_jobs.py --platform shopee --force
```

---

## Manajemen Cookie

Cookie untuk Shopee dan Lazada disimpan di **Redis dengan TTL otomatis**:
- Shopee: TTL 12 jam
- Lazada: TTL 24 jam

Setelah TTL habis, worker akan berhenti menerima job baru dan log warning.

### Refresh cookie manual:
```bash
python cookie_manager/login_handler.py --platform shopee
```

### Cek status cookie:
```bash
python cookie_manager/login_handler.py --platform status
```

---

## Konfigurasi Environment Variables

| Variable | Default | Keterangan |
|---|---|---|
| `BEANS_HOST` | `localhost` | Alamat Beanstalkd |
| `BEANS_PORT` | `11300` | Port Beanstalkd |
| `REDIS_HOST` | `localhost` | Alamat Redis |
| `SCHEDULER_CRON_HOUR` | `*` | Jam push jobs (cron format) |
| `SCHEDULER_CRON_MINUTE` | `0` | Menit push jobs |

### Contoh jadwal scheduler:
```bash
# Setiap jam
SCHEDULER_CRON_HOUR=*
SCHEDULER_CRON_MINUTE=0

# 2x sehari (jam 6 pagi & 6 sore WIB)
SCHEDULER_CRON_HOUR=6,18
SCHEDULER_CRON_MINUTE=0

# Setiap 30 menit (tidak bisa via CRON_HOUR, gunakan APScheduler IntervalTrigger di scheduler.py)
```

---

## Struktur File

```
ecommerce-scraper/
├── cookie_manager/
│   ├── cookie_manager.py      ← Simpan/ambil cookie dari Redis
│   └── login_handler.py       ← Login browser manual + simpan cookie
├── workers/
│   ├── base_worker.py         ← Base class: retry logic, dead-letter queue
│   ├── worker_shopee.py       ← Worker Shopee (extend BaseWorker)
│   ├── worker_lazada.py
│   ├── worker_tokopedia.py
│   ├── worker_blibli.py
│   └── worker_olx.py
├── scheduler.py               ← APScheduler-based scheduler
├── push_jobs.py               ← Manual job pusher
├── docker-compose.yml
└── requirements.txt
```

---

## Troubleshooting

**Worker Shopee/Lazada langsung berhenti:**
→ Cookie tidak ada di Redis. Jalankan `login_handler.py`.

**Job tidak diproses:**
→ Cek beanstalkd: `docker-compose logs beanstalkd`
→ Cek worker logs: `docker-compose logs worker-shopee`

**Job stuck di queue:**
→ Cek `*_failed` tube di beanstalkd untuk melihat job yang gagal.

**Cookie expired di tengah jalan:**
→ Worker akan otomatis berhenti dan log error. Refresh cookie lalu restart worker.
