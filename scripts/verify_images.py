"""Quick script to verify products have correct image URLs."""
from pymongo import MongoClient
import os

client = MongoClient(os.environ['AZURE_COSMOS_CONNECTION_STRING'])
db = client['ketzagenticecomm']
products = db['products']

count = products.count_documents({})
print(f'Total products: {count}')

# Check sample products from each category
categories = ['power_tools', 'hand_tools', 'paint', 'plumbing', 'electrical', 'appliances']

print('\nSample products:')
for cat in categories:
    sample = products.find_one({'category': cat})
    if sample:
        name = sample.get('name', 'N/A')[:40]
        img_url = sample.get('image_url', 'N/A')[:60]
        print(f'  {cat}: {name}... -> {img_url}...')

# Check for any placeholder URLs still present
placeholder_count = products.count_documents({'image_url': {'$regex': 'placehold'}})
print(f'\nProducts with placeholder images: {placeholder_count}')

# Check for unsplash URLs
unsplash_count = products.count_documents({'image_url': {'$regex': 'unsplash'}})
print(f'Products with Unsplash images: {unsplash_count}')
