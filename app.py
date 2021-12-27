from flask import Flask, render_template

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def hello():
  return render_template('./index.html', label='', imagesource='/static/images/flower-tulip.jpg')

if __name__ == '__main__':
  app.run(debug=True)