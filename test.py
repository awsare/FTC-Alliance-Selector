from flask import *

app = Flask(__name__)

@app.route('/home/')
def home():
	return "Hi"

if __name__ == '__main__':
	app.run(debug=False,host='0.0.0.0',port=5000)