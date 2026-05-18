from libs.beans import Pusher
import json
import uuid

PLATFORMS = {
    'ecommerce_crawler_tokopedia_keyword': 'tokopedia',
    'ecommerce_crawler_shopee_keyword': 'shopee',
    'ecommerce_crawler_lazada_keyword': 'lazada',
    'ecommerce_crawler_blibli_keyword': 'blibli'
}

keywords = [
    "Friesland Campina",
    "SGM",
    "Vidoran",
    "Dancow",
    "Shanghiang Perkasa",
    "Bebelac",
    "Lactogrow",
    "Healthy Way",
    "Abbot",
    "Mead Johnson",
    "Weyth Nutrition",
    "Nutrilon"
]

print("🚀 Start pushing jobs...\n")

for tubename, platform in PLATFORMS.items():

    print(f"\n📦 Queue: {tubename}")

    pusher = Pusher(
        tubename,
        host='localhost',
        port=11300
    )

    for i, keyword in enumerate(keywords, start=1):

        payload = {
            "job_id": str(uuid.uuid4()),
            "platform": platform,
            "content": keyword,
            "count": 0,
            "max_count": 1
        }

        pusher.setJob(json.dumps(payload))

        print(f"[{i}] PUSHED -> {keyword}")

    pusher.close()

print("\n✅ All jobs pushed successfully!")