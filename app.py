from json import dumps
import os
import uuid
from urllib.request import urlopen

import numpy as np
import requests
from flask import Flask, render_template, request, send_from_directory, url_for
from keras.preprocessing.image import load_img, img_to_array
from keras.models import load_model
from keras.engine.saving import model_from_json
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import secure_filename, redirect

img_width, img_height = 150, 150
model_path = './models/model.h5'
model_json_path = './models/model.json'
model_weights_path = './models/weights.h5'


def download(url: str, dest_folder: str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    file_name = url.split('/')[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, file_name)

    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))


# Using JSON Model
model_url = 'https://github.com/akbarsaputrait/flower-cnn/releases/download/v0.0.1/model.json'
json_file = urlopen(model_url)
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)

# Using h5 Model
# model = load_model(model_path)
# model.load_weights(model_weights_path)
# model_url = 'https://github.com/akbarsaputrait/flower-cnn/releases/download/v0.0.1/model.h5'
# download(model_url, './models/')
# model = load_model(model_path)

weight_url = 'https://github.com/akbarsaputrait/flower-cnn/releases/download/v0.0.1/weights.h5'
download(weight_url, './models/')
model.load_weights(model_weights_path)

model._make_predict_function()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def predict(file):
    x = load_img(file, target_size=(img_width, img_height))
    x = img_to_array(x)
    x = np.expand_dims(x, axis=0)
    array = model.predict(x)
    result = array[0]
    answer = np.argmax(result)
    return answer


def my_random_string(string_length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4())  # Convert UUID format to a Python string.
    random = random.upper()  # Make all characters uppercase.
    random = random.replace("-", "")  # Remove the UUID '-'.
    return random[0:string_length]  # Return the random string.


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('./index.html', label='', latin='', imagesource='/static/images/flower-rose.jpg')


@app.route('/submit', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        import time
        start_time = time.time()
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            result = predict(file_path)
            label = ''
            latin = ''
            if result == 0:
                label = 'Daisy'
                latin = 'Bellis Perennis'
            elif result == 1:
                label = 'Rose'
                latin = 'Rosa'
            elif result == 2:
                label = 'Sunflowers'
                latin = 'Helianthus Annuus'
            print(result)
            print(label)
            print(file_path)
            filename = my_random_string(6) + filename

            os.rename(file_path, os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("--- %s seconds ---" % str(time.time() - start_time))
            return render_template('index.html', label=label, latin=latin, imagesource='../uploads/' + filename)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


app.add_url_rule('/uploads/<filename>', 'uploaded_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads': app.config['UPLOAD_FOLDER']
})

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
