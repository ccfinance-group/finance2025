import json

data = {"name": "小明", "score": 60}
1
#ensure_ascii = False
json_str = json.dumps(data, ensure_ascii = True)
print(json_str)

print(ord('小'))
print(ord('明'))