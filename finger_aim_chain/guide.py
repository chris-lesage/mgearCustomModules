"""Guide Chain 01 module"""

from functools import partial

from mgear.shifter.component import guide
from mgear.core import pyqt
from mgear.vendor.Qt import QtWidgets, QtCore

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget

import settingsUI as sui


# guide info
AUTHOR = "Jeremie Passerin, Miquel Campos, Chris Lesage"
URL = "www.jeremiepasserin.com, www.miquel-campos.com, rigmarolestudio.com"
EMAIL = "geerem@hotmail.com, hello@miquel-campos.com, chris@rigmarolestudio.com"
VERSION = [1, 0, 0]
TYPE = "finger_aim_chain"
NAME = "finger"
DESCRIPTION = "Simple FK chain, where the parent is aimed so translating does not skew."

##########################################################
# CLASS
##########################################################


class Guide(guide.ComponentGuide):
    """Component Guide Class"""

    compType = TYPE
    compName = NAME
    description = DESCRIPTION

    author = AUTHOR
    url = URL
    email = EMAIL
    version = VERSION

    def postInit(self):
        """Initialize the position for the guide"""

        self.save_transform = ["root", "#_loc"]
        self.save_blade = ["blade"]
        self.addMinMax("#_loc", 1, -1)

    def addObjects(self):
        """Add the Guide Root, blade and locators"""

        self.root = self.addRoot()
        self.locs = self.addLocMulti("#_loc", self.root)
        self.blade = self.addBlade("blade", self.root, self.locs[0])

        centers = [self.root]
        centers.extend(self.locs)
        self.dispcrv = self.addDispCurve("crv", centers, 1)

    def addParameters(self):
        """Add the configurations settings"""

        self.pType = self.addParam("mode", "long", 0, 0)
        self.pBlend = self.addParam("blend", "double", 1, 0, 1)
        self.pNeutralPose = self.addParam("neutralpose", "bool", True)
        self.pIkRefArray = self.addParam("ikrefarray", "string", "")
        self.pUseIndex = self.addParam("useIndex", "bool", False)
        self.pParentJointIndex = self.addParam(
            "parentJointIndex", "long", -1, None, None)


##########################################################
# Setting Page
##########################################################


class settingsTab(QtWidgets.QDialog, sui.Ui_Form):

    def __init__(self, parent=None):
        super(settingsTab, self).__init__(parent)
        self.setupUi(self)


class componentSettings(MayaQWidgetDockableMixin, guide.componentMainSettings):

    def __init__(self, parent=None):
        self.toolName = TYPE
        # Delete old instances of the componet settings window.
        pyqt.deleteInstances(self, MayaQDockWidget)

        super(self.__class__, self).__init__(parent=parent)
        self.settingsTab = settingsTab()

        self.setup_componentSettingWindow()
        self.create_componentControls()
        self.populate_componentControls()
        self.create_componentLayout()
        self.create_componentConnections()

    def setup_componentSettingWindow(self):
        self.mayaMainWindow = pyqt.maya_main_window()

        self.setObjectName(self.toolName)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(TYPE)
        self.resize(280, 350)

    def create_componentControls(self):
        return

    def populate_componentControls(self):
        """Populate Controls

        Populate the controls values from the custom attributes of the
        component.

        """
        # populate tab
        self.tabs.insertTab(1, self.settingsTab, "Component Settings")

        # populate component settings
        self.settingsTab.ikfk_slider.setValue(
            int(self.root.attr("blend").get() * 100))
        self.settingsTab.ikfk_spinBox.setValue(
            int(self.root.attr("blend").get() * 100))
        self.settingsTab.mode_comboBox.setCurrentIndex(
            self.root.attr("mode").get())

        if self.root.attr("neutralpose").get():
            self.settingsTab.neutralPose_checkBox.setCheckState(
                QtCore.Qt.Checked)
        else:
            self.settingsTab.neutralPose_checkBox.setCheckState(
                QtCore.Qt.Unchecked)

        ikRefArrayItems = self.root.attr("ikrefarray").get().split(",")
        for item in ikRefArrayItems:
            self.settingsTab.ikRefArray_listWidget.addItem(item)

    def create_componentLayout(self):

        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):

        self.settingsTab.ikfk_slider.valueChanged.connect(
            partial(self.updateSlider, self.settingsTab.ikfk_slider, "blend"))
        self.settingsTab.ikfk_spinBox.valueChanged.connect(
            partial(self.updateSlider, self.settingsTab.ikfk_spinBox, "blend"))

        self.settingsTab.mode_comboBox.currentIndexChanged.connect(
            partial(self.updateComboBox,
                    self.settingsTab.mode_comboBox,
                    "mode"))

        self.settingsTab.neutralPose_checkBox.stateChanged.connect(
            partial(self.updateCheck,
                    self.settingsTab.neutralPose_checkBox,
                    "neutralpose"))

        self.settingsTab.ikRefArrayAdd_pushButton.clicked.connect(
            partial(self.addItem2listWidget,
                    self.settingsTab.ikRefArray_listWidget,
                    "ikrefarray"))
        self.settingsTab.ikRefArrayRemove_pushButton.clicked.connect(
            partial(self.removeSelectedFromListWidget,
                    self.settingsTab.ikRefArray_listWidget,
                    "ikrefarray"))
        self.settingsTab.ikRefArray_listWidget.installEventFilter(self)

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)
