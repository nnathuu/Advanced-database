from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
orders = client.shop.orders

pipeline = [
    {"$unwind": "$items"},
    {"$group": {
        "_id": "$customer.city",
        "revenue": {"$sum": {"$multiply": ["$items.qty", "$items.price"]}}
    }},
    {"$sort": {"revenue": -1}},
]
for row in orders.aggregate(pipeline):
    print(row)