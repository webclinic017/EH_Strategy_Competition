import backtrader as bt
from pykrx import stock
import pandas as pd

class MyStrategy(bt.Strategy): # bt.Strategy를 상속함

    # 볼린저 밴드에 사용할 이동평균일 수와 표준편차에 곱할 상수를 정의한다.
    params = (
        ("period", 20),
        ("devfacter",2),
        ("debug",False)
    )
    
    # 프롬프트에 매수 or 매도, 매수매도 가격, 개수를 출력한다.
    def log(self,txt, dt=None):
        ''' Logging function fot this strategy '''
        dt = dt or self.data.datetime[0]
        if isinstance(dt,float):
            dt = bt.num2date(dt)
        print("%s, %s"% (dt.isoformat(), txt))
    
    
    def __init__(self):
        
        # 볼린저 밴드 지표를 가져온다
        self.boll = bt.indicators.BollingerBands(period = self.p.period, 
                                                plot =True)
    def next(self):
        global size
        if not self.position: # 매수한 종목이 없다면
            if self.data.low[0] < self.boll.lines.bot[0]: # 저가 < 볼린저 밴드 하한선이면(종가로 수정 요망)
                bottom = self.boll.lines.bot[0]             
                size = int(self.broker.getcash() /bottom) # size는 매수 또는 매도 개수로 현재 금액에서 타겟가격으로 나누어준다.
                                                          # 볼린저 밴드 하한선에서 구매시 최대 구매 가능 개수
                self.buy(price=bottom, size=size)         # 매수 size 즉 구매 개수 설정
                self.log("BUY CREATE, %.2f" % (bottom))   # 프롬프트에 매수 로그 출력
                print(size,"EA")
        else:
            if self.data.high[0] > self.boll.lines.mid[0]:              # 고가 > 볼린저 밴드 중간선이면(종가로 수정 요망) 
                self.sell(price=self.boll.lines.mid[0], size=size)      # 매도: 20일 이동 평균선 = 볼린저 밴드 중간선
                self.log('SELL CREATE, %2.f' % (self.boll.lines.mid[0]))# 프롬프트에 매도 로그 출력
                print(size, 'EA')

size = 0 
stock_name = "KODEX 200"
stock_from = "20171125"
stock_to = "20211125"

stock_list = pd.DataFrame({'종목코드':stock.get_etf_ticker_list(stock_to)})
stock_list['종목명'] = stock_list['종목코드'].map(lambda x: stock.get_etf_ticker_name(x))
stock_list.head()

ticker = stock_list.loc[stock_list['종목명']==stock_name, '종목코드']
df = stock.get_etf_ohlcv_by_date(fromdate=stock_from, todate=stock_to, ticker=ticker)
df = df.drop(['NAV','거래대금','기초지수'], axis=1)
df = df.rename(columns={'시가':'open', '고가':'high', '저가':'low', '종가':'close', '거래량':'volume'})

df["open"]=df["open"].apply(pd.to_numeric,errors="coerce")
df["high"]=df["high"].apply(pd.to_numeric,errors="coerce")
df["low"]=df["low"].apply(pd.to_numeric,errors="coerce")
df["close"]=df["close"].apply(pd.to_numeric,errors="coerce")
df["volume"]=df["volume"].apply(pd.to_numeric,errors="coerce")

data = bt.feeds.PandasData(dataname=df)
cerebro = bt.Cerebro() # Cerebro 엔진 인스턴스 생성
cerebro.broker.setcash(100000) # 초기자금
cerebro.broker.setcommission(0.00015) # 수수료

cerebro.adddata(data) #data feed를 추가
cerebro.addstrategy(MyStrategy) #Add the trading strategy
cerebro.run()
cerebro.plot(style='candlestick',barup='red',bardown="blue",xtight=True,yTight=True,grid=True) # plot