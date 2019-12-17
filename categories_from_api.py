import requests
from utils import load_config
import json
import pandas as pd


categories = []
r = requests.get(load_config()['api_url'] + 'categories')
r = r.json()['results']

pd.DataFrame(r)

categories = { x['name']: {'id': x['id'], 'icon': x['icon'], 'type': '-' if x['sign']<0 else '+'} for x in r }
with open('categories.json', 'w') as f:
    json.dump(categories, f, indent=1)