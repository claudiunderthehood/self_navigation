import sys
import os
import time
import getopt
from threading import Thread
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QCoreApplication
from server import Server
from server_ui import Ui_server_ui

class ServerWindow(QMainWindow, Ui_server_ui):
    def __init__(self):
        self.use_ui = True
        self.start_tcp = False
        self.TCP_Server = Server()
        self.parse_options()
        
        if self.use_ui:
            self.app = QApplication(sys.argv)
            super().__init__()
            self.setupUi(self)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setMouseTracking(True)
            self.Button_Server.setText("On")
            self.on_toggle_server()
            self.Button_Server.clicked.connect(self.on_toggle_server)
            self.pushButton_Close.clicked.connect(self.close)
            self.pushButton_Min.clicked.connect(self.showMinimized)
        
        if self.start_tcp:
            self.start_server_threads()
            if self.use_ui:
                self.label.setText("Server On")
                self.Button_Server.setText("Off")
    
    def parse_options(self):
        opts, _ = getopt.getopt(sys.argv[1:], "tn")
        for opt, _ in opts:
            if opt == "-t":
                print("Opening TCP Server")
                self.start_tcp = True
            elif opt == "-n":
                self.use_ui = False
    
    def start_server_threads(self):
        self.TCP_Server.StartTcpServer()
        self.ReadData = Thread(target=self.TCP_Server.readdata)
        self.SendVideo = Thread(target=self.TCP_Server.sendvideo)
        self.PowerThread = Thread(target=self.TCP_Server.Power)
        
        self.SendVideo.start()
        self.ReadData.start()
        self.PowerThread.start()
    
    def stop_server_threads(self):
        for thread in [self.ReadData, self.SendVideo, self.PowerThread]:
            if thread.is_alive():
                thread.join()
        self.TCP_Server.StopTcpServer()
    
    def close(self):
        try:
            self.stop_server_threads()
            self.TCP_Server.server_socket.shutdown(2)
            self.TCP_Server.server_socket1.shutdown(2)
        except Exception:
            pass
        print("Closing TCP Server")
        if self.use_ui:
            QCoreApplication.instance().quit()
        os._exit(0)
    
    def on_toggle_server(self):
        if self.label.text() == "Server Off":
            self.label.setText("Server On")
            self.Button_Server.setText("Off")
            self.TCP_Server.tcp_Flag = True
            print("Starting TCP Server")
            self.start_server_threads()
        else:
            self.label.setText("Server Off")
            self.Button_Server.setText("On")
            self.TCP_Server.tcp_Flag = False
            print("Stopping TCP Server")
            self.stop_server_threads()
    
if __name__ == '__main__':
    try:
        server_ui = ServerWindow()
        if server_ui.use_ui:
            server_ui.show()
            sys.exit(server_ui.app.exec_())
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        server_ui.close()