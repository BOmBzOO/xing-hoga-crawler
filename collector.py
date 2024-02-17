import pandas as pd
from utility.utility import now, strf_time, timedelta_sec, float2str1p6
from utility.setting import ui_num, DICT_SET

"""
        "H1_": ORDER_BOOK_FIELDS,                     # 코스피 호가
        "S3_": TICK_FIELDS,                           # 코스피 체결
        "HA_": ORDER_BOOK_FIELDS,                     # 코스닥 호가
        "K3_": TICK_FIELDS,                           # 코스닥 체결
        "JH0": STOCK_FUTURES_ORDER_BOOK_FIELDS,       # 주식선물 호가
        "JC0": STOCK_FUTURES_TICK_FIELDS,             # 주식선물 체결
        "DH1": AFTER_MARKET_ORDER_BOOK_FIELDS,        # 코스피 시간외 단일가 호가
        "DS3": AFTER_MARKET_TICK_FIELDS,              # 코스피 시간외 단일가 체결
        "DHA": AFTER_MARKET_ORDER_BOOK_FIELDS,        # 코스닥 시간외 단일가 호가
        "DK3": AFTER_MARKET_TICK_FIELDS,              # 코스닥 시간외 단일가 체결
        "VI_": STOCK_VI_ON_OFF_FIELDS,                # 주식 VI 발동해제
        "K1_": BROKER_INFO_FIELDS,                    # 코스피 거래원
        "OK_": BROKER_INFO_FIELDS,                    # 코스닥 거래원
"""

class Collecter:
    def __init__(self, gubun, qlist, writer_qlist, windowQ):
        self.gubun = gubun
        self.qlist = qlist
        self.writer_qlist = writer_qlist
        self.gubun_name = gubun.split('_')[0]
        self.gubun_proc = gubun.split('_')[1]
        self.queue = self.qlist[int(self.gubun_proc)]
        self.windowQ = windowQ

        self.dict_set = DICT_SET
        self.dict_df = {}
        self.time_save = now()

        massage = f'시스템 명령 실행 알림 - 콜렉터 시작 {self.gubun}'
        self.windowQ.put([ui_num['S로그텍스트'], massage])
        print(massage)

        self.start()

    def start(self):
        while True:
            tick = self.queue.get()
            type, data = tick
            # print(type)
            if type in ['H1_', 'HA']: # 주식 호가 정보
                code = data['shcode']
                systemtime = data['system_time']
                columns  = list(data.keys())
                data = list(data.values())

                if code not in self.dict_df.keys():
                    self.dict_df[code] = pd.DataFrame([data], columns=columns, index=[systemtime])
                else:
                    self.dict_df[code].at[systemtime] = data
            else: pass

            if now() > self.time_save:
                self.writer_qlist[0].put([self.gubun, self.dict_df])
                self.dict_df = {}
                self.time_save = timedelta_sec(int(self.dict_set['저장주기']))

        






