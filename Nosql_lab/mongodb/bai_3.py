import random
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client.shop
big = db.orders_big
big.drop()                      # làm sạch để chạy lại được nhiều lần

# 1. Sinh 10.000 document ngẫu nhiên
random.seed(42)
cities = ["Hanoi", "Hue", "Da Nang", "HCMC", "Can Tho"]
statuses = ["paid", "pending", "shipped", "cancelled"]
skus = [f"BK-{i:02d}" for i in range(1, 21)]

docs = []
for i in range(10000):
    docs.append({
        "_id": i,
        "customer": {"name": f"user{i}", "city": random.choice(cities)},
        "status": random.choice(statuses),
        "items": [{"sku": random.choice(skus),
                   "qty": random.randint(1, 5),
                   "price": round(random.uniform(5, 50), 2)}],
    })
big.insert_many(docs)
print("Đã chèn:", big.count_documents({}), "document")

# 2. Hàm chạy explain và in gọn kết quả
query = {"customer.city": "Hanoi", "status": "paid"}

def explain():
    r = db.command({
        "explain": {"find": "orders_big", "filter": query},
        "verbosity": "executionStats",
    })
    plan = r["queryPlanner"]["winningPlan"]
    plan = plan.get("queryPlan", plan)          # phòng trường hợp MongoDB bọc thêm lớp
    while "inputStage" in plan:                 # đi xuống stage dưới cùng
        plan = plan["inputStage"]
    s = r["executionStats"]
    print(f"  stage={plan['stage']} | totalDocsExamined={s['totalDocsExamined']} "
          f"| nReturned={s['nReturned']} | time={s['executionTimeMillis']} ms")

# 3. So sánh trước và sau khi tạo index
print("TRƯỚC khi có index:")
explain()

big.create_index([("customer.city", 1), ("status", 1)])

print("SAU khi có index:")
explain()