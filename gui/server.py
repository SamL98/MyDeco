import sys
sys.path.insert(0, '../deco')

import json
from flask import Flask, jsonify
from os.path import join

from func import Function

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET'])
def home():
    return app.send_static_file('index.html')

@app.route('/js/<path:path>', methods=['GET'])
def get_script(path):
    return app.send_static_file(join('js', path))

@app.route('/cfg', methods=['GET'])
def cfg():
    with open(join('..', 'funcs', '%s.json' % sys.argv[1])) as f:
        func_j = json.load(f)

    func = Function.fromjson(func_j)
    func_j = func.tojson()
    return jsonify(func_j)

if __name__ == '__main__':
    app.run(port=8080)
