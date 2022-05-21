import argparse
import logging

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request

from yatetradki.uitools.index.search import read_index
from yatetradki.uitools.index.search import save_index

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

app = Flask(__name__, static_folder='static', template_folder='static')
IMAGES = ''
INDEX_NAME = ''
INDEX = {}


@app.route('/')
def root():
    global INDEX
    INDEX = read_index(args.index)

    offset = request.args.get('offset')
    offset = int(offset or 0)
    logging.info('offset: {}'.format(offset))
    limit = 100  # request.args.get('limit')
    items = []
    for name, (left, right) in INDEX.items():
        items.append({'name': name, 'left': left, 'right': right})
    items = sorted(items, key=lambda x: x['name'])
    items = items[offset:offset + int(limit or len(items))]
    next = offset + len(items)
    prev = max(0, offset - limit)
    return render_template('index.html', items=items, images=IMAGES, next=next, prev=prev)


@app.route('/change', methods=['POST'])
def change():
    logging.info('change')
    name = request.args.get('name')
    index = request.args.get('index')
    value = request.args.get('value')
    if name and index and value:
        old = INDEX[name][int(index)]
        INDEX[name][int(index)] = value
        if old != value:
            logging.info('Changed "{}" #{} {}=>{}'.format(name, index, old, value))
            save_index(INDEX_NAME, INDEX)
            return jsonify({'status': 'ok', 'state': 'modified'})
    return jsonify({'status': 'ok', 'state': 'unmodified'})


def main():
    app.run(host='0.0.0.0', port=8080, debug=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run index editor')
    parser.add_argument('--images', type=str, help='Path to images folder')
    parser.add_argument('--index', type=str, help='Path to index file')
    args = parser.parse_args()
    # IMAGES = load_images(args.images)
    # logging.info('Found {} images'.format(len(IMAGES)))
    IMAGES = args.images.rstrip('/')
    INDEX_NAME = args.index
    main()
