"""
增强型奥拉 II Python ver.
20200906

主入口部分

"""

from PyQt5.QtWidgets import QApplication

import sys

import Base
from MainForm import Ui_MainWindow

#启动主窗体
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Ui_MainWindow()
    main_window.setupUi(main_window)
    main_window.show()
    Base.log("启动主窗体")
    sys.exit(app.exec_())