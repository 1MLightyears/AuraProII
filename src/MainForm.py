# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainForm.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!
"""
增强型奥拉II

前端部分

"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QSystemTrayIcon, QAction, QMenu, QGraphicsDropShadowEffect, QLineEdit, QWidget, QMessageBox, QShortcut
from PyQt5.QtCore import pyqtSignal, QThread, Qt, QMutex, QPoint
from PyQt5.QtGui import QFont, QIcon, QCursor, QPixmap, QColor, QKeySequence
import PyQt5.sip

from json import loads
from os import sep
from os.path import exists
from time import sleep
import re

from Search import SearchName,SearchKM,addName

from Base import getNamebyID, font_path, TMsgEntry, Serialize
from Base import settings, Existsin, history, MDStyleStr, RGB2Hex, log,version
import resources

#进程锁
MutLabelList = QMutex()
MutEndSearch = QMutex()

#记录线程
thread_pool = set()
#记录当前运行的线程
current_thread_set = set()

class TThread(QThread):
    def __init__(self,func,args=(),next_step=None):
        #记录这个线程
        super(TThread, self).__init__()
        self.__name__=func.__name__
        self.func = func
        self.args = args if isinstance(args,tuple) else (args,)
        self.Msg=None

    def run(self):
        log("thread:"+self.__name__+",args="+self.args.__str__())
        self.Msg = self.func(*self.args)

class TMsgLabel(QLabel):
    def __init__(self, m=TMsgEntry(),no=-1,):
        super(TMsgLabel, self).__init__()
        self.no = no #在LabelList中的序号
        self.on_events = False  #正在响应事件
        self.MsgEntry=m

        left, top = self.MsgEntry.left, self.MsgEntry.top + (self.no * settings["labelFontSize"] * 6)
        self.move(left,top)
        self.setScaledContents = True  #自动拉伸
        self.setWordWrap = True
        self.setFont(QFont(font_path[settings["lang"]]))
        self.setTextFormat(Qt.MarkdownText)
        self.setText(font_path[settings["lang"]])
        if self.MsgEntry.style_str != "":
            #将html标签形式的font包装成text
            l= re.findall(r"<([a-zA-Z0-9\-_]*)([a-zA-Z0-9\-_#= ]*)>",self.MsgEntry.style_str)
            self.setText(self.MsgEntry.style_str + self.MsgEntry.text + ''.join(["</" + i[0] + ">" for i in l]))
        # 添加阴影
        self.effect_shadow = QGraphicsDropShadowEffect(self)
        text_color = re.search(r"color=(#[0-9A-F]*)", self.text())
        text_color = RGB2Hex((8,8,160,127)) if text_color == None else text_color.group(1)
        self.effect_shadow.setOffset(0,0)  # 偏移
        self.effect_shadow.setColor(QColor(text_color))  # 阴影颜色
        self.effect_shadow.setBlurRadius(10)  # 阴影半径
        self.setGraphicsEffect(self.effect_shadow)  # 将设置套用到widget窗口中

    def mousePressEvent(self, e):  # 单击
        global current_thread_set
        self.on_events = True
        self.parent().parent().LabelList_click_no = self.no
        if self.MsgEntry.ClickEvent != None:
            log("label:"+self.text()+",ClickEvent="+str(self.MsgEntry.ClickEvent)+",ClickArgs="+str(self.MsgEntry.ClickArgs))
            current_thread_set=set()
            self.parent().parent().EndSearchEvent()
            if self.MsgEntry.ClickEvent == SearchName:
                self.parent().parent().RefreshLabelList({"Searching": TMsgEntry(
                    text="正在搜索角色{name}...".format(name=str(self.MsgEntry.ClickArgs[0])),
                    style_str=MDStyleStr(
                            color=settings["clHint"],
                            font_size=settings["labelFontSize"]
                        ))})
                self.MsgEntry.ClickReturn = self.parent().parent().MultiThreadRun(func=self.MsgEntry.ClickEvent, args=self.MsgEntry.ClickArgs)
            elif self.MsgEntry.ClickEvent == SearchKM:
                #TODO:增加一个判断，如果已经获取了km则不重复获取
                if self.MsgEntry.ClickReturn == None:
                    self.parent().parent().StatusBar.showMessage("正在获取km...")
                    self.MsgEntry.ClickReturn = self.parent().parent().MultiThreadRun(func=self.MsgEntry.ClickEvent, args=self.MsgEntry.ClickArgs)
                # else:
                #     self.MsgEntry.enable = not self.MsgEntry.enable
                #     self.parent().parent().RefreshLabelList()


        self.on_events=False

    def leaveEvent(self, e):  # 鼠标离开label
        try:
            self.on_events=True
            #移回原位
            self.move(10, self.geometry().top())
            self.parent().parent().statusBar().clearMessage()
            if self.cursor()==Qt.PointingHandCursor:
                self.setCursor(Qt.ArrowCursor)
                self.effect_shadow.setOffset(0, 0)  # 偏移
        except Exception as e:
            self.on_events=False
            return e
        finally:
            self.on_events=False

    def enterEvent(self, e):  # 鼠标移入label
        try:
            if not self.on_events:
                self.on_events = True
                s = ""
                if self.MsgEntry.ClickEvent == SearchKM:
                    s += ("单击:获取击杀概况 KillMailID="+ str(self.MsgEntry.ClickArgs[1]))
                elif self.MsgEntry.ClickEvent == SearchName:
                    s += ("单击:获取角色 " + self.MsgEntry.ClickArgs[0] + "的信息")
                elif (self.text().find("href") >= 0):
                    s += "单击:在浏览器中打开链接" + re.search(r"'(http.*)'",self.text()).group(1)
                self.parent().parent().statusBar().showMessage(s)
                if s!="":
                    #手形指针
                    self.setCursor(Qt.PointingHandCursor)
                    #外框
                    self.effect_shadow.setOffset(5, 5)  # 偏移

                if self.geometry().width() > self.parent().parent().geometry().width():  #Label超长
                    while self.on_events:#如果一直在悬停中
                        #先往左移
                        while self.on_events and (self.geometry().left()+self.geometry().width()>self.parent().parent().geometry().width()):
                            self.move(self.geometry().left() - 1, self.geometry().top())
                            QApplication.processEvents()
                            sleep(0.02)
                        #移动到终点停1s
                        for i in range(50):
                            QApplication.processEvents()
                            if not self.on_events:
                                break
                            sleep(0.02)

                        #再往右移
                        while self.on_events and (self.geometry().left()<10):
                            self.move(self.geometry().left() + 1, self.geometry().top())
                            QApplication.processEvents()
                            sleep(0.02)
                        for i in range(50):
                            QApplication.processEvents()
                            if not self.on_events:
                                break
                            sleep(0.02)
                self.on_events=False
        except Exception as e:
            self.on_events=False
            return e


class TEdtName(QLineEdit):
    def __init__(self, *args,**kwargs):
        super(TEdtName, self).__init__(*args,**kwargs)
        self.setObjectName("EdtName")
        self.setAcceptDrops(True)
        self.textChanged.connect(self.textChangeEvent)

    def textChangeEvent(self, e):
        self.setStyleSheet("""
            TEdtName{
                border: 1px grey;
                border-style: none;
                border-radius: 10px;
                padding:1px 2px;
                color:rgb(255,0,0);
                background-color:rgba(0,0,0,127)
            }
            TEdtName:focus{
                color:rgb(255,0,0);
                background-color: rgb(0,0,0)
            }""")

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('text/plain'):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        #如果是zkb链接：
        log("拖入"+e.mimeData().text())
        self.setText(e.mimeData().text())
        self.parent().parent().StartSearchName(e.mimeData().text())

class Ui_MainWindow(QMainWindow, object):
    def setupUi(self, MainWindow):
        #载入资源文件
        #载入字体
        for i in font_path:
            if exists(settings["workingDir"]+font_path[i]):
                QtGui.QFontDatabase.addApplicationFont(settings["workingDir"]+font_path[i])
            else:
                log("字体不存在:" + font_path[i] + "(" + settings["lang"] + ")", level="error")
                font_path[i] = "Arial"

        self.setObjectName("MainWindow")
        self.resize(400, 300)
        self.setFixedSize(MainWindow.width(), MainWindow.height())
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowOpacity(settings["WindowOpacity"])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint)

        #widget
        if exists(settings["workingDir"]+settings["backgroundPath"]):
            backgroundPath=settings["workingDir"]+settings["backgroundPath"]
            log("加载背景图片:" + backgroundPath)
        else:
            backgroundPath = ":/black.png"
            log("未找到背景图片")
        self.RoundWidget = QWidget(parent=MainWindow)
        self.RoundWidget.setGeometry(MainWindow.geometry())
        self.RoundWidget.setStyleSheet("QWidget{border-image: url("+backgroundPath.replace(sep,"/")+r") 100% 100% round;border-radius:15px;}")
        self.RoundWidget.show()

        #拖动功能
        self._startPos,self._endPos=QPoint(0,0),QPoint(0,0)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        QApplication.setQuitOnLastWindowClosed(False)

        self.BtnSearch = QtWidgets.QPushButton(self.centralwidget)
        self.BtnSearch.setGeometry(QtCore.QRect(350, 10, 40, 40))
        self.BtnSearch.setText("")
        self.BtnSearch.setIcon(QIcon(":/AuraProII.ico"))
        self.BtnSearch.setIconSize(QtCore.QSize(40, 40))
        self.BtnSearch.setStyleSheet(r"QPushButton{border:1px solid;padding:5px;border-radius:10px;}")
        self.BtnSearch.setObjectName("BtnSearch")
        QShortcut(QKeySequence(settings["SearchShortCut"]), self.BtnSearch).activated.connect(self.BtnSearchClickEvent)
        self.BtnSearch.setToolTip("快捷键:"+settings["SearchShortCut"])
        self.BtnSearch.clicked.connect(self.EndSearchEvent)
        self.BtnSearch.clicked.connect(self.BtnSearchClickEvent)

        self.StatusBar = QtWidgets.QStatusBar(self.centralwidget)
        self.StatusBar.setStyleSheet("QStatusBar{color:rgba"+settings["clStatusBar"]+";}")
        self.setStatusBar(self.StatusBar)
        self.StatusBar.showMessage("增强型奥拉 II:"+version)

        self.EdtName = TEdtName(self.centralwidget)
        self.EdtName.setGeometry(QtCore.QRect(10, 10, 340, 40))
        self.EdtName.setPlaceholderText("在这里输入名字...")
        self.EdtName.setStyleSheet("""
            TEdtName{
                border:1px grey;
                border-style: none;
                border-radius:10px;
                padding:1px 2px;
                color:rgb(255,0,0);
                background-color:rgba(0,0,0,127)
            }
            """)
        self.EdtName.show()

        self.TrayMenu = QMenu(self)
        self.TrayMenu.addAction(QAction("显示/隐藏主界面", parent=self.TrayMenu,checkable=True,checked=True, triggered=self.ToggleShowHide))
        self.TrayMenu.addAction(QAction("主界面置顶", parent=self.TrayMenu, checkable=True, checked=True, triggered=self.ToggleStayOnTop))
        self.TrayMenu.addSeparator()
        self.TrayMenu.addAction(QAction("关于...", parent=self.TrayMenu, triggered=self.ShowAbout))
        self.TrayMenu.addSeparator()
        self.TrayMenu.addAction(QAction("停用 增强型奥拉II",parent=self.TrayMenu, triggered=self.quit))

        self.TrayIcon = QSystemTrayIcon(self)
        self.TrayIcon.setIcon(QIcon(":/AuraProII.ico"))
        self.TrayIcon.setToolTip(u'增强型奥拉 II:激活中')
        self.TrayIcon.show()
        self.TrayIcon.showMessage(u"增强型奥拉 II:"+version, "Fly safe o/", 0)
        self.TrayIcon.activated.connect(self.TrayIconClickEvent)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda:self.TrayMenu.exec_(QCursor.pos()))
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        #窗体创建完毕
        #信息列表
        self.MsgEntryList = {}
        # MsgEntryList结构
        # 每项为每个过程加入的信息
        # 如，StartSearchKB后，MsgEntryList中的内容应为:
        # {"SearchName":{
        #                   "Label":"正在搜索角色",
        #                   "ID":*******
        #               }
        #  "SearchKB":{...}
        # RefreshLabelList只会显示被SerializeMsgEntryList抽出的TMsgLabel对象

        #用于显示信息列表的Label列表
        self.LabelList = []
        self.LabelList_buffer = []
        self.LabelList_click_no = -1
        self.LabelList_pos=0

        #窗体创建完毕
        log("窗体创建完毕")

    def retranslateUi(self, MainWindow):
        _t = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_t("MainWindow", "MainWindow"))
        self.BtnSearch.setShortcut(_t("MainWindow", "Enter"))

    def quit(self):
        """
        终止程序。
        """
        self.TrayIcon.hide()
        self.closeEvent(None)
        self.EndSearchEvent()
        log("退出")
        QApplication.quit()

    def ToggleShowHide(self):
        """
        显示/隐藏主界面。
        """
        if self.sender().isChecked():
            self.show()
        else:
            self.hide()

    def ToggleStayOnTop(self):
        """
        切换窗口置顶。
        """
        if self.sender().isChecked():
            self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint)

    def ShowAbout(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle(u'关于...')
        msgBox.setIconPixmap(QPixmap(":/AuraProII.png"))
        msgBox.setText(u"""
            增强型奥拉 II
            """+version+"""
            by 百万光年
            1mlightyears@gmail.com""")
        msgBox.setWindowIcon(QIcon(":/AuraProII.ico"))

        msgBox.exec_()

    #event
    def mouseMoveEvent(self, e):  # 重写移动事件
        try:
            self.on_events=True
            self._endPos = e.pos() - self._startPos
            self.move(self.pos() + self._endPos)
        except Exception as error:
            self._endPos = e.pos()
            self._startPos = e.pos()
        finally:
            self.on_events = False

    def mousePressEvent(self, e):
        self.EdtName.clearFocus()
        if e.button() == Qt.LeftButton:
            self._isTracking = True
            self._startPos = QPoint(e.x(), e.y())

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None

    def closeEvent(self, event):
        self.hide()

    def TrayIconClickEvent(self, reason):
        if reason == 1:
            self.TrayMenu.exec_(QCursor.pos())
        elif reason == 2:
            self.TrayMenu.actions()[0].setChecked(True)
            self.show()

    def wheelEvent(self, event):
        if len(self.LabelList)>0:
            self.on_events = True
            ori=event.angleDelta().y()/120 if not isinstance(event,int) else event
            if ori > 0:
                #向上移
                if self.LabelList[0].geometry().top() < self.EdtName.geometry().height()+self.EdtName.geometry().top():
                    self.LabelList_pos+=1
                    for i in self.LabelList:
                        i.move(i.geometry().left(),i.geometry().top() + 10)
            else:
                #向下移
                if self.LabelList[-1].geometry().top() + self.LabelList[-1].geometry().height() > self.StatusBar.geometry().top():
                    self.LabelList_pos-=1
                    for i in self.LabelList:
                        i.move(i.geometry().left(),i.geometry().top() - 10)
            if not isinstance(event, int):
                event.accept()
            self.on_events = False

    def BtnSearchClickEvent(self):
        return self.StartSearchName()

    def EndSearchEvent(self,e=None):
        """
        搜索结束事件。
        将传递信息的线程传来的
        """
        if isinstance(self.sender(), TThread):
            log("EndSearch:"+str(self.sender().__name__))
            MutEndSearch.lock()
            Msg = self.sender().Msg
            log("Msg="+str(Msg))

            if id(self.sender()) not in current_thread_set:
                #说明不是此次搜索的返回线程，直接丢弃
                MutEndSearch.unlock()
                return - 1

            #由SearchName返回
            if "getKMList" in Msg:#完成了一轮完整的搜索流程
                self.MsgEntryList = {}
                self.MsgEntryList.update(Msg)
                self.statusBar().showMessage("搜索完成")
                self.EdtName.setStyleSheet("""
                    TEdtName{
                        border: 2px groove white;
                        border-radius: 3px;
                        padding:2px 3px;
                        color:rgb(255,0,0);
                        background-color:rgba(0,0,0,0)
                    }
                    TEdtName:focus{
                        color:rgb(0,255,0);
                        background-color: rgb(0,0,0)
                    } """)
            elif "Error" in Msg:  #SearchName返回错误
                self.MsgEntryList = {}
                self.MsgEntryList.update(Msg)
                if Msg["Error"] == "getKMListError":
                    self.MsgEntryList.update({"ErrorLabel": TMsgEntry("获取KM列表失败",style_str=MDStyleStr(color=settings["clFailed"],font_size=settings["labelFontSize"]))})
                elif Msg["Error"] == "zkbError":
                    self.MsgEntryList.update({"ErrorLabel": TMsgEntry("zkb查询失败",style_str=MDStyleStr(color=settings["clFailed"],font_size=settings["labelFontSize"]))})
                elif Msg["Error"] == "esiError":
                    self.MsgEntryList.update({"ErrorLabel": TMsgEntry("查询角色ID失败", style_str=MDStyleStr(color=settings["clFailed"], font_size=settings["labelFontSize"]))})
                elif Msg["Error"] == "SearchKMError":
                    self.MsgEntryList.update({"ErrorLabel": TMsgEntry("查询KM失败", style_str=MDStyleStr(color=settings["clFailed"], font_size=settings["labelFontSize"]))})
                elif Msg["Error"] == "NoSuchCharacterError":
                    self.MsgEntryList.update({"ErrorLabel": TMsgEntry("无此角色", style_str=MDStyleStr(color=settings["clFailed"], font_size=settings["labelFontSize"]))})

            elif "NameList" in Msg:  #多个搜索结果命中
                self.MsgEntryList.update({"MultipleHits": TMsgEntry("命中" + str(len(Msg["NameList"])) + "条搜索结果...",style_str=MDStyleStr(color=settings["clHint"],font_size=settings["labelFontSize"]))})
                NameList = Msg["NameList"][:]
                no=0
                for c in NameList:
                    no+=1
                    self.MultiThreadRun(func=addName, args=(c, no))
            elif "TooManyResults" in Msg:  #搜索结果命中数超过ResultCountLimit
                self.MsgEntryList.update(Msg)
                self.MultiThreadRun(func=SearchName,args=(Msg["name"],-1,True))

            #由addName返回
            elif "addName" in Msg:
                #处理addName返回的情况
                #addName会多并发调用EndSearchEvent,因此需要QMutex
                #addName会返回成对的name和characterID，每个返回都应被添加至self.MsgEntryList["addName"]
                if "addName" not in self.MsgEntryList:
                    self.MsgEntryList["addName"]=[]
                self.MsgEntryList["addName"] += Msg["addName"]

            #由SearchKM返回
            elif "SearchKM" in Msg:
                if self.LabelList_click_no != -1:
                    #需要找到被单击的Label在self.MsgEntryList中的位置
                    for i in range(len(self.MsgEntryList["getKMList"])):
                        #如果getKMList中记录的killmail_id==LabelList中记录的killmail_id
                        if (self.MsgEntryList["getKMList"][i][0][0]==self.LabelList[self.LabelList_click_no].MsgEntry.ClickArgs[1]):
                            self.MsgEntryList["getKMList"][i][2]=Msg
                            break
                self.statusBar().showMessage("KM已获取")
            MutEndSearch.unlock()
            self.RefreshLabelList()

    #custom
    def MultiThreadRun(self, *args, **kwargs):
        """
        启动多线程，用于网络IO
        """
        global thread_pool,current_thread_set
        t = TThread(*args, **kwargs)
        if not isinstance(t, TThread):
            return -1
        t.finished.connect(self.EndSearchEvent)
        if id(t) not in thread_pool:
            thread_pool.add(t)
            current_thread_set.add(id(t))
        else:
            QMessageBox.warning(self, "错误", "无法创建线程。", QMessageBox.standardButton)
            self.quit()
        return t.start()

    def RefreshLabelList(self, Msg=None):
        """
        刷新LabelList显示。
        Msg(None or dict):作为回调时需要在self.MsgEntryList中添加的信息
        """
        #作为多线程的回调，此进程需要加锁。
        global MutLabelList
        while not MutLabelList.tryLock(1):
            sleep(0.1)
            self.statusBar().showMessage("错误:无法刷新信息列表")
        ret=0

        #由于MsgLabel可能正在响应事件所以不能直接deleteLater
        #使用double buffer
        for i in self.LabelList_buffer:
            while (i.on_events):
                i.on_events=False
                sleep(0.1)
            i.deleteLater()
        for i in self.LabelList:
            i.hide()
        self.LabelList_buffer=self.LabelList[:]
        self.LabelList = []

        if isinstance(Msg,dict):
            self.MsgEntryList.update(Msg)
        #把MsgEntryList展平
        new_label_list = Serialize(self.MsgEntryList)

        count=-1
        for i in new_label_list:
            #每个i都是一个TMsgEntry
            count += 1
            if i.enable:
                self.LabelList.append(TMsgLabel(m=i,no=count))
        for i in self.LabelList:
            i.setParent(self.centralwidget)
            i.setOpenExternalLinks(True)
            i.show()
            i.lower()
        #向上滚动至之前位置
        wheel_pos = self.LabelList_pos
        self.LabelList_pos=0
        for i in range(abs(wheel_pos)):
            if i != -self.LabelList_pos:
                break
            self.wheelEvent(int(wheel_pos / abs(wheel_pos)))
        log("RefreshLabelList:"+','.join([i.text() for i in self.LabelList]))
        MutLabelList.unlock()
        return ret

    def StartSearchName(self,name:str=""):
        """
        开始一轮搜索。
        """
        global current_thread_set
        if name=="":
            name = self.EdtName.text()
        #检查这是否是一个合适的name
        name = name.strip(" \n\"\'“”‘’")
        if name == "":
            self.statusBar().showMessage("错误:没有输入名字")
            return - 1
        #如果是一个zkb链接
        fetch = re.search(r"https://zkillboard\.com/character/([0-9]*)/", name)
        if fetch != None:
            log("导入zkb链接"+fetch.group(0))
            self.RefreshLabelList({"LoadFromzkbLink": [TMsgEntry(
                "导入zkb链接 " + fetch.group(0),
                style_str=MDStyleStr(color=settings["clHint"], font_size=settings["labelFontSize"])
            ),TMsgEntry(
                "正在搜索...",
                style_str=MDStyleStr(color=settings["clHint"], font_size=settings["labelFontSize"])
            )]})
            self.MultiThreadRun(func=SearchName, args=(None, int(fetch.group(1))))
        else:
            name=re.search(r"^[a-zA-Z0-9 '\-_]*$", name)
            if name==None:
                #名字中含有非法字符
                self.statusBar().showMessage("错误:名字中含有非法字符")
                return - 1
            else:
                name=name.group(0)

            self.MsgEntryList = {}
            current_thread_set = set()
            log("搜索"+name)
            self.RefreshLabelList({"SearchName": {
                "Searching": [name,
                    TMsgEntry("正在搜索名字包含" + name + '的角色...',
                        style_str=MDStyleStr(
                            color=settings["clHint"],
                            font_size=settings["labelFontSize"]
                        )
                    ),
                ]
            }})
            self.MultiThreadRun(func=SearchName, args=(name,))
        return 0