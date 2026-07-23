import json
import os
from fastapi.testclient import TestClient
from src.api.main import app
import uuid

os.makedirs('docs', exist_ok=True)

schema = app.openapi()
with open('docs/openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)

print("docs/openapi.json created")

# Generate Postman Collection
collection = {
    "info": {
        "name": "Nifty100 API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": []
}

for path, methods in schema['paths'].items():
    for method, details in methods.items():
        if method.lower() not in ['get', 'post', 'put', 'delete']:
            continue
            
        url_parts = path.strip('/').split('/')
        postman_url = {
            "raw": f"{{{{base_url}}}}{path}",
            "host": ["{{base_url}}"],
            "path": url_parts
        }
        
        request_obj = {
            "method": method.upper(),
            "header": [],
            "url": postman_url
        }
        
        item = {
            "name": details.get('summary', path),
            "request": request_obj,
            "response": []
        }
        collection["item"].append(item)

with open('docs/postman_collection.json', 'w') as f:
    json.dump(collection, f, indent=2)

print("docs/postman_collection.json created")
