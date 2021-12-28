from json import dumps
import os
import uuid

import numpy as np
from flask import Flask, render_template, request, send_from_directory
from keras.preprocessing.image import load_img, img_to_array
from keras.models import load_model
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import secure_filename

img_width, img_height = 150, 150
model_path = './models/model.h5'
model_weights_path = './models/weights.h5'
model = load_model(model_path)
# model.load_weights(model_weights_path)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def predict(file):
    x = load_img(file, target_size=(img_width, img_height))
    x = img_to_array(x)
    x = np.expand_dims(x, axis=0)
    array = model.predict(x)
    result = array[0]
    answer = np.argmax(result)
    if answer == 0:
        print("Label: Daisy")
    elif answer == 1:
        print("Label: Rose")
    elif answer == 2:
        print("Label: Sunflower")
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
    return render_template('./index.html', label='', imagesource='/static/images/flower-rose.jpg')


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
            dumps(file_path)
            result = predict(file_path)
            label = ''
            if result == 0:
                label = 'Daisy'
            elif result == 1:
                label = 'Rose'
            elif result == 2:
                label = 'Sunflowers'
            print(result)
            print(file_path)
            filename = my_random_string(6) + filename

            os.rename(file_path, os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("--- %s seconds ---" % str(time.time() - start_time))
            return render_template('template.html', label=label, imagesource='../uploads/' + filename)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


app.add_url_rule('/uploads/<filename>', 'uploaded_file',
                 build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads': app.config['UPLOAD_FOLDER']
})

if __name__ == '__main__':
    app.run(debug=True)
