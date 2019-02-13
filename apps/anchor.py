from flask import Flask, render_template, redirect, url_for
app = Flask(__name__)

debug = True # Do not enable in production
host = '0.0.0.0'
port = 5000


@app.route('/')
def index():
    return render_template('anvil.html', actor = 'anchor')

@app.route('/connection_request', methods = ['GET', 'POST'])
def hello():
    print('ya boi')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host, port, debug)