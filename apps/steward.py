from flask import Flask, render_template
app = Flask(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000


@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello, World'


if __name__ == '__main__':
    app.run(host, port, debug)