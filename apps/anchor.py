from flask import Flask, render_template
app = Flask(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000


@app.route('/')
def index():
    return render_template('anvil.html', actor = 'anchor')

@app.route('/hello', methods = ['GET', 'POST'])
def hello():
    print('ya boi')
    return 'BROOO'


if __name__ == '__main__':
    app.run(host, port, debug)