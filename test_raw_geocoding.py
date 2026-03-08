import requests
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('HUAWEI_LOCATION_API_KEY')
url = f'https://siteapi-dre.cloud.huawei.com/mapApi/v1/siteService/geocode?key={quote_plus(key)}'

addresses = ['Times Square, New York', 'Eiffel Tower, Paris']

for addr in addresses:
    print(f'{addr}:')
    resp = requests.post(url, json={
        'address': addr, 
        'language': 'en'
    }, headers={
        'Content-Type': 'application/json', 
        'x-agccp-region-id': 'DE'
    })
    data = resp.json()
    if data.get('returnCode') == '0' and data.get('sites'):
        loc = data['sites'][0]['location']
        print(f'  {loc}')
    else:
        print('  Not found')
