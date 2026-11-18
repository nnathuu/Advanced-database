from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
orders = client.shop.orders

orders.delete_many({"_id": {"$gte": 1005, "$lte": 1009}})

orders.insert_many([
    {"_id": 1005, "customer": {"name": "An", "city": "Hanoi"}, "status": "paid",
     "items": [{"sku": "BK-01", "title": "Python Basics", "qty": 3, "price": 12.5}]},
    {"_id": 1006, "customer": {"name": "Binh", "city": "Hue"}, "status": "pending",
     "items": [{"sku": "BK-03", "title": "Data Viz", "qty": 1, "price": 22}],
     "tags": ["gift", "express"]},                       # có thêm tags
    {"_id": 1007, "customer": {"name": "Chi", "city": "Da Nang",
                               "address": {"street": "Le Loi", "no": 12}},  # lồng thêm address
     "status": "shipped",
     "items": [{"sku": "BK-07", "title": "SQL in Practice", "qty": 2, "price": 18},
               {"sku": "BK-01", "title": "Python Basics", "qty": 1, "price": 12.5}]},
    {"_id": 1008, "customer": {"name": "Dung", "city": "Hanoi"}, "status": "paid",
     "items": [{"sku": "BK-03", "title": "Data Viz", "qty": 2, "price": 22}],
     "coupon": "SALE10"},                                # có thêm coupon
    {"_id": 1009, "customer": {"name": "Em", "city": "Hue"}, "status": "cancelled",
     "items": []},                                       # không có sản phẩm
])

# Tìm mọi đơn chứa sku BK-01
for doc in orders.find({"items.sku": "BK-01"}):
    print(doc["_id"], doc["customer"]["name"])