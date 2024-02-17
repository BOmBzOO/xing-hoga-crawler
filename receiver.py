from datetime import datetime
import pythoncom
import pandas as pd
import sqlite3
from config import TICKER_DATA_FOLDER_PATH
from utility.setting import ui_num, DICT_SET, DB_STOCK_TICK, DB_STOCK_HOGA, DB_FUTURE_TICK, DB_FUTURE_HOGA, DB_STOCK_BROKER, DB_STOCK_VI
from utility.api import XingAPI
from utility.real_time import (
    RealTimeKospiOrderBook,
    RealTimeKospiTick,
    RealTimeKosdaqOrderBook,
    RealTimeKosdaqTick,
    RealTimeStockViOnOff,
    RealTimeKospiBrokerInfo,
    RealTimeKosdaqBrokerInfo,

    RealTimeStockFuturesOrderBook,
    RealTimeStockFuturesTick,
    RealTimeStockAfterMarketKospiOrderBook,
    RealTimeStockAfterMarketKospiTick,
    RealTimeStockAfterMarketKosdaqOrderBook,
    RealTimeStockAfterMarketKosdaqTick,
)
from utility.utility import make_dir

make_dir(TICKER_DATA_FOLDER_PATH)
TODAY = datetime.today().strftime("%Y-%m-%d")
TODAY_PATH = f"{TICKER_DATA_FOLDER_PATH}/{TODAY}"
make_dir(TODAY_PATH)

class Receiver:
    def __init__(self, kospi_qlist, kosdaq_qlist, windowQ):
        self.kospi_qlist = kospi_qlist
        self.kosdaq_qlist = kosdaq_qlist
        self.windowQ = windowQ

        _ = XingAPI.login(is_real_server=True)
        massage = f'시스템 명령 실행 알림 - 로그인 성공'
        self.windowQ.put([ui_num['S로그텍스트'], massage])
        print(massage)

        self.listed_code_df_kospi = XingAPI.get_listed_code_list(market_type=1)
        self.listed_code_df_kosdaq = XingAPI.get_listed_code_list(market_type=2)
        self.code_list_kospi = self.listed_code_df_kospi['단축코드'].tolist()
        self.code_list_kosdaq = self.listed_code_df_kosdaq['단축코드'].tolist()
        self.code_list_stock = self.code_list_kospi + self.code_list_kosdaq
        
        self.kospi_code_list_split = {}
        for idx in range(len(self.kospi_qlist)):
            temp = [code for i, code in enumerate(self.code_list_kospi) if i % len(self.kospi_qlist) == idx]
            self.kospi_code_list_split[f'kospi{idx}'] = temp
        # print(self.kospi_code_list_split)


        self.kosdaq_code_list_split = {}
        for idx in range(len(self.kosdaq_qlist)):
            temp = [code for i, code in enumerate(self.code_list_kosdaq) if i % len(self.kosdaq_qlist) == idx]
            self.kosdaq_code_list_split[f'kosdaq{idx}'] = temp
        # print(self.kosdaq_code_list_split)

        self.set_db_DB_STOCK_HOGA()

        self.start()

    def start(self):

        """
                "S3_": TICK_FIELDS,                           # 코스피 체결
                "H1_": ORDER_BOOK_FIELDS,                     # 코스피 호가
                "K3_": TICK_FIELDS,                           # 코스닥 체결
                "HA_": ORDER_BOOK_FIELDS,                     # 코스닥 호가
                "K1_": BROKER_INFO_FIELDS,                    # 코스피 거래원
                "OK_": BROKER_INFO_FIELDS,                    # 코스닥 거래원
                "VI_": STOCK_VI_ON_OFF_FIELDS,                # 주식 VI 발동해제
                "JC0": STOCK_FUTURES_TICK_FIELDS,             # 주식선물 체결
                "JH0": STOCK_FUTURES_ORDER_BOOK_FIELDS,       # 주식선물 호가
                "DS3": AFTER_MARKET_TICK_FIELDS,              # 코스피 시간외 단일가 체결
                "DH1": AFTER_MARKET_ORDER_BOOK_FIELDS,        # 코스피 시간외 단일가 호가
                "DK3": AFTER_MARKET_TICK_FIELDS,              # 코스닥 시간외 단일가 체결
                "DHA": AFTER_MARKET_ORDER_BOOK_FIELDS,        # 코스닥 시간외 단일가 호가
        """

        # 코스피 틱
        real_time_kospi = {}
        for idx, key in enumerate(self.kospi_code_list_split.keys()):
            # print(idx, self.kospi_code_list_split[key])
            real_time_kospi[key]  = RealTimeKospiOrderBook(queue=self.kospi_qlist[idx])
            real_time_kospi[key].set_code_list(self.kospi_code_list_split[key])
        # print(real_time_kospi)
        massage = f'시스템 명령 실행 알림 - 리시버 시작 코스닥'
        self.windowQ.put([ui_num['S로그텍스트'], massage])
        print(massage)

        # 코스닥 틱
        real_time_kosdaq = {}
        for idx, key in enumerate(self.kosdaq_code_list_split.keys()):
            real_time_kosdaq[key] = RealTimeKosdaqOrderBook(queue=self.kosdaq_qlist[idx])
            real_time_kosdaq[key].set_code_list(self.kosdaq_code_list_split[key])
        # print(real_time_kosdaq)
        massage = f'시스템 명령 실행 알림 - 리시버 시작 코스피'
        self.windowQ.put([ui_num['S로그텍스트'], massage])
        print(massage)

        while True:
            pythoncom.PumpWaitingMessages()

    def set_db_DB_STOCK_HOGA(self):

        con = sqlite3.connect(DB_STOCK_HOGA)
        cur = con.cursor()
        cur.execute('pragma journal_mode=WAL')
        cur.execute('pragma synchronous=normal')
        cur.execute('pragma temp_store=memory')
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        tables = list(tables['name'])

        # 주식 호가 DB 스키마
        for code in self.code_list_stock:
            if code not in tables:
                query = f'CREATE TABLE "{code}" ("index" REAL, "system_time" REAL, "shcode" TEXT,'\
                        '"hotime" TEXT, "donsigubun" INTEGER, "totofferrem" INTEGER, "totbidrem" INTEGER,'\
                        '"offerho1" INTEGER, "bidho1" INTEGER, "offerrem1" INTEGER, "bidrem1" INTEGER,'\
                        '"offerho2" INTEGER, "bidho2" INTEGER, "offerrem2" INTEGER, "bidrem2" INTEGER,'\
                        '"offerho3" INTEGER, "bidho3" INTEGER, "offerrem3" INTEGER, "bidrem3" INTEGER,'\
                        '"offerho4" INTEGER, "bidho4" INTEGER, "offerrem4" INTEGER, "bidrem4" INTEGER,'\
                        '"offerho5" INTEGER, "bidho5" INTEGER, "offerrem5" INTEGER, "bidrem5" INTEGER,'\
                        '"offerho6" INTEGER, "bidho6" INTEGER, "offerrem6" INTEGER, "bidrem6" INTEGER,'\
                        '"offerho7" INTEGER, "bidho7" INTEGER, "offerrem7" INTEGER, "bidrem7" INTEGER,'\
                        '"offerho8" INTEGER, "bidho8" INTEGER, "offerrem8" INTEGER, "bidrem8" INTEGER,'\
                        '"offerho9" INTEGER, "bidho9" INTEGER, "offerrem9" INTEGER, "bidrem9" INTEGER,'\
                        '"offerho10" INTEGER, "bidho10" INTEGER, "offerrem10" INTEGER, "bidrem10" INTEGER)'
                # self.save0Q.put(['S_HOGA', query])
                # query = f'CREATE INDEX "ix_{code}_index" ON "{code}"("index")'
                # self.save0Q.put(['S_HOGA', query])
                cur.execute(query)
                con.commit()
            else: 
                pass
        con.close()
        massage = f'시스템 명령 실행 알림 - 데이터베이스 준비 완료'
        self.windowQ.put([ui_num['S로그텍스트'], massage])
        print(massage)



    

    


