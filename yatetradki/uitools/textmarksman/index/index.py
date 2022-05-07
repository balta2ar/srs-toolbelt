import argparse
import csv
import logging

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

app = Flask(__name__, static_folder='static', template_folder='static')
IMAGES = ''
INDEX = {}


def read_index(path):
    index = {}
    with open(path, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            index[row[0]] = row[1:]
    return index


def save_index(index):
    with open('index.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for key, value in index.items():
            writer.writerow([key] + value)


# def load_images(path):
#     images = {}
#     for path in glob(path):
#          basename(path)


@app.route('/')
def root():
    items = []
    for name, (left, right) in INDEX.items():
        items.append({'name': name, 'left': left, 'right': right})
    items = sorted(items, key=lambda x: x['name'])
    return render_template('index.html', items=items, images=IMAGES)


@app.route('/change', methods=['POST'])
def change():
    name = request.args.get('name')
    index = request.args.get('index')
    value = request.args.get('value')
    if name and index and value:
        old = INDEX[name][int(index)]
        INDEX[name][int(index)] = value
        if old != value:
            logging.info('Changed "{}" #{} {}=>{}'.format(name, index, old, value))
            # save_index(INDEX)
            return jsonify({'status': 'ok', 'state': 'modified'})
    return jsonify({'status': 'ok', 'state': 'unmodified'})


def main():
    app.run(host='0.0.0.0', port=8080, debug=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run index editor')
    parser.add_argument('--images', type=str, help='Path to imades folder')
    parser.add_argument('--index', type=str, help='Path to index file')
    args = parser.parse_args()
    # IMAGES = load_images(args.images)
    # logging.info('Found {} images'.format(len(IMAGES)))
    IMAGES = args.images.rstrip('/')
    INDEX = read_index(args.index)
    logging.info('Loaded {} index entries'.format(len(INDEX)))
    main()
