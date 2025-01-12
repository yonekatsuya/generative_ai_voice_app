import urllib.parse
import json

url = __file__
qs = urllib.parse.urlparse(url).query
qs_d = urllib.parse.parse_qs(qs)

obj = {"name": "taro"}

jsonObj = json.dumps(obj)
return jsonObj