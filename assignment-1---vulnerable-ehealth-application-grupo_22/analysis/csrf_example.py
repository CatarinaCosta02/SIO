from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['POST'])
def result():
    for k, v in request.form.items():
        print(k, v, sep=': ')
    return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
