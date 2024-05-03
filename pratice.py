import requests

api_key = '552a9a2c-4d5c-4973-82c0-2de286538c2c'
word = 'potato'
url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}'

res = requests.get(url)

definitions = res.json()

for  definition in definitions:
    print(definition)