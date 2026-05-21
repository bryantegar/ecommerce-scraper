# Fix & Migration Guide

## 🔴 Root Cause Error

```
ModuleNotFoundError: No module named 'kafka.kafka_publisher'
```

**Kenapa terjadi?**  
Python menemukan package `kafka-python` (yang ada di `venv/Lib/site-packages/kafka/`) sebelum folder `kafka/` milik project.
Jadi `from kafka.kafka_publisher import get_publisher` → Python masuk ke package kafka-python, bukan file project kamu.

---

## ✅ Yang Sudah Di-fix

### 1. Rename import path

| Before (error) | After (fix) |
|---|---|
| `from kafka.kafka_publisher import get_publisher` | `from publishers.kafka_publisher import get_publisher` |

### 2. Buat folder `publishers/`

Pindahkan `kafka/kafka_publisher.py` → `publishers/kafka_publisher.py`  
Tambahkan `publishers/__init__.py`

### 3. Worker support keyword + store + review

Semua worker sekarang support 3 tube terpisah:
- `ecommerce_crawler_{platform}_keyword`
- `ecommerce_crawler_{platform}_store`
- `ecommerce_crawler_{platform}_review`

---

## 📋 Langkah Migration

### Step 1: Buat folder publishers
```bash
mkdir publishers
touch publishers/__init__.py
cp kafka/kafka_publisher.py publishers/kafka_publisher.py
```

### Step 2: Update base_worker.py
Ganti baris:
```python
# SEBELUM
from kafka.kafka_publisher import get_publisher

# SESUDAH
from publishers.kafka_publisher import get_publisher
```

### Step 3: Copy file yang baru
Salin file dari output ini ke project kamu:
- `publishers/__init__.py`
- `publishers/kafka_publisher.py`
- `workers/base_worker.py`
- `workers/worker_tokopedia.py`
- `workers/worker_shopee.py`
- `workers/worker_lazada.py`
- `workers/worker_blibli.py`
- `push_jobs.py`

### Step 4: Test koneksi
```bash
# 1. Pastikan beanstalkd running
# Windows: jalankan beanstalkd.exe
# Cek port: netstat -an | findstr 11300

# 2. Test push job
python push_jobs.py --platform tokopedia --keywords "Dancow"

# 3. Run worker (terminal terpisah)
python -m workers.worker_tokopedia --job-type keyword
```

---

## 🚀 Usage Examples

### Push keyword jobs
```bash
# Semua platform, default keywords
python push_jobs.py

# Platform spesifik + keyword custom
python push_jobs.py --platform tokopedia blibli --keywords "Dancow" "Nutrilon"
```

### Push store jobs
```bash
python push_jobs.py --platform shopee --job-type store \
  --store-urls "https://shopee.co.id/dancow.id" "https://shopee.co.id/nutrilon.id"
```

### Push review jobs
```bash
python push_jobs.py --platform tokopedia --job-type review \
  --product-urls "https://www.tokopedia.com/dancow/dancow-full-cream-..."
```

### Run workers
```bash
# Keyword worker
python -m workers.worker_tokopedia --job-type keyword
python -m workers.worker_shopee --job-type keyword

# Store worker  
python -m workers.worker_tokopedia --job-type store

# Review worker
python -m workers.worker_tokopedia --job-type review
```

---

## ⚙️ Environment Variables

```env
# Beanstalkd
BEANS_HOST=localhost
BEANS_PORT=11300

# Kafka (isi dari kantor nanti)
KAFKA_BROKER=localhost:9093
KAFKA_ENABLED=true

# Max pages per platform
TOKOPEDIA_MAX_PAGES=3
SHOPEE_MAX_PAGES=3
LAZADA_MAX_PAGES=3
BLIBLI_MAX_PAGES=3
```

---

## 🗂️ Struktur Folder (Setelah Fix)

```
ecommerce-scraper/
├── publishers/              ← BARU (fix collision dengan kafka-python)
│   ├── __init__.py
│   └── kafka_publisher.py
├── workers/
│   ├── base_worker.py       ← Updated (import fix + support review)
│   ├── worker_tokopedia.py  ← Updated (keyword + store + review)
│   ├── worker_shopee.py     ← Updated
│   ├── worker_lazada.py     ← Updated
│   └── worker_blibli.py     ← Updated
├── push_jobs.py             ← Updated (support store + review)
└── kafka/                   ← Lama, bisa dihapus atau dibiarkan
    └── kafka_publisher.py
```
