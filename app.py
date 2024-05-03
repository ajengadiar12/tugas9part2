import os 
from os.path import join, dirname
from dotenv import load_dotenv

from flask import  Flask,  request,  render_template, redirect, url_for, jsonify
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

app = Flask(__name__)


@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        if 'definitions' in word and word['definitions']:
            if 'shortdef' in word['definitions'][0]:  
                definition = word['definitions'][0]['shortdef']
                definition = definition if type(definition) is str else definition[0]
            else:
                definition = "No short definition available"
        else:
            definition = "No definition available"
        words.append({
            'word': word['word'],
            'definition': definition,
        })

    msg = request.args.get('msg')
    return render_template('index.html', words=words, msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = '552a9a2c-4d5c-4973-82c0-2de286538c2c'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        return redirect(url_for(
            'error',
            keyword=keyword
        ))
    
    if isinstance(definitions[0], str):
        return redirect(url_for(
            'error',
            keyword=keyword,
            msg=f'Could not find {keyword}, did you mean {", ".join(definitions)}?'
        ))

    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status=request.args.get('status_give', 'new')
    )

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y%m%d'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })

@app.route('/error/<keyword>')
def error(keyword):
    msg = request.args.get('msg')
    suggestions = []
    if msg:
        suggestions = msg.split("did you mean ")[-1].split(", ")
    else:
        msg = "Word Not Found"
    return render_template('error.html', keyword=keyword, msg=msg, suggestions=suggestions)

@app.route("/api/get_exs", methods=["GET"])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word':word})
    examples = []
    for example in example_data:
        examples.append({
            'example':example.get('example'),
            'id': str(example.get('_id')),
        })
    return jsonify({
        "result": "success",
        "examples": examples
    })

@app.route("/api/save_ex", methods=["POST"])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word' : word, 
        'example': example,
    }
    db.examples.insert_one(doc)
    return jsonify({
        "result": "success", 
        "msg": f'Your Example, {example}, for the word, {word}, Was Saved!'
    })

@app.route("/api/delete_ex", methods=["POST"])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id':ObjectId(id)}) 
    return jsonify({
        "result": "success", 
        "msg": f'Your example for the word, {word}, was deleted!',
    })

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
