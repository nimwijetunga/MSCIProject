import yfinance as yf
import pandas as pd
from scipy.optimize import minimize
import numpy as np 
import argparse


def getStockInfo(first_stock, second_stock):
	fs = yf.Ticker(first_stock)
	ss = yf.Ticker(second_stock)
	if not fs or not ss:
		return None
	fs_history = fs.history(start="2018-06-01", end="2019-06-01")
	ss_history = ss.history(start="2018-06-01", end="2019-06-01")
	fs_history = fs_history.rename(columns={'Close':'fs_close'})
	ss_history = ss_history.rename(columns={'Close':'ss_close'})
	history = pd.concat([fs_history, ss_history], axis=1)
	returns = history[['fs_close','ss_close']]
	returns_daily  = returns.pct_change()
	returns_annual = (1+returns_daily.mean())**365-1
	cov_daily = returns_daily.cov()
	cov_annual = cov_daily * 365
	returns = np.array(returns_annual)
	covar = np.array(cov_annual)
	return returns, covar

def portMean(wA, wB, rA, rB):
	return wA * rA + wB * rB

def portStd(wA, wB, vA, vB, cov):
	return (wA**2*vA + wB**2*vB + 2*wA*wB*cov)**(1/2.0)

def getMinVarPortfolio(returns, covar):
	wss = (covar[0,0] - covar[0,1])/(covar[1,1] + covar[0,0] - 2*covar[0,1])
	wfs = 1-wss
	return(wfs, wss, portMean(wfs, wss, returns[0], returns[1]), portStd(wfs,wss,covar[0,0],covar[1,1],covar[0,1]))

def getMarketPorfolioProportions(returns, covar, rf):
	bnds = ((0.0, 1.0), (0.0, 1.0))
	def negSharpeRatio(params, *args):
		rA, rB, rf, vA, vB, cov = args
		wA, wB = params
		mean = portMean(wA, wB, rA, rB)
		std = portStd(wA, wB, vA, vB, cov)
		return -(mean - rf)/std
	max_ratio = minimize(negSharpeRatio, [0.5, 0.5], 
						args=(returns[0], returns[1], rf, covar[0,0], covar[1,1], covar[0,1]),
						bounds=bnds,
						constraints=({'type': 'eq','fun': lambda x: x[0]+x[1]-1}))
	return max_ratio.x[0], max_ratio.x[1]

def sharpeRatio(wA, wB, rA, rB, rf, vA, vB, cov):
	mean = portMean(wA, wB, rA, rB)
	std = portStd(wA, wB, vA, vB, cov)
	return (mean - rf)/std

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("first_stock")
	parser.add_argument("second_stock")
	parser.add_argument("risk_free_rate")
	args = parser.parse_args()
	returns, covar = getStockInfo(args.first_stock, args.second_stock)
	wA, wB, mean, stdev = getMinVarPortfolio(returns, covar)
	print('MVP Proportion of %s: %s %%' % (args.first_stock, round(wA * 100,2)))
	print('MVP Proportion of %s: %s %%' % (args.second_stock, round(wB * 100, 2)))
	print('MVP standard deviation: %s %%' % (round(stdev*100, 2)))
	print('MVP Expected Portfolio Return: %s %%' % (round(mean*100, 2)))
	print('\n\n\n\n')
	risk_free_rate = float(args.risk_free_rate)
	marketA, marketB = getMarketPorfolioProportions(returns, covar, risk_free_rate)
	sharpeRatio = sharpeRatio(marketA,marketB,returns[0], returns[1], risk_free_rate, covar[0,0], covar[1,1], covar[0,1])
	print('Maximium Sharpe Ratio %s' % (round(sharpeRatio,2)))
	print('Market Portfolio Proportion of %s: %s %%' % (args.first_stock, round(marketA * 100,2)))
	print('Market Portfolio Proportion of %s: %s %%' % (args.second_stock, round(marketB * 100, 2)))
	print('Market Portfolio standard deviation: %s %%' % (round(portStd(marketA, marketB, covar[0,0], covar[1,1], covar[0,1])*100, 2)))
	print('Market Portfolio Expected Portfolio Return: %s %%' % (round(portMean(marketA, marketB, returns[0], returns[1])*100, 2)))
