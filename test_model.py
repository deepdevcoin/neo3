import requests
import json
import config


MODEL = config.MODEL  # or hardcode
API = config.API

# Test basic model call
payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant. When I say 'test', respond with 'working'."},
        {"role": "user", "content": "test"}
    ],
    "stream": True
}

print("Testing model connection...")
resp = requests.post(API, json=payload, stream=True)

full = ""
for line in resp.iter_lines():
    if not line:
        continue
    data = json.loads(line)
    if data.get("done"):
        break
    chunk = data.get("message", {}).get("content", "")
    if chunk:
        print(chunk, end="", flush=True)
        full += chunk

print(f"\n\nFull response: {full}")
print("✅ Model is responding!" if full else "❌ Model not responding")