from flask import Flask, request
from flask import jsonify, render_template
from stocks import getMinVarPortfolio

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/minVarPortfolio', methods=['POST'])
def stock_returns():
	body = request.json
	first_stock = body['stock1']
	second_stock = body['stock2']
	rf = float(body['riskFreeRate'])
	try:
		wA, wB, mean, stdev = getMinVarPortfolio(first_stock, second_stock, rf)
		return(jsonify({'wA': wA, 'wB': wB, 'mean': mean, 'stdev': stdev, 'msg': 'success'}))
	except:
		return(jsonify({'msg': 'error'})), 401