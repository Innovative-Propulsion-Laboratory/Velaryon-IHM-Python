"""
Human-Machine Interface for 1kN rocket engine project

Creator : Mehdi Delouane

Creation 28/07/2024:
    -   Main Window + tabs + program closing button + IPL logo
    -   PIDs
    -   SV control + reference table
    -   Selection of SV to control + update table (Options tab)
    -   Worker (writing in two csv depending of "frequency")
    -   IRT plot using PyQt5 + choose curves to display + choice of the x-axis length
    -   Selection of the graph to display (Options tab)
    -   "Loading window" with Arrax logo and fake download bar
    -   Sensor values displayed on the PIDs + update sensor(Options)

Update 03/08/2024: 
    -   Date and time + chronometer since the launch of the HMI
    -   Minesweeper
    -   Pressure control 
    -   Actuator control + central angle computation
    -   Sequence definition + right click on graph for more options like export graph
    -   TVC selection

Update 04/08/2024:
    -   Launch test + time since launch
    -   Emergency
    -   Warning if actuators lead to high central angle

Update 07/08/2024:
    -   Fix graph issues + removing of unecessary
    -   Fix some names and displays + display of valve name for seQuence chronograph (will change To match the original names)
    -   Specific Csv based on date
    -   Actuator button to send the values

Note: ExcePt for the valves, nothing was tested with a real MC board communication

New uPdate IncomiNg :
    -   MC board Communication using byte arrays + errOr Management
    -   Update of the length-central angle relatIon relation from DMUK data
    -   CommeNts
    -   Options (solenoid valves/actuator voltaGes)

Ideas :
    -   Cooldown before ingition (MC board or using sequence)
"""


from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import *
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import sys
import functools
from functools import partial
from socket import *
import csv
import numpy as np
import time 
import threading
import pandas as pd
import random
import os
from datetime import datetime

global nbr_SV_engine
global nbr_SV_cooling
global nbr_sensor_engine
global nbr_sensor_cooling
global address
global board_connection
global data_csv
global data_1kHz_csv
global phase
global angle_central_limit
global dated_csv

nbr_SV_engine = 13
nbr_SV_cooling = 6
nbr_sensor_engine = 12
nbr_sensor_cooling = 8
address=('192.168.0.149',12345)
board_connection = 0
dated_csv=0
data_csv='data.csv'
data_1kHz_csv='data_1kHz.csv'
phase=0
angle_central_limit=12

if dated_csv==1:
    timestamp = datetime.now().strftime("%H_%M_%S")
    data_csv = f"data_{timestamp}.csv"
    data_1kHz_csv = f"data_1kHz_{timestamp}.csv"
    
class Main(object):
    def setupUi(self, MainWindow):
        self.bits="101000110000010110"
        self.client_socket = socket(AF_INET, SOCK_DGRAM)
        self.client_socket.settimeout(1)
        self.client_socket.sendto(bytes(self.bits, 'utf-8'), address)

        MainWindow.resize(1922, 1237)
        self.centralwidget = QWidget(MainWindow)
        _translate = QCoreApplication.translate

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)
        QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setWindowFlags(MainWindow.windowFlags() & ~Qt.WindowCloseButtonHint)
        MainWindow.setStyleSheet("background-color: #F3F3F3")
        
        self.tab_widget = QTabWidget(self.centralwidget)
        self.tab_widget.setGeometry(QRect(0, 0, 2000, 1080))
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                height: 40px;
                width: 150px;
            }
        """)

        self.tabs = [QWidget() for _ in range(5)]
        self.tab_name=["Engine cycle","Cooling cycle","Test","Plot","Options"]   
        for tab,name in zip(self.tabs,self.tab_name)   :  
            self.tab_widget.addTab(tab, _translate("MainWindow", name))
        self.tab_widget.setStyleSheet("""QTabWidget::pane { border: 1px solid #000000; }
    QTabBar::tab {
        background-color: #bcbaba; color: black; height: 40px; width: 150px; font-weight: bold;
        border: 1px solid #000000;
    }
    QTabBar::tab:hover { background-color: #a8a8a8; }
    QTabBar::tab:selected { background-color: #d4d4d4; }""")
        # Set the height and width of the tabs programmatically
        self.tab_widget.tabBar().setStyleSheet("QTabBar::tab { height: 60px; width: 250px; }")

        self.pressure_labels=[]
        

        self.background_engine = QLabel(self.tabs[0])
        self.background_engine.setGeometry(QRect(-20, 50, 2100, 900))
        self.background_engine.setPixmap(QPixmap("Arrax_engine.png"))





        self.SV_frame_engine = [QFrame(self.tabs[0]) for _ in range(nbr_SV_engine)]
        self.SV_frame_engine_dim=[(990-120, 700-20, 111, 91),(1281-26, 600-40, 111, 91),(1281-26, 740, 111, 91),
                            (990-120, 175, 111, 91),(1281-83, 290, 111, 91),(1281-52+86, 290, 111, 91),

                            (1281-26, 110, 111, 91),
                            (140, 330, 111, 91),(390, 290, 111, 91),(635, 285,  111, 91),
                            (635, 550, 111, 91),(1520+40, 260-35, 111, 91),(1520+40, 642-20, 111, 91)]
        
        for frame,dim in zip(self.SV_frame_engine,self.SV_frame_engine_dim):
            frame.setStyleSheet("""QFrame, QLabel, QToolTip {
            background-color: rgb(230, 230, 230);
            border: 3px solid grey;
            border-radius: 10px;
            padding: 2px;
            }""")  
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setFrameShadow(QFrame.Raised)
            x,y,h,w=dim
            frame.setGeometry(QRect(x,y,h,w))
            frame.raise_()

        self.SV_frame_engine_status=[QLabel(self.tabs[0]) for _ in range(nbr_SV_engine)] 
        self.SV_frame_engine_label=[QLabel(self.tabs[0]) for _ in range(nbr_SV_engine)]  
        self.SV_button_ouvert_engine=[QPushButton(self.tabs[0]) for _ in range(nbr_SV_engine)] 
        self.SV_button_ferme_engine=[QPushButton(self.tabs[0]) for _ in range(nbr_SV_engine)] 
        
        self.SV_frame_engine_status_dims=[(1009-120, 710-20, 111, 16),(1300-26, 610-40, 111, 16),(1300-26, 750, 111, 16),
                                    (1009-120, 185, 111, 16),(1281-83+19, 300, 111, 16),(1281-52+86+19, 300, 111, 16),

                                    (1281-26+19, 120, 111, 16),
                                    (140-26+19+26, 340, 111, 16),(390-26+19+26, 300, 111, 16),(635-26+19+26, 295,  111, 16),
                                    (635-26+19+26, 560, 111, 16),(1539+40, 270-35, 111, 16),(1539+40, 652-20, 111, 16)]
        self.SV_frame_engine_label_dim=[(1029-120, 730-20, 55, 16),(1320-26, 630-40, 55, 16),(1320-26, 770, 55, 16),
                                    (1029-120, 205, 55, 16),(1281+20-83+19, 320, 55, 16),(1281-52+86+19+20, 320, 55, 16),

                                    (1281-26+20+19, 140, 55, 16),
                                    (140-26+20+19+26, 360, 55, 16),(390-26+20+19+26, 320, 55, 16),(635-26+20+19+26, 315,  55, 16),
                                    (635-26+20+19+26, 580, 55, 16),(1559+40, 290-35, 55, 16),(1559+40, 672-20, 55, 16)]    
        self.SV_button_ouvert_engine_dim=[(1000-120, 750-20,  41, 28),(1291-26, 650-40,  41, 28),(1291-26, 790,  41, 28),
                                    (1000-120, 225,  41, 28),(1281-9-83+19, 340,  41, 28),(1281-52+86+19-9, 340,  41, 28),

                                    (1281-26+19-9, 160,  41, 28),
                                    (140-26+19-9+26, 380,  41, 28),(390-26+19-9+26, 340,  41, 28),(635-26+19-9+26, 335,  41, 28),
                                    (635-26+19-9+26, 600,  41, 28),(1530+40, 310-35,  41, 28),(1530+40, 692-20,  41, 28)]         
        self.SV_button_ferme_engine_dim=[(1046-120, 750-20,  48, 28),(1337-26, 650-40,  48, 28),(1337-26, 790,  48, 28),
                                    (1046-120, 225,  48, 28),(1281-83-9+46+19, 340,  48, 28),(1281-52+86+19-9+46, 340,  48, 28),

                                    (1281-26+19+46-9, 160,  48, 28),
                                    (140-26+19+46-9+26, 380,  48, 28),(390-26+19+46-9+26, 340,  48, 28),(635-26+19+46-9+26, 335,  48, 28),
                                    (635-26+19+46-9+26, 600,  48, 28),(1576+40, 310-35,  48, 28),(1576+40, 692-20,  48, 28)]
        self.names_engine_valve=['SV11','SV12','SV13',
                    'SV21','SV22','SV23',
                    'SV24','SV31','SV32',
                    'SV33','SV34','SV35','SV36']
                    
        element=zip(self.SV_frame_engine_status,self.SV_frame_engine_label,self.SV_button_ouvert_engine,self.SV_button_ferme_engine,self.SV_frame_engine_status_dims,self.SV_frame_engine_label_dim,self.SV_button_ouvert_engine_dim,self.SV_button_ferme_engine_dim,self.names_engine_valve)
        
        for i,(widget,label,ouvert,ferme,dim_status,dim_label,dim_ouvert,dim_ferme,name) in enumerate(element):
            x,y,h,w=dim_status
            widget.setGeometry(QRect(x,y,h,w))
            x,y,h,w=dim_label
            label.setGeometry(QRect(x,y,h,w))
            x,y,h,w=dim_ouvert
            ouvert.setGeometry(QRect(x,y,h,w))
            x,y,h,w=dim_ferme
            ferme.setGeometry(QRect(x,y,h,w))

            font = QFont("Arial", 8, QFont.Bold)
            widget.setFont(font)
            label.setFont(font)
            font = QFont("Arial", 7, QFont.Bold)
            ouvert.setFont(font)
            ferme.setFont(font)

            if i in [0,2,6,7]:
                status_="Open"
                color=Qt.darkGreen
            else:
                status_="Closed"
                color=Qt.red

            widget.setText(_translate("MainWindow", "<u>"+name+" status:</u>"))
            label.setText(_translate("MainWindow", status_))
            color_effect = QGraphicsColorizeEffect()
            color_effect.setColor(color)
            label.setGraphicsEffect(color_effect)
            widget.adjustSize() 
            label.adjustSize()

            ouvert.setText(_translate("MainWindow", "Open"))
            ouvert.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #ADADAD;
                border: 2px rgb(255,200,200);
            }
            """)
            ferme.setText(_translate("MainWindow", "Close"))
            ferme.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #ADADAD;
                border: 2px rgb(255,200,200);
            }
            """)
            
            widget.raise_()
            label.raise_()
            ouvert.raise_()
            ferme.raise_() 

        self.SV_status_table_engine = QTableWidget(self.tabs[0])
        self.SV_status_table_engine.setRowCount(len(self.names_engine_valve))
        self.SV_status_table_engine.setColumnCount(2)
        self.SV_status_table_engine.setHorizontalHeaderLabels(['Name', 'Status'])

        self.SV_status_table_engine.verticalHeader().setVisible(False)
        self.SV_status_table_engine.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.SV_status_table_engine.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table_status_labels_engine = []

        for idx, (name, label,ouvert,ferme) in enumerate(zip(self.names_engine_valve, self.SV_frame_engine_status,self.SV_button_ouvert_engine,self.SV_button_ferme_engine)):
            if idx in [0, 2, 6, 7]:
                status_text = "Open"
                color = Qt.darkGreen
            else:
                status_text = "Closed"
                color = Qt.red

            status_label = QLabel(status_text)
            status_label.setAlignment(Qt.AlignCenter)
            color_effect = QGraphicsColorizeEffect()
            color_effect.setColor(color)
            status_label.setGraphicsEffect(color_effect)
            font = QFont("Arial", 8, QFont.Bold)
            status_label.setFont(font)
            
            self.table_status_labels_engine.append(status_label)
            name=QTableWidgetItem(name)
            name.setFont(font)
            self.SV_status_table_engine.setItem(idx, 0, name)
            self.SV_status_table_engine.setCellWidget(idx, 1, status_label)
            ouvert.clicked.connect(functools.partial(self.open_valve, idx, self.SV_frame_engine_label[idx]))
            ferme.clicked.connect(functools.partial(self.close_valve, idx, self.SV_frame_engine_label[idx]))

        self.SV_status_table_engine.resizeColumnsToContents()
        self.SV_status_table_engine.resizeRowsToContents()

        table_width = self.SV_status_table_engine.verticalHeader().width() + self.SV_status_table_engine.horizontalHeader().length() + self.SV_status_table_engine.frameWidth() * 2
        table_height = self.SV_status_table_engine.horizontalHeader().height() + self.SV_status_table_engine.verticalHeader().length() + self.SV_status_table_engine.frameWidth() * 2

        self.SV_status_table_engine.setGeometry(QRect(290, 580, table_width, table_height))
        self.SV_status_table_engine.raise_()
        
        self.sensors_engine = [QLabel(self.tabs[0]) for _ in range(nbr_sensor_engine)]
        self.dim_sensors_engine=[(685, 708, 70,21),(1550, 557, 70,21),(685, 210, 70,21),
                        (1550, 367, 70,21),(180, 222, 70,21),(1640, 375, 70,21),
                        (1718, 375, 70,21),(1435, 567, 70,21),(1647, 567, 70,21),
                        (1725, 567 , 70,21),(1053, 557, 70,21),(1053, 365 , 70,21)]
        for sensor,dim in zip(self.sensors_engine,self.dim_sensors_engine):
            x,y,h,w=dim
            sensor.setGeometry(QRect(x,y,h,w))
            sensor.raise_()
        
        self.pressure_engine_LOX=QLabel(self.tabs[0])
        self.pressure_engine_LOX.setGeometry(QRect(785, 415, 65, 25))
        self.pressure_labels.append(self.pressure_engine_LOX)
        
        self.pressure_engine_CH4=QLabel(self.tabs[0])
        self.pressure_engine_CH4.setGeometry(QRect(785, 500, 65, 25))
        self.pressure_labels.append(self.pressure_engine_CH4)
    

        self.background_cooling = QLabel(self.tabs[1])
        self.background_cooling.setGeometry(QRect(20, 70, 2100, 900))
        self.background_cooling.setPixmap(QPixmap("Arrax_cooling.png"))

        self.SV_frame_cooling = [QFrame(self.tabs[1]) for _ in range(nbr_SV_cooling)]
        self.SV_frame_cooling_dim=[(405, 290, 111, 91),(612, 600, 111, 91),(612, 305, 111, 91),
                                    (990-35, 700, 111, 91),(990-35, 205, 111, 91),(1180-19, 352-5, 111, 91)]
        
        for frame,dim in zip(self.SV_frame_cooling,self.SV_frame_cooling_dim):
            frame.setStyleSheet("""QFrame, QLabel, QToolTip {
            background-color: rgb(230, 230, 230);
            border: 3px solid grey;
            border-radius: 10px;
            padding: 2px;
            }""")  
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setFrameShadow(QFrame.Raised)
            x,y,h,w=dim
            frame.setGeometry(QRect(x,y,h,w))
            frame.raise_()

        self.SV_frame_cooling_status=[QLabel(self.tabs[1]) for _ in range(nbr_SV_cooling)] 
        self.SV_frame_cooling_label=[QLabel(self.tabs[1]) for _ in range(nbr_SV_cooling)]  
        self.SV_button_ouvert_cooling=[QPushButton(self.tabs[1]) for _ in range(nbr_SV_cooling)] 
        self.SV_button_ferme_cooling=[QPushButton(self.tabs[1]) for _ in range(nbr_SV_cooling)] 
        
        self.SV_frame_cooling_status_dims=[(395+19+10, 300, 111, 16),(631, 610, 111, 16),(631, 315, 111, 16),
                                            (1009-35, 710, 111, 16),(1009-35, 215, 111, 16),(1199-19, 362-5, 111, 16)]
        self.SV_frame_cooling_label_dim=[(395+39+10, 320, 55, 16),(651, 630, 55, 16),(651, 335, 55, 16),
                                            (1029-35, 730, 55, 16),(1029-35, 235, 55, 16),(1219-19, 382-5, 55, 16)]    
        self.SV_button_ouvert_cooling_dim=[(395+10+10, 340,  41, 28),(622, 650,  41, 28),(622, 355,  41, 28),
                                            (1000-35, 750,  41, 28),(1000-35, 255,  41, 28),(1190-19, 402-5,  41, 28)]         
        self.SV_button_ferme_cooling_dim=[(395+56+10, 340,  48, 28),(668, 650,  48, 28),(668, 355,  48, 28),
                                            (1046-35, 750,  48, 28),(1046-35, 255,  48, 28),(1236-19, 402-5,  48, 28)]
        self.names_cooling_valve=['SV51','SV52','SV53',
                            'SV61','SV62','SV63']
        
        element=zip(self.SV_frame_cooling_status,self.SV_frame_cooling_label,self.SV_button_ouvert_cooling,self.SV_button_ferme_cooling,self.SV_frame_cooling_status_dims,self.SV_frame_cooling_label_dim,self.SV_button_ouvert_cooling_dim,self.SV_button_ferme_cooling_dim,self.names_cooling_valve)
        
        for i,(widget,label,ouvert,ferme,dim_status,dim_label,dim_ouvert,dim_ferme,name) in enumerate(element):
            x,y,h,w=dim_status
            widget.setGeometry(QRect(x,y,h,w))
            x,y,h,w=dim_label
            label.setGeometry(QRect(x,y,h,w))
            x,y,h,w=dim_ouvert
            ouvert.setGeometry(QRect(x,y,h,w))
            x,y,h,w=dim_ferme
            ferme.setGeometry(QRect(x,y,h,w))

            font = QFont("Arial", 8, QFont.Bold)
            widget.setFont(font)
            label.setFont(font)
            font = QFont("Arial", 7, QFont.Bold)
            ouvert.setFont(font)
            ferme.setFont(font)

            if i in [1,3,4]:
                status_="Open"
                color=Qt.darkGreen
            else:
                status_="Closed"
                color=Qt.red

            widget.setText(_translate("MainWindow", "<u>"+name+" status:</u>"))
            label.setText(_translate("MainWindow", status_))
            color_effect = QGraphicsColorizeEffect()
            color_effect.setColor(color)
            label.setGraphicsEffect(color_effect)
            widget.adjustSize() 
            label.adjustSize()

            ouvert.setText(_translate("MainWindow", "Open"))
            ouvert.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #ADADAD;
                border: 2px rgb(255,200,200);
            }
            """)
            ferme.setText(_translate("MainWindow", "Close"))
            ferme.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #ADADAD;
                border: 2px rgb(255,200,200);
            }
            """)
            
            widget.raise_()
            label.raise_()
            ouvert.raise_()
            ferme.raise_() 

        self.SV_status_table_cooling = QTableWidget(self.tabs[1])
        self.SV_status_table_cooling.setRowCount(len(self.names_cooling_valve))
        self.SV_status_table_cooling.setColumnCount(2)
        self.SV_status_table_cooling.setHorizontalHeaderLabels(['Name', 'Status'])

        self.SV_status_table_cooling.verticalHeader().setVisible(False)
        self.SV_status_table_cooling.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.SV_status_table_cooling.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table_status_labels_cooling = []

        for idx, (name, label,ouvert,ferme) in enumerate(zip(self.names_cooling_valve, self.SV_frame_cooling_status,self.SV_button_ouvert_cooling,self.SV_button_ferme_cooling)):
            if idx in [1,3,4]:
                status_text = "Open"
                color = Qt.darkGreen
            else:
                status_text = "Closed"
                color = Qt.red

            status_label = QLabel(status_text)
            status_label.setAlignment(Qt.AlignCenter)
            color_effect = QGraphicsColorizeEffect()
            color_effect.setColor(color)
            status_label.setGraphicsEffect(color_effect)
            font = QFont("Arial", 8, QFont.Bold)
            status_label.setFont(font)
            
            self.table_status_labels_cooling.append(status_label)
            name=QTableWidgetItem(name)
            name.setFont(font)
            self.SV_status_table_cooling.setItem(idx, 0, name)
            self.SV_status_table_cooling.setCellWidget(idx, 1, status_label)
            ouvert.clicked.connect(functools.partial(self.open_valve, idx+nbr_SV_engine, self.SV_frame_cooling_label[idx]))
            ferme.clicked.connect(functools.partial(self.close_valve, idx+nbr_SV_engine, self.SV_frame_cooling_label[idx]))

        self.SV_status_table_cooling.resizeColumnsToContents()
        self.SV_status_table_cooling.resizeRowsToContents()

        table_width = self.SV_status_table_cooling.verticalHeader().width() + self.SV_status_table_cooling.horizontalHeader().length() + self.SV_status_table_cooling.frameWidth() * 2
        table_height = self.SV_status_table_cooling.horizontalHeader().height() + self.SV_status_table_cooling.verticalHeader().length() + self.SV_status_table_cooling.frameWidth() * 2

        self.SV_status_table_cooling.setGeometry(QRect(290, 580, table_width, table_height))
        self.SV_status_table_cooling.raise_()

        self.sensors_cooling = [QLabel(self.tabs[1]) for _ in range(8)]
        self.dim_sensors_cooling=[(248,240,70,21),(820-28-50, 733, 70,21),(792-50, 239, 70,21),
                                    (1415, 422, 70,21),(1574, 422, 70,21),(1417, 548, 70,21),
                                    (1576, 548, 70,21),(1305, 440, 70,21)]
        for sensor,dim in zip(self.sensors_cooling,self.dim_sensors_cooling):
            x,y,h,w=dim
            sensor.setGeometry(QRect(x,y,h,w))
            sensor.raise_()
        
        self.pressure_cooling=QLabel(self.tabs[1])
        self.pressure_cooling.setGeometry(QRect(850, 485, 65, 25))
        self.pressure_labels.append(self.pressure_cooling)

        self.checkbox_frame_valve = QFrame(self.tabs[4])
        self.checkbox_frame_valve.setFrameShape(QFrame.StyledPanel)
        self.checkbox_frame_valve.setGeometry(QRect(10,50,400,400))

        self.grid_layout = QGridLayout(self.checkbox_frame_valve)
        title_label = QLabel(self.checkbox_frame_valve)
        title_label.setText(_translate("MainWindow", "Displayed valve control"))
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(title_label, 0, 1)

        engine_title = QLabel(self.checkbox_frame_valve)
        engine_title.setText(_translate("MainWindow", "Engine:"))
        font = QFont("Arial", 10, QFont.Bold)
        engine_title.setFont(font)
        engine_title.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(engine_title, 1, 0)

        for i in range(nbr_SV_engine):
            checkbox = QCheckBox(self.checkbox_frame_valve)
            checkbox.setChecked(True)
            label = QLabel(self.names_engine_valve[i])
            h_layout = QHBoxLayout()
            h_layout.addWidget(checkbox)
            h_layout.addWidget(label)
            self.grid_layout.addLayout(h_layout, i+2, 0)
            checkbox.stateChanged.connect(lambda state, idx=i: self.on_checkbox_state_changed_valve(state, idx))

        cooling_title = QLabel(self.checkbox_frame_valve)
        cooling_title.setText(_translate("MainWindow", "Cooling:"))
        font = QFont("Arial", 10, QFont.Bold)
        cooling_title.setFont(font)
        cooling_title.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(cooling_title, 1, 2)

        for i in range(nbr_SV_cooling):
            checkbox = QCheckBox(self.checkbox_frame_valve)
            checkbox.setChecked(True)
            label = QLabel(self.names_cooling_valve[i])
            h_layout = QHBoxLayout()
            h_layout.addWidget(checkbox)
            h_layout.addWidget(label)
            self.grid_layout.addLayout(h_layout, i+2, 2)
            checkbox.stateChanged.connect(lambda state, idx=i+nbr_SV_engine: self.on_checkbox_state_changed_valve(state, idx))
        
        self.checkbox_frame = QFrame(self.tabs[4])
        self.checkbox_frame.setFrameShape(QFrame.StyledPanel)
        self.checkbox_frame.setGeometry(QRect(10, 451, 400, 100))

        self.frame_layout = QVBoxLayout(self.checkbox_frame)
        self.frame_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(self.checkbox_frame)
        title_label.setText(_translate("MainWindow", "Displayed graphs"))
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(title_label)


        checkbox_layout = QHBoxLayout()
        checkbox_layout.setAlignment(Qt.AlignCenter)

        self.checkboxes = []
        checkbox_names = ["Pressure", "Temperature", "Flowrate", "Force"]

        for i in range(4):
            control_graph = QVBoxLayout()
            control_graph.setAlignment(Qt.AlignCenter)
            
            label = QLabel(checkbox_names[i], self.checkbox_frame)
            font = QFont("Arial", 8, QFont.Bold)
            label.setFont(font)
            control_graph.addWidget(label, alignment=Qt.AlignCenter)
            
            checkbox = QCheckBox(self.checkbox_frame)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_binary_value)
            self.checkboxes.append(checkbox)
            control_graph.addWidget(checkbox, alignment=Qt.AlignCenter)
            
            checkbox_layout.addLayout(control_graph)
            if i < 3:
                checkbox_layout.addSpacing(20)

        self.frame_layout.addLayout(checkbox_layout)

        self.sensors=self.sensors_engine[0:7]+self.sensors_cooling[0:5]+self.sensors_engine[7:10]+self.sensors_cooling[5:7]+self.sensors_engine[10:]+self.sensors_cooling[7:]
        
        self.checkbox_frame_sensor = QFrame(self.tabs[4])
        self.checkbox_frame_sensor.setFrameShape(QFrame.StyledPanel)
        self.checkbox_frame_sensor.setGeometry(QRect(411,50,400,400))

        self.grid_layout_sensor = QGridLayout(self.checkbox_frame_sensor)
        title_label = QLabel(self.checkbox_frame_sensor)
        title_label.setText(_translate("MainWindow", "Displayed sensor values"))
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        self.grid_layout_sensor.addWidget(title_label, 0, 1)

        engine_title = QLabel(self.checkbox_frame_sensor)
        engine_title.setText(_translate("MainWindow", "Engine:"))
        font = QFont("Arial", 10, QFont.Bold)
        engine_title.setFont(font)
        engine_title.setAlignment(Qt.AlignCenter)
        self.grid_layout_sensor.addWidget(engine_title, 1, 0)

        self.names_engine_sensor=["PS11","PS12","PS21","PS22","PS31","PS41","PS42","TS11","TS41","TS42","FM11","FM12"]
        self.names_cooling_sensor=["PS51","PS61","PS62","PS63","PS64","TS61","TS62","FM61"]

        for i in range(nbr_sensor_engine):
            checkbox = QCheckBox(self.checkbox_frame_sensor)
            checkbox.setChecked(True)
            label = QLabel(self.names_engine_sensor[i])
            h_layout = QHBoxLayout()
            h_layout.addWidget(checkbox)
            h_layout.addWidget(label)
            self.grid_layout_sensor.addLayout(h_layout, i+2, 0)
            checkbox.stateChanged.connect(lambda state, idx=i: self.on_checkbox_state_changed_sensor(state, idx))

        cooling_title = QLabel(self.checkbox_frame_sensor)
        cooling_title.setText(_translate("MainWindow", "Cooling:"))
        font = QFont("Arial", 10, QFont.Bold)
        cooling_title.setFont(font)
        cooling_title.setAlignment(Qt.AlignCenter)
        self.grid_layout_sensor.addWidget(cooling_title, 1, 2)

        for i in range(nbr_sensor_cooling):
            checkbox = QCheckBox(self.checkbox_frame_sensor)
            checkbox.setChecked(True)
            label = QLabel(self.names_cooling_sensor[i])
            h_layout = QHBoxLayout()
            h_layout.addWidget(checkbox)
            h_layout.addWidget(label)
            self.grid_layout_sensor.addLayout(h_layout, i+2, 2)
            checkbox.stateChanged.connect(lambda state, idx=i+nbr_SV_engine: self.on_checkbox_state_changed_sensor(state, idx))
        
        
        self.launch_frame = QFrame(self.tabs[2])
        self.launch_frame.setGeometry(QRect(10, 382, 851, 270))
        self.launch_frame.setFrameShape(QFrame.StyledPanel)
        self.launch_frame_layout = QVBoxLayout()

        title_label = QLabel("Launch test")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.launch_frame_layout.addWidget(title_label)
        title_label.setAlignment(Qt.AlignCenter)

        label_layout = QHBoxLayout()
        self.launch_labels = [QLabel() for _ in range(6)]
        for label in self.launch_labels:
            label_layout.addWidget(label)
        self.launch_frame_layout.addLayout(label_layout)

        self.transparent_label = QLabel()
        self.transparent_label.setFixedSize(330, 100)

        self.launch_button = QPushButton("Start test")
        self.launch_button.setFixedSize(150, 100)
        self.launch_button.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #ADADAD;
                border: 2px solid rgb(0, 0, 0);
            }
        """)
        self.launch_button.clicked.connect(self.show_confirmation_dialog)

        self.time_label = QLabel("              00:00.000")
        self.time_label.setStyleSheet("""
            font-size: 24px;       /* Larger font size */
            font-weight: bold;    /* Bold text */
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.transparent_label)
        button_layout.addWidget(self.launch_button)
        button_layout.addWidget(self.time_label)

        button_layout.setStretch(1, 1)

        self.launch_frame_layout.addLayout(button_layout)

        self.launch_frame.setLayout(self.launch_frame_layout)    

        self.timer_launch = QTimer()
        self.timer_launch.timeout.connect(self.update_elapsed_time)

        self.start_time = None

        self.actuator_frame = QFrame(self.tabs[2])
        self.actuator_frame.setFrameShape(QFrame.StyledPanel)
        self.actuator_frame.setGeometry(QRect(411, 10, 200, 371))
        self.frame_actuator_layout = QVBoxLayout(self.actuator_frame)
        self.frame_actuator_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(self.actuator_frame)
        title_label.setText(_translate("MainWindow", "Actuator control"))
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        self.frame_actuator_layout.addWidget(title_label)

        radio_layout = QHBoxLayout()
        self.radio_button_1 = QRadioButton("Length", self.actuator_frame)
        self.radio_button_2 = QRadioButton("Angle", self.actuator_frame)
        radio_layout.addWidget(self.radio_button_1)
        radio_layout.addWidget(self.radio_button_2)
        self.frame_actuator_layout.addLayout(radio_layout)

        line = QFrame(self.actuator_frame)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.frame_actuator_layout.addWidget(line)

        self.actuator_layout = QHBoxLayout()
        self.actuator_layout.setAlignment(Qt.AlignCenter)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.L_spinbox = QDoubleSpinBox(self.actuator_frame)
        self.R_spinbox = QDoubleSpinBox(self.actuator_frame)
        self.L_slider = QSlider(Qt.Vertical, self.actuator_frame)
        self.R_slider = QSlider(Qt.Vertical, self.actuator_frame)
        self.L_spinbox.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.R_spinbox.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.L_spinbox.setStyleSheet(
            """QDoubleSpinBox {
                border: 2px solid #5A5A5A;  /* Border color */
                border-radius: 5px;         /* Rounded corners */
                padding: 5px;               /* Padding inside the box */
                background: #F0F0F0;        /* Background color */
                color: #333333;             /* Text color */
                font-size: 16px;            /* Font size */
            }

            /* Style the up button */
            QDoubleSpinBox::up-button {
                width: 20px; /* Width of the up button */
                height: 15px; /* Height of the up button */
                subcontrol-origin: border;
                subcontrol-position: top right;
            }

            /* Style the down button */
            QDoubleSpinBox::down-button {
                width: 20px; /* Width of the down button */
                height: 15px; /* Height of the down button */
                subcontrol-origin: border;
                subcontrol-position: bottom right;
            }"""
        )
        self.R_spinbox.setStyleSheet(
            """QDoubleSpinBox {
                border: 2px solid #5A5A5A;  /* Border color */
                border-radius: 5px;         /* Rounded corners */
                padding: 5px;               /* Padding inside the box */
                background: #F0F0F0;        /* Background color */
                color: #333333;             /* Text color */
                font-size: 16px;            /* Font size */
            }

            /* Style the up button */
            QDoubleSpinBox::up-button {
                width: 20px; /* Width of the up button */
                height: 15px; /* Height of the up button */
                subcontrol-origin: border;
                subcontrol-position: top right;
            }

            /* Style the down button */
            QDoubleSpinBox::down-button {
                width: 20px; /* Width of the down button */
                height: 15px; /* Height of the down button */
                subcontrol-origin: border;
                subcontrol-position: bottom right;
            }"""
        )
        self.L_slider.setStyleSheet(
        """
        QSlider::groove:vertical {
            border: 1px solid #999999;
            background: #E0E0E0;
            width: 10px; /* adjust width */
            margin: 5px 5px; /* adjust margin */
        }
        QSlider::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f6f7fa, stop:1 #dadbde);
            border: 1px solid #5c5c5c;
            width: 20px; /* adjust width */
            height: 12px; /* adjust height */
            margin: -1px -5px; /* adjust margin */
            border-radius: 10px; /* adjust border radius */
        }
        """
        )
        self.R_slider.setStyleSheet(
        """
        QSlider::groove:vertical {
            border: 1px solid #999999;
            background: #E0E0E0;
            width: 10px; /* adjust width */
            margin: 5px 5px; /* adjust margin */
        }
        QSlider::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f6f7fa, stop:1 #dadbde);
            border: 1px solid #5c5c5c;
            width: 20px; /* adjust width */
            height: 12px; /* adjust height */
            margin: -1px -5px; /* adjust margin */
            border-radius: 10px; /* adjust border radius */
        }
        """
        )

        self.L_spinbox.setAlignment(Qt.AlignCenter)
        self.R_spinbox.setAlignment(Qt.AlignCenter)
        


        self.L_spinbox.setRange(0.0, 100.0)
        self.R_spinbox.setRange(0.0, 100.0)
        self.L_slider.setRange(0, 1000)
        self.R_slider.setRange(0, 1000)

        self.L_slider.setMinimumSize(50, 120)
        self.R_slider.setMinimumSize(50, 120)
        self.L_spinbox.setFixedSize(90, 30)
        self.R_spinbox.setFixedSize(90, 30)

        left_layout.addWidget(self.L_spinbox, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.L_slider, alignment=Qt.AlignCenter)

        right_layout.addWidget(self.R_spinbox, alignment=Qt.AlignCenter)
        right_layout.addWidget(self.R_slider, alignment=Qt.AlignCenter)

        self.actuator_layout.addLayout(left_layout)
        self.actuator_layout.addLayout(right_layout)

        self.frame_actuator_layout.addLayout(self.actuator_layout)
        self.sync_spinbox_slider(self.L_spinbox, self.L_slider)
        self.sync_spinbox_slider(self.R_spinbox, self.R_slider) 

        self.radio_button_1.toggled.connect(self.update_ranges)
        self.radio_button_2.toggled.connect(self.update_ranges)

        self.radio_button_1.setChecked(True)

        self.angle_central_label = QLabel("Control Panel", self.actuator_frame)
        self.angle_central_label.setText(_translate("MainWindow", "Control Panel"))
        font = QFont("Arial", 10, QFont.Bold)
        self.angle_central_label.setFont(font)
        self.angle_central_label.setAlignment(Qt.AlignCenter)

        self.frame_actuator_layout.addWidget(self. angle_central_label)

        self.frame_actuator_layout.setSpacing(10)

        self.L_slider.valueChanged.connect(self.get_slider_val)
        self.R_slider.valueChanged.connect(self.get_slider_val)
        self.L_spinbox.valueChanged.connect(self.get_slider_val)
        self.R_spinbox.valueChanged.connect(self.get_slider_val)


        self.spinbox_frame = QFrame(self.tabs[2])
        self.spinbox_frame.setFrameShape(QFrame.StyledPanel)
        self.spinbox_frame.setGeometry(QRect(10, 10, 400, 371))

        self.send_actuator_button = QPushButton(self.actuator_frame)
        self.send_actuator_button.setText(_translate("MainWindow", "Send Data"))
        self.send_actuator_button.clicked.connect(self.send_actuator_val)
        
        self.frame_actuator_layout.addWidget(self.send_actuator_button)
        self.frame_pressurisation_layout = QVBoxLayout(self.spinbox_frame)
        self.frame_pressurisation_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(self.spinbox_frame)
        title_label.setText(_translate("MainWindow", "Tank pressure control"))
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        self.frame_pressurisation_layout.addWidget(title_label)
        void = QLabel(self.spinbox_frame)
        void.setText(_translate("MainWindow", "  "))
        void.setAlignment(Qt.AlignCenter)
        self.frame_pressurisation_layout.addWidget(void)

        self.pressurisation_layout = QHBoxLayout()
        self.pressurisation_layout.setAlignment(Qt.AlignCenter)

        self.pressurisation_spinbox = []
        spinbox_names = ["LOX pressure", "ETH pressure", "H2O pressure"]
        j=0

        for i in range(3):
            control_graph = QVBoxLayout()
            control_graph.setAlignment(Qt.AlignCenter)
            
            label = QLabel(spinbox_names[i], self.spinbox_frame)
            font = QFont("Arial", 8, QFont.Bold)
            label.setFont(font)
            control_graph.addWidget(label, alignment=Qt.AlignCenter)
            
            spinbox = QDoubleSpinBox(self.spinbox_frame)
            spinbox.setFixedSize(100, 30)
            spinbox.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))  # Set the locale first
            
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    border: 2px solid #5A5A5A;  /* Border color */
                    border-radius: 5px;         /* Rounded corners */
                    padding: 5px;               /* Padding inside the box */
                    background: #F0F0F0;        /* Background color */
                    color: #333333;             /* Text color */
                    font-size: 16px;            /* Font size */
                }

                /* Style the up button */
                QDoubleSpinBox::up-button {
                    width: 20px; /* Width of the up button */
                    height: 15px; /* Height of the up button */
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                }

                /* Style the down button */
                QDoubleSpinBox::down-button {
                    width: 20px; /* Width of the down button */
                    height: 15px; /* Height of the down button */
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                }
            """)
            
            spinbox.valueChanged.connect(lambda value, idx=i: self.pressure_display(value, idx))
            
            self.pressurisation_spinbox.append(spinbox)
            control_graph.addWidget(spinbox, alignment=Qt.AlignCenter)
            spinbox.setRange(1, 20)
            spinbox.setValue(16)
            self.pressurisation_layout.addLayout(control_graph)
            if i < 2:
                self.pressurisation_layout.addSpacing(20)
            
            label = QLabel(self.spinbox_frame)
            if j==0:
                label.setStyleSheet("""QLabel {
                background-color: #1BA1E2;
                padding: 10px;
                border: 1px solid #016BAA;
                border-radius: 25px;
            }""")
            elif j==1:
                label.setStyleSheet("""QLabel {
                background-color: #E51400;
                padding: 10px;
                border: 1px solid #9F0404;
                border-radius: 25px;
                }""")
            else:
                label.setStyleSheet("""QLabel {
                background-color: #F0A30A;
                padding: 10px;
                border: 1px solid #BD7000;
                border-radius: 25px;
                }""")
                spinbox.setMinimum(1)
                spinbox.setValue(4)
                spinbox.setMaximum(10)
            label.setFixedSize(50,115)
            control_graph.addWidget(label, alignment=Qt.AlignCenter)
            j+=1
        self.frame_pressurisation_layout.addLayout(self.pressurisation_layout)
        for idx, spinbox in enumerate(self.pressurisation_spinbox):
            self.pressure_display(spinbox.value(), idx)
        
        self.sequence_frame = QFrame(self.tabs[2])
        self.sequence_frame.setFrameShape(QFrame.StyledPanel)
        self.sequence_frame.setGeometry(QRect(612, 10, 250, 100))

        self.frame_sequence_layout = QVBoxLayout(self.sequence_frame)
        self.frame_sequence_layout.setAlignment(Qt.AlignCenter)

        self.titleLabel = QLabel("Sequence control", self.sequence_frame)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        self.frame_sequence_layout.addWidget(self.titleLabel)

        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.setAlignment(Qt.AlignCenter)

        self.comboBox = QComboBox(self.sequence_frame)
        self.comboBox.setFixedSize(120, 30)
        self.comboBox.setStyleSheet("""
            QComboBox {
                border: 2px solid #000000; /* Blue border */
                border-radius: 5px; /* Rounded corners */
                padding: 5px 10px; /* Padding inside the box */
                background-color: #F0F0F0; /* Light grey background */
                color: #333; /* Dark grey text color */
            }
            QComboBox QAbstractItemView {
                border: 2px solid #000000; /* Border around the dropdown list */
                selection-background-color: #F0F0F0; /* Background color of the selected item */
                selection-color: black; /* Text color of the selected item */
                background-color: #F0F0F0; /* Background color of the dropdown list */
            }
        """)
        self.update_combobox()
        self.hbox_layout.addWidget(self.comboBox)

        self.hbox_layout.addStretch()

        self.viewButton = QPushButton("View selection", self.sequence_frame)
        self.viewButton.setFixedSize(100, 30)  # Custom size
        self.viewButton.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #ADADAD;
                border: 2px rgb(255,200,200);
            }
        """)
        self.viewButton.clicked.connect(self.view_sequence)
        self.hbox_layout.addWidget(self.viewButton)

        self.frame_sequence_layout.addLayout(self.hbox_layout)
        
        self.TVC_control_frame = QFrame( self.tabs[2])
        self.TVC_control_frame.setFrameShape(QFrame.StyledPanel)
        self.TVC_control_frame.setGeometry(QRect(612, 111, 250, 270))

        self.frame_TVC_control = QVBoxLayout(self.TVC_control_frame)
        self.frame_TVC_control.setAlignment(Qt.AlignCenter)

        self.TVC_label = QLabel("TVC control", self.TVC_control_frame)
        self.TVC_label.setAlignment(Qt.AlignCenter)
        self.TVC_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        self.frame_TVC_control.addWidget(self.TVC_label)

        self.hbox_layout_TVC = QHBoxLayout()
        self.hbox_layout_TVC.setAlignment(Qt.AlignCenter)

        self.comboBox_TVC = QComboBox(self.TVC_control_frame)
        self.comboBox_TVC.setFixedSize(120, 30)
        self.comboBox_TVC.addItems(['None', 'Square', 'Circle', 'Up-Down', 'Left-Right'])
        self.comboBox_TVC.setStyleSheet("""
            QComboBox {
                border: 2px solid #000000; /* Blue border */
                border-radius: 5px; /* Rounded corners */
                padding: 5px 10px; /* Padding inside the box */
                background-color: #F0F0F0; /* Light grey background */
                color: #333; /* Dark grey text color */
            }
            QComboBox QAbstractItemView {
                border: 2px solid #000000; /* Border around the dropdown list */
                selection-background-color: #F0F0F0; /* Background color of the selected item */
                selection-color: black; /* Text color of the selected item */
                background-color: #F0F0F0; /* Background color of the dropdown list */
            }
        """)
        self.hbox_layout_TVC.addWidget(self.comboBox_TVC)

        self.hbox_layout_TVC.addStretch()

        self.viewButton_TVC = QPushButton("View TVC shape", self.TVC_control_frame)
        self.viewButton_TVC.setFixedSize(100, 30)
        self.viewButton_TVC.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: #ADADAD;
                border: 2px rgb(255,200,200);
            }
        """)
        self.hbox_layout_TVC.addWidget(self.viewButton_TVC)

        self.frame_TVC_control.addLayout(self.hbox_layout_TVC)

        self.figure = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(220, 180)
        self.frame_TVC_control.addWidget(self.canvas)

        self.viewButton_TVC.clicked.connect(self.plotShape)
        self.shape = None

        self.emergency_frame = QFrame(self.tabs[2])
        self.emergency_frame.setGeometry(QRect(10, 653, 851, 270))
        self.emergency_frame.setFrameShape(QFrame.StyledPanel)
        self.emergency_frame_layout = QVBoxLayout()

        title_label = QLabel("Test abortion")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.emergency_frame_layout.addWidget(title_label)
        title_label.setAlignment(Qt.AlignCenter)

        self.emergency_button = QPushButton("Abort test")
        self.emergency_button.clicked.connect(self.emergency)
        self.emergency_frame_layout.addWidget(self.emergency_button, alignment=Qt.AlignCenter)
        self.emergency_button.setFixedSize(150, 150)
        self.emergency_button.setStyleSheet("""
            QPushButton {
                border: 1px rgb(255, 0, 0);
                background-color: rgb(220, 0, 0);
                border-radius: 20px;
                height: 30px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: rgb(250, 0, 0);
                border: 2px solid rgb(255, 0, 0);
            }
        """)

        
        self.invisible_label1 = QLabel(self.tabs[0])
        self.invisible_label1.setGeometry(0, 0, 2000, 1000)
        self.invisible_label1.lower()
        self.invisible_label1.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #000000;
            }
        """)

        self.invisible_label2 = QLabel(self.tabs[1])
        self.invisible_label2.setGeometry(0, 0, 2000, 1000)
        self.invisible_label2.lower()
        self.invisible_label2.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #000000;
            }
        """)
        self.invisible_label3 = QLabel(self.tabs[2])
        self.invisible_label3.setGeometry(0, 0, 2000, 750)
        self.invisible_label3.lower()
        self.invisible_label3.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #000000;
            }
        """)

        self.elpased_date_time_label=[]


        self.emergency_frame.setLayout(self.emergency_frame_layout)    




        for index, tab in enumerate(self.tabs):
            if index!=3:
                self.close_all = QPushButton(tab)
                self.close_all.setGeometry(QRect(1670, 930, 120, 40))
                self.close_all.clicked.connect(self.End_program)
                self.close_all.setStyleSheet("""
                    QPushButton {
                        border: 2px solid #B20000;
                        background-color: #FF1400;
                        border-radius: 3px;
                        height: 30px;
                    }
                    QPushButton:hover {
                        background-color: rgb(255,100,100);
                        border: 2px rgb(255,200,200);
                    }""")
                self.close_all.setText(_translate("MainWindow", "End program"))
                font = QFont("Arial", 10, QFont.Bold)
                self.close_all.setFont(font)
                self.close_all.raise_()

                self.logo = QLabel(tab)
                self.logo.setGeometry(QRect(1600, 50, 500, 100))
                self.logo.setPixmap(QPixmap("Logo_IPL.png"))
                self.logo.raise_()

                self.currentTimeLabel = QLabel(tab)
                self.elapsedTimeLabel = QLabel(tab)
                self.currentTimeLabel.setGeometry(QRect(1620, 145, 300, 50))  
                self.elapsedTimeLabel.setGeometry(QRect(1620, 175, 300, 50))   

                self.currentTimeLabel.raise_()
                self.elapsedTimeLabel.raise_()
                self.elapsedTimer = QElapsedTimer()
                self.elapsedTimer.start()
                
                self.timer_elapsedtime = QTimer()
                self.timer_elapsedtime.timeout.connect(self.Update_Elapsed_Time)
                self.timer_elapsedtime.start(1000)
                self.Update_Elapsed_Time()
                self.elpased_date_time_label.append((self.currentTimeLabel, self.elapsedTimeLabel))

                self.label = QLabel(tab)
                self.label.setStyleSheet("background-color: transparent;")
                self.label.setGeometry(1600, 50, 500, 100)
                self.label.setCursor(Qt.PointingHandCursor)
                self.label.mousePressEvent = self.on_label_click

        self.worker = Worker()
        self.worker_thread = threading.Thread(target=self.worker.write_csv_arduino)
        self.worker_thread.daemon = True    
        self.worker_thread.start()
        self.worker.update_signal.connect(self.update_displayed_data)
        
        self.update_binary_value()
        self.update_ranges()
        self.get_slider_val()
        self.plotShape()
        self.update_launch_data()

    def send_actuator_val(self):
        value_L = self.L_spinbox.value()
        value_R = self.R_spinbox.value()
        if self.radio_button_1.isChecked():
            string = "Length"
        elif self.radio_button_2.isChecked():
            string = "Angle"
        else:
            string = "Unknown"
        print(f"Values: {value_L,value_R}, String: {string}")    

    def start_timer(self):
        self.start_time = QTime.currentTime()
        self.timer_launch.start(1)

    def update_elapsed_time(self):
        if self.start_time:
            elapsed = self.start_time.msecsTo(QTime.currentTime())
            minutes = elapsed // 60000
            seconds = (elapsed % 60000) // 1000
            milliseconds = elapsed % 1000
            formatted_time = f"{minutes:02}:{seconds:02}.{milliseconds:03}"
            self.time_label.setText(f"              {formatted_time}")

    def show_confirmation_dialog(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        reply = msgBox.warning(MainWindow, 'Confirmation',
                               "Are you sure you want to launch?",
                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.start_timer()
            self.invisible_label1.raise_()
            self.invisible_label2.raise_()
            self.invisible_label3.raise_()
    
    def stop_timer(self):
        self.timer_launch.stop()

    def emergency(self):
        self.invisible_label1.lower()
        self.invisible_label2.lower()
        self.invisible_label3.lower()  
        self.stop_timer()    
  
    def update_launch_data(self):
        sequence_name = self.comboBox.currentText()
        with open(sequence_name, 'r') as file:
            lines = file.readlines()
        
        time_max=[]
        for line in lines[1:]:
            parts = line.strip().split(',')
            times = list(map(int, parts[1:]))
            time_max.append(max(times)/1000)
        launch_time=max(time_max)
        tvc_choice = self.comboBox_TVC.currentText()

        self.launch_labels[3].setText(f"Sequence: {sequence_name}")
        self.launch_labels[4].setText(f"Launch Time: {launch_time} s")
        self.launch_labels[5].setText(f"TVC Choice: {tvc_choice}")
        for lab in self.launch_labels:
            lab.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
            """)

    def plotShape(self):
        self.shape = self.comboBox_TVC.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        background_color = (236/255, 236/255, 236/255)
        self.figure.patch.set_facecolor(background_color)
        
        ax.axis('off')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        
        ax.spines['top'].set_color(background_color)
        ax.spines['right'].set_color(background_color)
        ax.spines['bottom'].set_color(background_color)
        ax.spines['left'].set_color(background_color)
        
        if self.shape == "Square":
            ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], 'g-')
        elif self.shape == "Circle":
            circle = plt.Circle((0.5, 0.5), 0.48, color='b', fill=False)
            ax.add_artist(circle)
        elif self.shape == "Up-Down":
            ax.plot([0.5, 0.5], [0, 1], 'r-')
        elif self.shape == "Left-Right":
            ax.plot([0, 1], [0.5, 0.5], 'r-')
        
        self.canvas.draw()
        self.update_launch_data()

    def update_combobox(self):
        txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
        self.comboBox.clear()
        self.comboBox.addItems(txt_files)
        if not txt_files:
            self.comboBox.addItem('No .txt files found')

    def view_sequence(self):
        filename = self.comboBox.currentText()
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        init_state_graph = lines[0].strip()
        events = {}
        time_max = []
        for line in lines[1:]:
            parts = line.strip().split(',')
            valve_name = parts[0]
            times = list(map(int, parts[1:]))
            events[valve_name] = [time / 1000 for time in times]
            time_max.append(max(times) / 1000)

        self.frame_sequence = QFrame(self.tabs[2])
        self.frame_sequence.setFrameShape(QFrame.StyledPanel)
        self.frame_sequence.setGeometry(QRect(863, 10, 720, 913))

        self.vertical_layout = QVBoxLayout(self.frame_sequence)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'State')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setTitle('Valve State Chronograph')
        self.vertical_layout.addWidget(self.plot_widget)

        for i, (valve_name, times) in enumerate(events.items()):
            state_changes = [(0, int(init_state_graph[i]))]

            for t in times:
                a, b = state_changes[-1]
                state_changes.append((t, 0 if b == 0 else 1))
                state_changes.append((t, 1 if b == 0 else 0))

            a, b = state_changes[-1]
            state_changes.append((max(time_max) + 1, b))

            state_changes = np.array(state_changes)

            state_values = state_changes[:, 1] + (i * 2)
            time_values = state_changes[:, 0]

            self.plot_widget.plot(time_values, state_values, pen=pg.mkPen(width=2))
            name_y_position = 1 + i * 2

            # Add text label for each curve
            text = pg.TextItem(f"SV{i}", anchor=(0, 0))
            text.setPos(max(time_max)+1.2, name_y_position)
            self.plot_widget.addItem(text)

        self.plot_widget.setXRange(0, max(time_max) + 2.5, padding=0)
        self.frame_sequence.setLayout(self.vertical_layout)
        self.frame_sequence.show()
        self.update_launch_data()

    def update_ranges(self):
        if self.radio_button_1.isChecked():
            self.L_spinbox.setRange(-25.0, 25.0)
            self.R_spinbox.setRange(-25.0, 25.0)
            self.L_slider.setRange(-250, 250)
            self.R_slider.setRange(-250, 250)
            self.L_spinbox.setValue(0.0)
            self.R_spinbox.setValue(0.0)
        else:
            self.L_spinbox.setRange(-12.0, 12.0)
            self.R_spinbox.setRange(-12.0, 12.0)
            self.L_slider.setRange(-120, 120)
            self.R_slider.setRange(-120, 120)
            self.L_spinbox.setValue(0.0)
            self.R_spinbox.setValue(0.0)

    def sync_spinbox_slider(self,spinbox, slider):
        def on_spinbox_value_changed(value):
            slider.setValue(int(value * 10))
        def on_slider_value_changed(value):
            spinbox.setValue(value / 10.0)
        spinbox.valueChanged.connect(on_spinbox_value_changed)
        slider.valueChanged.connect(on_slider_value_changed)

    def get_slider_val(self):
        ####################################################################################### Find relation using table (make new one probably for new position of actuator)
        x = self.L_spinbox.value()
        y = self.R_spinbox.value()

        if self.radio_button_1.isChecked():
            angle1 = -3.0969022073278854e-05-3.51267954e-01*x+3.51268192e-01*y+3.36528848e-06*x*y-3.69500756e-08*x**2-3.20762748e-06*y**2
            angle2 = -0.009798940960050781-3.57194001e-01*x-0.38888253*y-1.31003446e-03*x*y+2.36429555e-05*x**2-1.31060395e-03*y**2

            
            angle_total=np.arccos(np.cos(np.deg2rad(angle1))*np.cos(np.deg2rad(angle2)))
            if np.rad2deg(angle_total)>angle_central_limit:
                self.angle_central_label.setText(f"⚠ Central angle too high : {round(np.rad2deg(angle_total),1)}")
                self.angle_central_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px;")
            else:
                self.angle_central_label.setText(f"Central angle: {round(np.rad2deg(angle_total),1)}")
                self.angle_central_label.setStyleSheet("color: black; font-weight: bold; font-size: 14px;")
        else:
            angle_total=np.arccos(np.cos(np.deg2rad(x))*np.cos(np.deg2rad(y)))
            if np.rad2deg(angle_total)>angle_central_limit:
                self.angle_central_label.setText(f"⚠ Central angle too high : {round(np.rad2deg(angle_total),1)}")
                self.angle_central_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px;")
            else:
                self.angle_central_label.setText(f"Central angle: {round(np.rad2deg(angle_total),1)}")
                self.angle_central_label.setStyleSheet("color: black; font-weight: bold; font-size: 14px;")
                
    def pressure_display(self, value, index):
        self.pressure_labels[index].setText(f"{value} bar")
        font = QFont("Arial", 9, QFont.Bold)
        self.pressure_labels[index].setFont(font)
        self.pressure_labels[index].setStyleSheet("""
            QLabel {
                background-color: transparent;  /* Transparent background */
                color: #000000;  /* Optional: Set text color if needed */
            }
        """)
        name_map = {0: "ETH", 1: "LOX", 2: "H2O"}
        name = name_map.get(index, "Unknown")
        self.launch_labels[index].setText(f"{name} Pressure: {value} bar")
        
    def on_label_click(self,event):
        self.new_window = Minesweeper()
        self.new_window.show()

    def Update_Elapsed_Time(self):
        currentDateTime = QDateTime.currentDateTime()
        currentTimeStr = currentDateTime.toString('yyyy/MM/dd   hh:mm:ss')
        
        elapsedTime = self.elapsedTimer.elapsed() / 1000
        elapsedHours = int(elapsedTime // 3600)
        elapsedMinutes = int((elapsedTime % 3600) // 60)
        elapsedSeconds = int(elapsedTime % 60)
        elapsedTimeStr = f'{elapsedHours:02}:{elapsedMinutes:02}:{elapsedSeconds:02}'

        for current_time_label, elapsed_time_label in self.elpased_date_time_label:
            current_time_label.setText(f'Date: {currentTimeStr[:12]}Time:{currentTimeStr[12:]}')
            elapsed_time_label.setText(f'Chrono: {elapsedTimeStr}')
            current_time_label.setStyleSheet("background-color: transparent;")
            elapsed_time_label.setStyleSheet("background-color: transparent;")
            font = QFont("Arial", 10, QFont.Bold)
            current_time_label.setFont(font)
            elapsed_time_label.setFont(font)

    def update_binary_value(self):
        binary_value = 0
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                binary_value += 2 ** i
        binary_string = f'{binary_value:04b}'
        self.tab_widget.removeTab(3)     
        self.tab_widget.insertTab(3, RealTimePlotter(data_csv, int(binary_string[0]), int(binary_string[1]), int(binary_string[2]), int(binary_string[3])), "Plot")

    def End_program(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        reply = msgBox.warning(MainWindow, "Warning", 
            "Are you sure to quit?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.worker.stop()
            if self.worker_thread.is_alive():
                self.worker_thread.join()
            print("\n\n\nYou closed the program.\nDid it work bitch (ง'-̀'́)ง  Ϟ  ฝ('-'ฝ)\n\n\n")
            QCoreApplication.quit()

    def send_command(self,command):
        self.client_socket.sendto(str.encode(command), address)
        rec_data, addr = self.client_socket.recvfrom(1024)
        return rec_data

    def update_valve_status(self, valve_label, idx, status_text, color):
        _translate = QCoreApplication.translate

        color_effect = QGraphicsColorizeEffect()
        color_effect.setColor(color)
        valve_label.setText(_translate("MainWindow", status_text))
        valve_label.setGraphicsEffect(color_effect)
        valve_label.adjustSize()

        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignCenter)
        color_effect = QGraphicsColorizeEffect()
        color_effect.setColor(color)
        status_label.setGraphicsEffect(color_effect)
        font = QFont("Arial", 8, QFont.Bold)
        status_label.setFont(font)
        if idx<nbr_SV_engine:
            self.SV_status_table_engine.setCellWidget(idx, 1, status_label)
        else:
            self.SV_status_table_cooling.setCellWidget(idx-nbr_SV_engine, 1, status_label)

    def open_valve(self, valve_number, valve_label):
        binary_list = list(self.bits)
        index = valve_number
        binary_list[index] = str(1)
        modified_binary = ''.join(binary_list)
        if board_connection == 0:
            self.update_valve_status(valve_label, valve_number, "Open", Qt.darkGreen)
        else:
            try:
                rec_data = self.send_command(modified_binary)
                if rec_data == b"ACK":
                    self.update_valve_status(valve_label, valve_number, "Open", Qt.darkGreen)
                    self.bits=modified_binary
            except:
                pass

    def close_valve(self, valve_number, valve_label):
        binary_list = list(self.bits)
        index = valve_number
        binary_list[index] = str(0)
        modified_binary = ''.join(binary_list)
        if board_connection == 0:
            self.update_valve_status(valve_label, valve_number, "Closed", Qt.red)
        else:
            try:
                rec_data = self.send_command(modified_binary)
                
                if rec_data == b"ACK":
                    self.update_valve_status(valve_label, valve_number, "Closed", Qt.red)
                    self.bits=modified_binary
            except:
                pass

    def on_checkbox_state_changed_valve(self, state, idx):
        if idx<nbr_SV_engine:
            if state == Qt.Checked:
                self.SV_frame_engine[idx].show()
                self.SV_frame_engine_status[idx].show()
                self.SV_frame_engine_label[idx].show()
                self.SV_status_table_engine.setRowHeight(idx, 30)

                if self.SV_button_ouvert_engine[idx] is not None:
                    self.SV_button_ouvert_engine[idx].show()
                if self.SV_button_ferme_engine[idx] is not None:
                    self.SV_button_ferme_engine[idx].show()
            else:
                self.SV_frame_engine[idx].hide()
                self.SV_frame_engine_status[idx].hide()
                self.SV_frame_engine_label[idx].hide()
                self.SV_status_table_engine.setRowHeight(idx, 0)

                if self.SV_button_ouvert_engine[idx] is not None:
                    self.SV_button_ouvert_engine[idx].hide()
                if self.SV_button_ferme_engine[idx] is not None:
                    self.SV_button_ferme_engine[idx].hide()
            table_width = self.SV_status_table_engine.verticalHeader().width() + self.SV_status_table_engine.horizontalHeader().length() + self.SV_status_table_engine.frameWidth() * 2
            table_height = self.SV_status_table_engine.horizontalHeader().height() + self.SV_status_table_engine.verticalHeader().length() + self.SV_status_table_engine.frameWidth() * 2
            self.SV_status_table_engine.setGeometry(QRect(290, 580, table_width, table_height))
        else:
            idx-=nbr_SV_engine
            if state == Qt.Checked:
                self.SV_frame_cooling[idx].show()
                self.SV_frame_cooling_status[idx].show()
                self.SV_frame_cooling_label[idx].show()
                self.SV_status_table_cooling.setRowHeight(idx, 30)

                if self.SV_button_ouvert_cooling[idx] is not None:
                    self.SV_button_ouvert_cooling[idx].show()
                if self.SV_button_ferme_cooling[idx] is not None:
                    self.SV_button_ferme_cooling[idx].show()
            else:
                self.SV_frame_cooling[idx].hide()
                self.SV_frame_cooling_status[idx].hide()
                self.SV_frame_cooling_label[idx].hide()
                self.SV_status_table_cooling.setRowHeight(idx, 0)

                if self.SV_button_ouvert_cooling[idx] is not None:
                    self.SV_button_ouvert_cooling[idx].hide()
                if self.SV_button_ferme_cooling[idx] is not None:
                    self.SV_button_ferme_cooling[idx].hide()
            table_width = self.SV_status_table_cooling.verticalHeader().width() + self.SV_status_table_cooling.horizontalHeader().length() + self.SV_status_table_cooling.frameWidth() * 2
            table_height = self.SV_status_table_cooling.horizontalHeader().height() + self.SV_status_table_cooling.verticalHeader().length() + self.SV_status_table_cooling.frameWidth() * 2
            self.SV_status_table_cooling.setGeometry(QRect(290, 580, table_width, table_height))

    def on_checkbox_state_changed_sensor(self, state, idx):
        if idx<nbr_sensor_engine:
            if state == Qt.Checked:
                self.sensors_engine[idx].show()
            else:
                self.sensors_engine[idx].hide()
        else:
            idx-=nbr_sensor_engine
            if state == Qt.Checked:
                self.sensors_cooling[idx].show()
            else:
                self.sensors_cooling[idx].hide()

    def update_displayed_data(self,values):
        _translate = QCoreApplication.translate

        for i,(widget, value) in enumerate(zip(self.sensors, values[1:])):
            if value==None:
                widget.setText(_translate("MainWindow", "No data"))
                font = QFont("Arial", 5, QFont.Bold)
                widget.setFont(font)

            elif i<=11:
                widget.setText(_translate("MainWindow", str(value)+"bar"))
            elif 11<i<=16:
                widget.setText(_translate("MainWindow", str(value)+"K"))
            elif 16<i:
                widget.setText(_translate("MainWindow", str(value)+"kg/s"))
            
        for widget in self.sensors:            
            font = QFont("Arial", 10, QFont.Bold)
            widget.setFont(font)
            widget.setStyleSheet("background-color: #dcdcdc")
            widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
     
class RealTimePlotter(QWidget):
    def __init__(self, csv_file,state1,state2,state3,state4):
        super().__init__()

        self.csv_file = csv_file
        self.state1 = state1
        self.state2 = state2
        self.state3 = state3
        self.state4 = state4
        self.initUI()
        
        self.x_axis_interval1 = 60
        self.x_axis_interval2 = 60
        self.x_axis_interval3 = 60
        self.x_axis_interval4 = 60
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start(100)

    def initUI(self):
        main_frame = QFrame(self)
        main_frame.setGeometry(0, 0, 1922, 1237)

        plots_frame = QFrame(main_frame)
        plots_frame.setGeometry(0, 0, 1600, 1000)
        plots_layout = QVBoxLayout(plots_frame)

        checkboxes_frame = QFrame(main_frame)
        checkboxes_frame.setGeometry(1600, 0, 500, 1000)
        checkboxes_layout = QVBoxLayout(checkboxes_frame)

        self.plot1 = pg.PlotWidget(title="Pressure")
        self.plot2 = pg.PlotWidget(title="Temperature")
        self.plot3 = pg.PlotWidget(title="Flowrate")
        self.plot4 = pg.PlotWidget(title="Force")

        self.plot1.setBackground('w')
        self.plot2.setBackground('w')
        self.plot3.setBackground('w')
        self.plot4.setBackground('w')

        plot_height = 200 
        self.plot1.setMinimumHeight(plot_height)
        self.plot2.setMinimumHeight(plot_height)
        self.plot3.setMinimumHeight(plot_height)
        self.plot4.setMinimumHeight(plot_height)

        plot_width = 1600
        self.plot1.setMaximumWidth(plot_width)
        self.plot2.setMaximumWidth(plot_width)
        self.plot3.setMaximumWidth(plot_width)
        self.plot4.setMaximumWidth(plot_width)

        name = ["PS11", "PS12", "PS21", "PS22", "PS23", "PS41", "PS42", "PS51", "PS61", "PS62", "PS63", "PS64",
                "TS11", "TS41", "TS42", "TS61", "TS62",
                "FM11", "FM21", "FM61",
                "FS01"]
        self.checkbox_frames = []
        self.buttons = []

        if self.state4==1:
            plots_layout.addWidget(self.plot1)
            self.create_checkbox_frame(self.plot1, 1, [name[i] for i in range(12)], checkboxes_layout)
        if self.state3==1:
            plots_layout.addWidget(self.plot2)
            self.create_checkbox_frame(self.plot2, 2, [name[i] for i in range(12, 17)], checkboxes_layout)
        if self.state2==1:
            plots_layout.addWidget(self.plot3)
            self.create_checkbox_frame(self.plot3, 3, [name[i] for i in range(17, 20)], checkboxes_layout)
        if self.state1==1:
            plots_layout.addWidget(self.plot4)
            self.create_checkbox_frame(self.plot4, 4, [name[-1]], checkboxes_layout)

        self.curves1 = [self.plot1.plot(pen=pg.mkPen(color=(i, len(range(1, 14))), width=5)) for i in range(12)]
        self.curves2 = [self.plot2.plot(pen=pg.mkPen(color=(i, len(range(14, 19))), width=5)) for i in range(5)]
        self.curves3 = [self.plot3.plot(pen=pg.mkPen(color=(i, len(range(19, 22))), width=5)) for i in range(3)]
        self.curve4 = self.plot4.plot(pen=pg.mkPen(color='r', width=5))

        self.curve_visibility = {
            "Pressure": [i == 0 for i in range(12)],
            "Temperature": [i == 0 for i in range(5)],
            "Flowrate": [i == 0 for i in range(3)],
            "Force": [True]
        }

        for i, curve in enumerate(self.curves1):
            curve.setVisible(self.curve_visibility["Pressure"][i])
        for i, curve in enumerate(self.curves2):
            curve.setVisible(self.curve_visibility["Temperature"][i])
        for i, curve in enumerate(self.curves3):
            curve.setVisible(self.curve_visibility["Flowrate"][i])
        self.curve4.setVisible(self.curve_visibility["Force"][0])

    def create_checkbox_frame(self, plot, idx, labels, layout):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFixedSize(280, 250)
        frame_layout = QVBoxLayout()

        interval_label = QLabel("Time Interval:")
        frame_layout.addWidget(interval_label)
        
        button_layout = QGridLayout()
        intervals = [('1m', 60), ('10m', 600), ('30m', 1800), ('All', 10**10)]
        for i, (label, x_range) in enumerate(intervals):
            button = QPushButton(label)
            self.buttons.append(button)
            button.setFixedSize(130, 35)
            button.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                background-color: white;
                border-radius: 3px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: lightgrey;
                border-color: black;
                border: 3px solid black;
            }
            """)
            if idx == 1:
                button.clicked.connect(partial(self.set_x_range1, x_range, i))
            elif idx == 2:
                button.clicked.connect(partial(self.set_x_range2, x_range, i + 4))
            elif idx == 3:
                button.clicked.connect(partial(self.set_x_range3, x_range, i + 8))
            elif idx == 4:
                button.clicked.connect(partial(self.set_x_range4, x_range, i + 12))
            button_layout.addWidget(button, i // 2, i % 2)

        frame_layout.addLayout(button_layout)

        sensors_label = QLabel("Sensors:")
        frame_layout.addWidget(sensors_label)

        checkbox_grid = QGridLayout()
        if idx == 4:
            for i, label in enumerate(labels):
                checkbox = QCheckBox(label)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(lambda state, plot=plot, i=i: self.toggle_curve(plot, i, state))
                checkbox_grid.addWidget(checkbox, 0, 0)
            curve_label1 = QLabel(" ", self)
            curve_label2 = QLabel(" ", self)
            curve_label3 = QLabel(" ", self)
            checkbox_grid.addWidget(curve_label1, 1, 0)
            checkbox_grid.addWidget(curve_label2, 2, 0)
            checkbox_grid.addWidget(curve_label3, 3, 0)
        elif idx == 3:
            for i, label in enumerate(labels):
                checkbox = QCheckBox(label)
                checkbox.setChecked(i == 0)
                checkbox.stateChanged.connect(lambda state, plot=plot, i=i: self.toggle_curve(plot, i, state))
                checkbox_grid.addWidget(checkbox, i % 4, i // 4)
            curve_label4 = QLabel(" ", self)
            checkbox_grid.addWidget(curve_label4, 3, 0)
        else:
            for i, label in enumerate(labels):
                checkbox = QCheckBox(label)
                checkbox.setChecked(i == 0)
                checkbox.stateChanged.connect(lambda state, plot=plot, i=i: self.toggle_curve(plot, i, state))
                checkbox_grid.addWidget(checkbox, i % 4, i // 4)
        
        frame_layout.addLayout(checkbox_grid)
        frame.setLayout(frame_layout)
        layout.addWidget(frame)
        self.checkbox_frames.append((plot, checkbox_grid))

    def toggle_curve(self, plot, index, state):
        visibility = state == 2
        if plot == self.plot1:
            self.curves1[index].setVisible(visibility)
            self.curve_visibility["Pressure"][index] = visibility
        elif plot == self.plot2:
            self.curves2[index].setVisible(visibility)
            self.curve_visibility["Temperature"][index] = visibility
        elif plot == self.plot3:
            self.curves3[index].setVisible(visibility)
            self.curve_visibility["Flowrate"][index] = visibility
        elif plot == self.plot4:
            self.curve4.setVisible(visibility)
            self.curve_visibility["Force"][0] = visibility

    def set_x_range1(self, x_range,i):
        self.x_axis_interval1 = x_range
        for j in range(4):
            if j==i:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: grey;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
                                                
            """)
            else:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: white;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
            """)

    def set_x_range2(self,x_range,i):
        self.x_axis_interval2 = x_range
        for j in range(4,8):
            if j==i:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: grey;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
                                                
            """)
            else:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: white;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
            """)

    def set_x_range3(self,x_range,i):
        self.x_axis_interval3 = x_range
        for j in range(8,12):
            if j==i:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: grey;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
                                                
            """)
            else:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: white;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
            """)

    def set_x_range4(self, x_range,i):
        self.x_axis_interval4 = x_range
        for j in range(12,16):
            if j==i:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: grey;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
                                                
            """)
            else:
                self.buttons[j].setStyleSheet("""
                QPushButton {
                    border: 1px solid black;
                    background-color: white;
                    border-radius: 3px;
                    height: 30px;
                }
                QPushButton:hover {
                    background-color: lightblue;
                    border-color: lightblue;
                }
            """)

    def update_plot_data(self):
        try:
            data = pd.read_csv(self.csv_file,header=None)
            time = data.iloc[:, 0].values

            for i, curve in enumerate(self.curves1):
                if self.curve_visibility["Pressure"][i]:
                    curve.setData(time, data.iloc[:, i + 1].values)
            self.plot1.setXRange(max(0, max(time) - self.x_axis_interval1), max(time))

            for i, curve in enumerate(self.curves2):
                if self.curve_visibility["Temperature"][i]:
                    curve.setData(time, data.iloc[:, i + 13].values)
            self.plot2.setXRange(max(0, max(time) - self.x_axis_interval2), max(time))

            for i, curve in enumerate(self.curves3):
                if self.curve_visibility["Flowrate"][i]:
                    curve.setData(time, data.iloc[:, i + 18].values)
            self.plot3.setXRange(max(0, max(time) - self.x_axis_interval3), max(time))

            if self.curve_visibility["Force"][0]:
                self.curve4.setData(time, data.iloc[:, 21].values)
            self.plot4.setXRange(max(0, max(time) - self.x_axis_interval4), max(time))

        except Exception as e:
            print(f"Error updating plot data: {e}")


            self.x_axis_interval4 = interval
            button_list = [self.button_1m_4, self.button_10m_4, self.button_30m_4, self.button_All_4]

            for i, button in enumerate(button_list):
                if i == id - 1:
                    button.setStyleSheet("""
        QPushButton {
            border: 1px solid black;
            background-color: grey;
            border-radius: 3px;
            height: 30px;
        }
        QPushButton:hover {
            background-color: lightblue;
            border-color: lightblue;
        }
    """)
                else:
                    button.setStyleSheet("""
        QPushButton {
            border: 1px solid black;
            background-color: white;
            border-radius: 3px;
            height: 30px;
        }
        QPushButton:hover {
            background-color: lightblue;
            border-color: lightblue;
        }
    """)
            self.update_plot()

class Worker(QObject):

    update_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()
        self.kHz_register=phase
        self.T=[]
    def stop(self):
        self.stop_event.set()
    def write_csv_arduino(self):
        i = 0
        if board_connection==1:
            client_socket = socket(AF_INET, SOCK_DGRAM)
            client_socket.settimeout(1)
            client_socket.sendto(bytearray([0xDD,0xDD]), address)

        while not self.stop_event.is_set():
            if board_connection == 0:
                if i==60 or i==120:
                    print("switch")
                    self.kHz_register **=1

                values = [i] + [round(100*np.sin(2*np.pi*0.02*i + 3*k/2),1) for k in range(21)]
                self.update_signal.emit(values)

                with open(data_csv, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(values)
                if self.kHz_register==1:
                    with open(data_1kHz_csv, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(values)
                i += 1
                time.sleep(0.25)

            else:
                ########################################################################################
                #                               Work in progress
                ########################################################################################
                data, addr = client_socket.recvfrom(4096)
                try:
                    if len(data) == 0:
                        print("No data received")

                except:
                    a = []
                    if data==bytearray([0xEE, 0xEE, 0xEE, 0xEE, 0xFF, 0xFF]):
                        phase='OFF'
                    else:

                        t = (
                            int(data[4]) << 24
                            | int(data[5]) << 16
                            | int(data[6]) << 8
                            | int(data[7])
                        )
                        self.T.append(t/1000)
                        a.append(t-self.T[0])                         

                        for i in range(8, 27, 2):
                            a1 = (int(data[i]) << 8
                                | int(data[i + 1]))
                            a1 = (25/(4))*(a1 * (5 / 1023)-0.5)
                            a.append(round(a1, 2))

                        for i in range(28, 47, 4):
                            a1 = (
                            int(data[i]) << 24
                            | int(data[i+1]) << 16
                            | int(data[i+2]) << 8
                            | int(data[i+3])
                        )
                            a.append(round(a1/100 - 273.15, 2))

                        for i in range(48, 49, 2):
                            a1 = (int(data[i]) << 8
                                | int(data[i + 1]))
                            a.append(round(a1, 2))

                        for i in range(50, 55, 2):
                            a1 = (int(data[i]) << 8
                                | int(data[i + 1]))
                            a.append(round(a1, 2))

                        for i in range(56, len(data), 2):
                            a1 = (
                            int(data[i]) << 24
                            | int(data[i+1]) << 16
                            | int(data[i+2]) << 8
                            | int(data[i+3])
                            )
                            a.append(round(a1, 2))
                        self.update_signal.emit(a)

                        with open(data_csv, 'a', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow(a)
                        if phase=='ON':
                            with open(data_1kHz_csv, 'a', newline='') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerow(values)
                        j+=1

class SplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.SplashScreen)

        self.setStyleSheet("background-color: white;")

        self.pixmap = pixmap

        self.splash_width = pixmap.width()
        self.splash_height = pixmap.height() + 50

        self.setFixedSize(self.splash_width, self.splash_height)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(10, pixmap.height() + 10, pixmap.width() - 20, 20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #1a75ff;
                width: 20px;
                height: 20px;
            }
        """)
        self.percent_label = QLabel('0%')
        self.percent_label.setFont(QFont('Arial', 16))
        self.percent_label.setAlignment(Qt.AlignCenter)

    def drawContents(self, painter):
        painter.drawPixmap(QRect(0, 0, self.pixmap.width(), self.pixmap.height()), self.pixmap)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"{value}%")

class Minesweeper(QMainWindow):
    def __init__(self, rows=20, cols=20, mines=50):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.buttons = []
        self.minefield = [[0] * cols for _ in range(rows)]
        self.revealed = [[False] * cols for _ in range(rows)]
        self.setup_ui()
        self.place_mines()

    def setup_ui(self):
        self.setWindowTitle('Minesweeper')
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout()
        central_widget.setLayout(layout)

        for row in range(self.rows):
            button_row = []
            for col in range(self.cols):
                button = QPushButton('')
                button.setFixedSize(30, 30)
                button.setStyleSheet("background-color: lightgray;")
                button.clicked.connect(lambda _, r=row, c=col: self.reveal(r, c))
                layout.addWidget(button, row, col)
                button_row.append(button)
            self.buttons.append(button_row)

        self.setGeometry(100, 100, self.cols * 30, self.rows * 30)

    def place_mines(self):
        locations = random.sample(range(self.rows * self.cols), self.mines)
        for location in locations:
            r = location // self.cols
            c = location % self.cols
            self.minefield[r][c] = -1
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols and self.minefield[nr][nc] != -1:
                        self.minefield[nr][nc] += 1

    def reveal(self, row, col):
        if self.minefield[row][col] == -1:
            QMessageBox.critical(self, 'Game Over', 'You hit a mine!')
            self.reveal_all_mines()
            return

        self._reveal_cell(row, col)
        if all(self.is_cell_revealed(r, c) or self.minefield[r][c] == -1
               for r in range(self.rows)
               for c in range(self.cols)):
            QMessageBox.information(self, 'Congratulations', 'You win!')

    def _reveal_cell(self, row, col):
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return
        if self.revealed[row][col]:
            return

        self.revealed[row][col] = True
        button = self.buttons[row][col]

        if self.minefield[row][col] == 0:
            button.setText('')
            button.setStyleSheet("background-color: white;")
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    self._reveal_cell(row + dr, col + dc)
        else:
            button.setText(str(self.minefield[row][col]))
            button.setStyleSheet("background-color: white;")

    def is_cell_revealed(self, row, col):
        return self.revealed[row][col]

    def reveal_all_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.minefield[r][c] == -1:
                    self.buttons[r][c].setText('*')
                    self.buttons[r][c].setStyleSheet("background-color: red;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    splash_pix = QPixmap('Logo_Arrax.png')
    splash = SplashScreen(splash_pix)

    screen = app.primaryScreen()
    screen_geometry = screen.geometry()
    x = (screen_geometry.width() - splash.splash_width) // 2
    y = (screen_geometry.height() - splash.splash_height) // 2
    splash.move(x, y)

    splash.show()

    for i in range(1, 101):
        time.sleep(0.01)    
        splash.update_progress(i)
        app.processEvents()

    MainWindow = QMainWindow()
    ui = Main()
    ui.setupUi(MainWindow)

    splash.finish(MainWindow)

    MainWindow.showFullScreen()

    sys.exit(app.exec_())
