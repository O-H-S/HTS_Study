# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'training_trader.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets

class TraderUI(QtWidgets.QFrame):
    def __init__(self, parent):
        QtWidgets.QFrame.__init__(self, parent)
        self.setupUi()

    def setupUi(self):
        self.setGeometry(QtCore.QRect(100, 30, 150, 200))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(150, 200))
        self.setMaximumSize(QtCore.QSize(150, 200))
        self.setAutoFillBackground(True)
        self.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setLineWidth(1)
        self.setObjectName("frame_2")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setSpacing(3)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_6.addWidget(self.label_2, 0, QtCore.Qt.AlignTop)
        self.label_3 = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_6.addWidget(self.label_3, 0, QtCore.Qt.AlignTop)
    
    def setContent(self, name, fund):
        self.label_2.setText(name)
        self.label_3.setText(fund)

