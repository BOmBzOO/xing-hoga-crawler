import sqlite3
from utility.setting import ui_num, DB_STOCK_TICK, DB_STOCK_HOGA, DB_FUTURE_TICK, DB_FUTURE_HOGA, DB_STOCK_BROKER, DB_STOCK_VI

class Saver:
    def __init__(self, gubun, writer_qlist, windowQ):
        self.gubun = gubun
        self.gubun_name = gubun.split('_')[0]
        self.gubun_proc = gubun.split('_')[1]
        self.writer_qlist = writer_qlist
        self.queue = self.writer_qlist[int(self.gubun_proc)]
        self.windowQ = windowQ

        self.con = sqlite3.connect(DB_STOCK_HOGA)
        self.cur = self.con.cursor()
        self.cur.execute('pragma journal_mode=WAL')
        self.cur.execute('pragma synchronous=normal')
        self.cur.execute('pragma temp_store=memory')

        massage = f'시스템 명령 실행 알림 - 세이버 시작 {self.gubun}'
        self.windowQ.put([ui_num['S로그텍스트'], massage])
        print(massage)

        # print(f'[ Saver Started ] {self.gubun}')
        
        self.Start()

    def __del__(self):
        self.con.close()

    def Start(self):
        while True:
            if self.queue.qsize() > 0:
                query = self.queue.get()

                # 주식 호가데이터 처리
                try:
                    for code in list(query[1].keys()):
                        query[1][code].to_sql(code, self.con, if_exists='append', chunksize=10000, method='multi')
                    massage = f'시스템 명령 실행 알림 - 데이터 저장 완료 [ {query[0]} ]'
                    self.windowQ.put([ui_num['S단순텍스트'], massage])
                    print(massage)
                except Exception as e:
                    massage = f'시스템 명령 오류 알림 - 데이터 저장 완료 {e}'
                    self.windowQ.put([ui_num['S단순텍스트'], massage])
                    print(massage)

    def data_to_db(self, query):
        try:
            for code in list(query[1].keys()):
                query[1][code].to_sql(code, self.con, if_exists='append', chunksize=10000, method='multi')
            massage = f'시스템 명령 실행 알림 - 데이터 저장 완료 [ {query[0]} ]'
            self.windowQ.put([ui_num['S단순텍스트'], massage])
            print(massage)
        except Exception as e:
            massage = f'시스템 명령 오류 알림 - 데이터 저장 완료 {e}'
            self.windowQ.put([ui_num['S단순텍스트'], massage])
            print(massage)
