"""Guide Spine IK 01 module"""

from functools import partial

from mgear.shifter.component import guide
from mgear.core import transform, pyqt
from mgear.vendor.Qt import QtWidgets, QtCore

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget

import settingsUI as sui

# guide info
AUTHOR = "Jeremie Passerin, Miquel Campos"
URL = "www.jeremiepasserin.com, www.miquel-campos.com"
EMAIL = "geerem@hotmail.com, hello@miquel-campos.com"
VERSION = [2, 0, 0]
TYPE = "spine_horizontal_01"
NAME = "spine"
DESCRIPTION = """An ik spine with an over top layer of fk controllers
that follow the ik position. Optional auto bend ik control and central
tangent control.
spine_ik_01 flipped 90 degrees for horizontal quadrupeds so Y is still up.
Modified by Chris Lesage
"""

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
        self.save_transform = ["root", "eff"]
        self.save_blade = ["blade"]

    def addObjects(self):
        """Add the Guide Root, blade and locators"""

        self.root = self.addRoot()
        vTemp = transform.getOffsetPosition(self.root, [0, 4, 0])
        self.eff = self.addLoc("eff", self.root, vTemp)
        self.blade = self.addBlade("blade", self.root, self.eff)

        centers = [self.root, self.eff]
        self.dispcrv = self.addDispCurve("crv", centers)

    def addParameters(self):
        """Add the configurations settings"""

        # Default values
        self.pPosition = self.addParam("position", "double", 0, 0, 1)
        self.pMaxStretch = self.addParam("maxstretch", "double", 1.5, 1)
        self.pMaxSquash = self.addParam("maxsquash", "double", .5, 0, 1)
        self.pSoftness = self.addParam("softness", "double", 0, 0, 1)
        self.pLockOri = self.addParam("lock_ori", "double", 1, 0, 1)

        # Options
        self.pDivision = self.addParam("division", "long", 5, 3)
        self.pAutoBend = self.addParam("autoBend", "bool", False)
        self.pCentralTangent = self.addParam("centralTangent", "bool", False)

        # FCurves
        self.pSt_profile = self.addFCurveParam(
            "st_profile", [[0, 0], [.5, -1], [1, 0]])

        self.pSq_profile = self.addFCurveParam(
            "sq_profile", [[0, 0], [.5, 1], [1, 0]])

        self.pUseIndex = self.addParam("useIndex", "bool", False)

        self.pParentJointIndex = self.addParam(
            "parentJointIndex", "long", -1, None, None)

    def get_divisions(self):
        """ Returns correct segments divisions """

        self.divisions = self.root.division.get()

        return self.divisions

##########################################################
# Setting Page
##########################################################


class settingsTab(QtWidgets.QDialog, sui.Ui_Form):
    """The Component settings UI"""

    def __init__(self, parent=None):
        super(settingsTab, self).__init__(parent)
        self.setupUi(self)


class componentSettings(MayaQWidgetDockableMixin, guide.componentMainSettings):
    """Create the component setting window"""

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
        self.resize(280, 360)

    def create_componentControls(self):
        return

    def populate_componentControls(self):
        """Populate the controls values.

        Populate the controls values from the custom attributes of the
        component.

        """
        # populate tab
        self.tabs.insertTab(1, self.settingsTab, "Component Settings")

        # populate component settings
        self.settingsTab.softness_slider.setValue(
            int(self.root.attr("softness").get() * 100))
        self.settingsTab.position_spinBox.setValue(
            int(self.root.attr("position").get() * 100))
        self.settingsTab.position_slider.setValue(
            int(self.root.attr("position").get() * 100))
        self.settingsTab.lockOri_spinBox.setValue(
            int(self.root.attr("lock_ori").get() * 100))
        self.settingsTab.lockOri_slider.setValue(
            int(self.root.attr("lock_ori").get() * 100))
        self.settingsTab.softness_spinBox.setValue(
            int(self.root.attr("softness").get() * 100))
        self.settingsTab.maxStretch_spinBox.setValue(
            self.root.attr("maxstretch").get())
        self.settingsTab.maxSquash_spinBox.setValue(
            self.root.attr("maxsquash").get())
        self.settingsTab.division_spinBox.setValue(
            self.root.attr("division").get())

        self.populateCheck(self.settingsTab.autoBend_checkBox, "autoBend")

        self.populateCheck(self.settingsTab.centralTangent_checkBox,
                           "centralTangent")

    def create_componentLayout(self):

        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):

        self.settingsTab.softness_slider.valueChanged.connect(
            partial(self.updateSlider,
                    self.settingsTab.softness_slider,
                    "softness"))
        self.settingsTab.softness_spinBox.valueChanged.connect(
            partial(self.updateSlider,
                    self.settingsTab.softness_spinBox,
                    "softness"))
        self.settingsTab.position_slider.valueChanged.connect(
            partial(self.updateSlider,
                    self.settingsTab.position_slider,
                    "position"))
        self.settingsTab.position_spinBox.valueChanged.connect(
            partial(self.updateSlider,
                    self.settingsTab.position_spinBox,
                    "position"))
        self.settingsTab.lockOri_slider.valueChanged.connect(
            partial(self.updateSlider,
                    self.settingsTab.lockOri_slider,
                    "lock_ori"))
        self.settingsTab.lockOri_spinBox.valueChanged.connect(
            partial(self.updateSlider,
                    self.settingsTab.lockOri_spinBox,
                    "lock_ori"))
        self.settingsTab.maxStretch_spinBox.valueChanged.connect(
            partial(self.updateSpinBox,
                    self.settingsTab.maxStretch_spinBox,
                    "maxstretch"))
        self.settingsTab.maxSquash_spinBox.valueChanged.connect(
            partial(self.updateSpinBox,
                    self.settingsTab.maxSquash_spinBox,
                    "maxsquash"))
        self.settingsTab.division_spinBox.valueChanged.connect(
            partial(self.updateSpinBox,
                    self.settingsTab.division_spinBox,
                    "division"))
        self.settingsTab.autoBend_checkBox.stateChanged.connect(
            partial(self.updateCheck,
                    self.settingsTab.autoBend_checkBox,
                    "autoBend"))
        self.settingsTab.centralTangent_checkBox.stateChanged.connect(
            partial(self.updateCheck,
                    self.settingsTab.centralTangent_checkBox,
                    "centralTangent"))
        self.settingsTab.squashStretchProfile_pushButton.clicked.connect(
            self.setProfile)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)
