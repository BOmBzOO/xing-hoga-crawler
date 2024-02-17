import sys
import psutil
import logging
import pyqtgraph as pg
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from multiprocessing import Process, get_context
from receiver import Receiver
from collector import Collecter
from savedata import Saver
from utility.setui import *
from utility.setting import *
from utility.utility import now, strf_time, timedelta_sec, float2str1p6

class Writer(QtCore.QThread):
    data1 = QtCore.pyqtSignal(list)
    # data2 = QtCore.pyqtSignal(list)
    # data3 = QtCore.pyqtSignal(list)
    # data4 = QtCore.pyqtSignal(list)
    # data5 = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            data = windowQ.get()
            if data[0] <= 10:
                self.data1.emit(data)

class COLLECT_DATA(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.log1 = logging.getLogger('Stock')
        self.log1.setLevel(logging.INFO)
        filehandler = logging.FileHandler(filename=f"{SYSTEM_PATH}/log/S{strf_time('%Y%m%d')}.txt", encoding='utf-8')
        self.log1.addHandler(filehandler)

        SetUI(self)

        self.showQsize = False
        self.time_queue_print = now()

        self.qtimer1 = QtCore.QTimer()
        self.qtimer1.setInterval(1000)
        self.qtimer1.timeout.connect(self.print_qsize)
        self.qtimer1.start()

        self.writer = Writer()
        self.writer.data1.connect(self.UpdateTexedit)
        self.writer.start()

    def print_qsize(self):
        # queue_info = f'코스피 틱  '
        queue_info = str()
        for idx, q in enumerate(kospi_qlist):
            if idx == len(kospi_qlist)-1:
                queue_info += f'{idx}:{q.qsize():<5} | '
            else:
                queue_info += f'{idx}:{q.qsize():<5} '
        # queue_info += f'코스닥 틱  '
        for idx, q in enumerate(kosdaq_qlist):
            if idx == len(kosdaq_qlist)-1:
                queue_info += f'{idx}:{q.qsize():<5} | '
            else:
                queue_info += f'{idx}:{q.qsize():<5} '
        # queue_info += f'저장  '
        for idx, q in enumerate(writer_qlist):
            if idx == len(writer_qlist)-1:
                queue_info += f'{idx}:{q.qsize():<5}'
            else:
                queue_info += f'{idx}:{q.qsize():<5}'
        windowQ.put([ui_num['S단순텍스트'], queue_info])
        print(queue_info)    
        self.UpdateWindowTitle()

        if int(strf_time('%H%M%S')) >= 170000:
            for proc in processes:
                proc.kill()
            if self.writer.isRunning():
                self.writer.terminate()
            if self.qtimer1.isActive():
                self.qtimer1.stop()
            sys.exit(0)

    def UpdateWindowTitle(self):
        if self.showQsize:
            kospiQ_size = 0
            for q in kospi_qlist: kospiQ_size =+ q.qsize()
            kosdaqQ_size = 0
            for q in kosdaq_qlist: kosdaqQ_size += q.qsize()

            text = f'ORDERBOOK Crawler - Qsize : 코스피 [{kospiQ_size}] | 코스닥 [{kosdaqQ_size}]'
            self.setWindowTitle(text)
        elif self.windowTitle() != 'ORDERBOOK Crawler':
            self.setWindowTitle('ORDERBOOK Crawler')

    def ShowQsize(self):
        self.showQsize = True if not self.showQsize else False

    def UpdateTexedit(self, data):
        text = f'[{now()}]  {data[1]}'
        if data[0] == ui_num['S로그텍스트']:
            self.st_textEdit.append(text)
            self.log1.info(text)
        elif data[0] == ui_num['S단순텍스트']:
            self.sc_textEdit.append(text)

    # noinspection PyArgumentList
    def closeEvent(self, a):
        buttonReply = QtWidgets.QMessageBox.question(
            self, "프로그램 종료", "호가 프로그램을 종료합니다.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            for proc in processes:
                proc.kill()
            if self.qtimer1.isActive():
                self.qtimer1.stop()
            if self.writer.isRunning():
                self.writer.terminate()
            a.accept()
        else:
            a.ignore()

if __name__ == "__main__":

    proc_number = {
        'kospi' : 10,
        'kosdaq' : 2,
        'writer' : 1
    }
    ctx = get_context("spawn")
    kospi_qlist=[ctx.Queue() for _ in range(proc_number['kospi'])]
    kosdaq_qlist=[ctx.Queue() for _ in range(proc_number['kosdaq'])]
    writer_qlist=[ctx.Queue() for _ in range(proc_number['writer'])]
    windowQ = ctx.Queue()

    receiver_proc = []
    receiver_p = Process(target=Receiver, args=(kospi_qlist, kosdaq_qlist, windowQ,))
    receiver_proc.append(receiver_p)

    collector_kospi_proc=[]
    for idx, queue in enumerate(kospi_qlist):
        kospi_p = Process(target=Collecter, args=(f'코스피_{idx}', kospi_qlist, writer_qlist, windowQ,))
        collector_kospi_proc.append(kospi_p)

    collector_kosdaq_proc=[]
    for idx, queue in enumerate(kosdaq_qlist):
        kosdaq_p = Process(target=Collecter, args=(f'코스닥_{idx}', kosdaq_qlist, writer_qlist, windowQ,))
        collector_kosdaq_proc.append(kosdaq_p)
    
    writer_proc=[]
    for idx, queue in enumerate(writer_qlist):
        writer_p = Process(target=Saver, args=(f'저장_{idx}', writer_qlist, windowQ,))
        writer_proc.append(writer_p)
    
    processes = receiver_proc + collector_kospi_proc + collector_kosdaq_proc + writer_proc

    for proc in processes:
        proc.start()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(ProxyStyle())
    app.setStyle('fusion')
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, color_bg_bc)
    palette.setColor(QtGui.QPalette.Background, color_bg_bc)
    palette.setColor(QtGui.QPalette.WindowText, color_fg_bc)
    palette.setColor(QtGui.QPalette.Base, color_bg_bc)
    palette.setColor(QtGui.QPalette.AlternateBase, color_bg_dk)
    palette.setColor(QtGui.QPalette.Text, color_fg_bc)
    palette.setColor(QtGui.QPalette.Button, color_bg_bc)
    palette.setColor(QtGui.QPalette.ButtonText, color_fg_bc)
    palette.setColor(QtGui.QPalette.Link, color_fg_bk)
    palette.setColor(QtGui.QPalette.Highlight, color_fg_hl)
    palette.setColor(QtGui.QPalette.HighlightedText, color_bg_bk)
    app.setPalette(palette)
    window = COLLECT_DATA()
    window.show()
    app.exec_()





