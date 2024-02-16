import matplotlib.pyplot as plt

import yfinance as yf
from jugaad_data.rbi import RBI
import datetime as dt
import gnews

import numpy
import pandas as pd

class StockInfo():
	def __init__(self):
	
		self.today = dt.datetime.today().date()
		self.o_y = dt.timedelta(days = 365)
		
		#calculate Index (NIFTY50) returns in last 7,31 and 365 sessions

		idx_year = yf.download('^NSEI',start = self.today - self.o_y,end = self.today)['Adj Close']

		self.idx_week = (idx_year[-1] - idx_year[-8]) / idx_year[-8]
		self.idx_month = (idx_year[-1] - idx_year[-31]) / idx_year[-31]
		self.idx_year = (idx_year[-1] - idx_year[0]) / idx_year[0]



	def helper_function(self,ticker,metric):
	    d = ticker.info
	    
	    if metric == 'trailingEps':
	        try:
	            return numpy.round((d['profitMargins'] * d['totalRevenue'])/d['sharesOutstanding'],2)
	        except:
	            return 'NIL'

	    if metric == 'trailingPE':
	        try:
	            eps = (d['profitMargins'] * d['totalRevenue'])/d['sharesOutstanding']
	            return np.round(d['currentPrice']/eps,2)
	        except:
	            return 'NIL'

	    if (metric == 'debtToEquity') or (metric == 'trailingAnnualDividendYield'):
	        return 'NIL'

	    if metric == 'beta':
	        index_annual_data = yf.Ticker('^NSEI').history(period='1y')['Close']
	        ticker_annual_data = ticker.history(period='1y')['Close']
	        
	        #calculate log returns
	        ticker_returns = numpy.log((ticker_annual_data / ticker_annual_data.shift(1)).dropna().astype('float64'))
	        index_returns = numpy.log((index_annual_data / index_annual_data.shift(1)).dropna().astype('float64'))
	        _min = min([len(index_returns),len(ticker_returns)])
	                   
	        #calculate covariance b/w market and stock, and market variance
	        cov_ticker_index = numpy.cov(ticker_returns[-_min::],index_returns[-_min::])[0][1]
	        var_index = numpy.var(index_returns)

	        return numpy.round(cov_ticker_index / var_index,2)

	def StockPerformanceMetrics(self,ticker='^NSEI'):

		today = self.today
		o_y = self.o_y
		
		ticker_name = ticker
		ticker = yf.Ticker(ticker=ticker)
		annual_data = ticker.history(start = today - o_y,end = today)['Close']
		oy_50 = ticker.history(start = today - o_y - dt.timedelta(50),end = today)['Close']

		# Calculate returns for 7,31 and 365 sessions
		week = (annual_data[-1] - annual_data[-8]) / annual_data[-8]
		month = (annual_data[-1] - annual_data[-31]) / annual_data[-31]
		year = (annual_data[-1] - annual_data[0]) / annual_data[0]

		# Technical Ratios and other informations
		stock_data = {'One Week returns' : str(numpy.round(week*100,2))+"%",
		             'One Month returns': str(numpy.round(month*100,2))+"%",
		             'One Year returns' : str(numpy.round(year*100,2))+"%"}

		benchmark_data = {'Index One week returns' : str(numpy.round(self.idx_week*100,2))+"%",
						  'Index One month returns' : str(numpy.round(self.idx_month*100,2))+"%",
						  'Index One year returns' : str(numpy.round(self.idx_year*100,2))+"%"}

		target_metrics = ['industryDisp','trailingEps','trailingPE','beta','debtToEquity','trailingAnnualDividendYield']
		metric_genral_name = ['Industry',
		                      'Trailing Earnings Per Share',
		                      'Trailing Price to earning ratio',
		                      'Systematics Risk / Beta',
		                      'Debt to Equity ratio',
		                      'Annual Dividend Yeild']

		for i,metric in enumerate(target_metrics):
		    if metric in ticker.info.keys():
		        stock_data[metric_genral_name[i]] = numpy.round(ticker.info[metric],2) if metric != 'industryDisp' else ticker.info[metric] 
		    else:
		        stock_data[metric_genral_name[i]] = self.helper_function(ticker,metric)


		stock_data['Trailing Earnings Per Share'] = "INR " + str(stock_data['Trailing Earnings Per Share']) 
		

		r = RBI()
		rbi_data = r.current_rates()
		benchmark_data["1 year Treasury Bill's yeid"] = rbi_data['364 day T-bills']
		benchmark_data['Bank rate of intrest'] = rbi_data['Bank Rate']
		
		# Simple moving average
		sma_50 = [sum(oy_50[i:i-50:-1])/50 for i in range(len(oy_50))]

		# Plot price graph
		fig = plt.figure(figsize=(10,5))
		sub = fig.add_subplot(111)

		sub.plot(annual_data,alpha=0.6,color='#eb444c',linewidth=0.8,label='Price')
		if len(sma_50) > 0.5*(len(annual_data)):
		    sub.plot(list(oy_50.index)[50:],sma_50[50:],color='#31d3d6',label='50 DMA',linewidth=2)

		sub.text(annual_data.index[0],annual_data[0],f'Rs. {numpy.round(annual_data[0],2)}',fontsize=12)
		sub.text(annual_data.index[-30],annual_data[-1],f'Rs. {numpy.round(annual_data[-1],2)}',fontsize=11)

		sub.set_title(ticker_name.split('.')[0])
		sub.yaxis.tick_right()
		sub.legend()

		return [fig,stock_data,benchmark_data]

	def fetch_recent_devlopments(self,ticker='^NSEI'):
		gn = gnews.GNews()
		gn.max_results = 5 #limiting to 5 headlines to keep number of input tokens smaller

		devlopments = ""
		for e,i in enumerate(gn.get_news(f'{ticker.split(".")[0]} stock news')):
		    devlopments += (f'{e+1}) '+i['title'].split(' - ')[0] + '. '+'\n')

		return devlopments
