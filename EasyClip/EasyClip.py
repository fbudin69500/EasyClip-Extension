from __main__ import vtk, qt, ctk, slicer

import numpy
import SimpleITK as sitk
from math import *

import unittest
from slicer.ScriptedLoadableModule import *

import os

#
# Load Files
#

class EasyClip(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Easy Clip"
        parent.categories = ["Shape Analysis"]
        parent.dependencies = []
        parent.contributors = ["Julia Lopinto, (University Of Michigan)"]
        parent.helpText = """
        This Module is used to clip one or different 3D Models according to a predetermined plane.
        Plane can be saved to be reused for other models.
        After clipping, the models are closed and can be saved as new 3D Models.

        This is an alpha version of the module.
        It can't be used for the moment.
        """
        
        parent.acknowledgementText = """
            This work was supported by the National
            Institutes of Dental and Craniofacial Research
            and Biomedical Imaging and Bioengineering of
            the National Institutes of Health under Award
            Number R01DE024450.
            """
        
        
        
        self.parent = parent

class EasyClipWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        # Instantiate and connect widgets
        #
        # Interface
        #
        # Collapsible button -- Scene Description
        self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadCollapsibleButton.text = "Scene"
        self.layout.addWidget(self.loadCollapsibleButton)

        # Layout within the laplace collapsible button
        self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

        # GLOBALS:
        self.image = None
        self.logic = EasyClipLogic()
        #--------------------------- List of Models --------------------------#

        treeView = slicer.qMRMLTreeView()
        treeView.setMRMLScene(slicer.app.mrmlScene())
        treeView.setSceneModelType('Displayable')
        treeView.sceneModel().setHorizontalHeaderLabels(["Models"])
        treeView.sortFilterProxyModel().nodeTypes = ['vtkMRMLModelNode']
        header = treeView.header()
        header.setResizeMode(0, qt.QHeaderView.Stretch)
        header.setVisible(True)
        self.loadFormLayout.addWidget(treeView)


        #------------------------ Compute Bounding Box ----------------------#
        buttonFrameBox = qt.QFrame(self.parent)
        buttonFrameBox.setLayout(qt.QHBoxLayout())
        self.loadFormLayout.addWidget(buttonFrameBox)

        self.computeBox = qt.QPushButton("Compute Bounding Box around all models")
        buttonFrameBox.layout().addWidget(self.computeBox)
        self.computeBox.connect('clicked()', self.onComputeBox)

        #--------------------------- Clipping Part --------------------------#

        # Collapsible button -- Clipping part
        self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadCollapsibleButton.text = "Clipping"
        self.layout.addWidget(self.loadCollapsibleButton)

        # Layout within the laplace collapsible button
        self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

        #-------------------------- Buttons --------------------------#
        # CLIPPING BUTTONS

        self.red_plane_box = qt.QGroupBox("Red Slice Clipping")
        self.red_plane_box.setCheckable(True)
        self.red_plane_box.setChecked(False)
        self.red_plane_box.connect('clicked(bool)', self.redPlaneCheckBoxClicked)

        self.radio_red_Neg = qt.QRadioButton("Keep Down Arrow")
        self.radio_red_Neg.setIcon(qt.QIcon(":/Icons/RedSpaceNegative.png"))
        self.radio_red_Pos = qt.QRadioButton("Keep Top Arrow")
        self.radio_red_Pos.setIcon(qt.QIcon(":/Icons/RedSpacePositive.png"))

        vbox = qt.QHBoxLayout()
        vbox.addWidget(self.radio_red_Neg)
        vbox.addWidget(self.radio_red_Pos)
        vbox.addStretch(1)
        self.red_plane_box.setLayout(vbox)
        self.loadFormLayout.addWidget(self.red_plane_box)

        self.yellow_plane_box = qt.QGroupBox("Yellow Slice Clipping")
        self.yellow_plane_box.setCheckable(True)
        self.yellow_plane_box.setChecked(False)
        self.yellow_plane_box.connect('clicked(bool)', self.yellowPlaneCheckBoxClicked)

        self.radio_yellow_Neg= qt.QRadioButton("Keep Down Arrow")
        self.radio_yellow_Neg.setIcon(qt.QIcon(":/Icons/YellowSpaceNegative.png"))
        self.radio_yellow_Pos = qt.QRadioButton("Keep Top Arrow")
        self.radio_yellow_Pos.setIcon(qt.QIcon(":/Icons/YellowSpacePositive.png"))

        vbox = qt.QHBoxLayout()
        vbox.addWidget(self.radio_yellow_Neg)
        vbox.addWidget(self.radio_yellow_Pos)
        vbox.addStretch(1)
        self.yellow_plane_box.setLayout(vbox)
        self.loadFormLayout.addWidget(self.yellow_plane_box)


        self.green_plane_box = qt.QGroupBox("Green Slice Clipping")
        self.green_plane_box.setCheckable(True)
        self.green_plane_box.setChecked(False)
        self.green_plane_box.connect('clicked(bool)', self.greenPlaneCheckBoxClicked)

        self.radio_green_Neg= qt.QRadioButton("Keep Down Arrow")
        self.radio_green_Neg.setIcon(qt.QIcon(":/Icons/GreenSpaceNegative.png"))
        self.radio_green_Pos = qt.QRadioButton("Keep Top Arrow")
        self.radio_green_Pos.setIcon(qt.QIcon(":/Icons/GreenSpacePositive.png"))

        vbox = qt.QHBoxLayout()
        vbox.addWidget(self.radio_green_Neg)
        vbox.addWidget(self.radio_green_Pos)
        vbox.addStretch(1)
        self.green_plane_box.setLayout(vbox)
        self.loadFormLayout.addWidget(self.green_plane_box)

        buttonFrame = qt.QFrame(self.parent)
        buttonFrame.setLayout(qt.QHBoxLayout())
        self.loadFormLayout.addWidget(buttonFrame)

        self.ClippingButton = qt.QPushButton("Clipping")
        buttonFrame.layout().addWidget(self.ClippingButton)
        self.ClippingButton.connect('clicked()', self.ClippingButtonClicked)

        self.UndoButton = qt.QPushButton("Undo")
        buttonFrame.layout().addWidget(self.UndoButton)
        self.UndoButton.connect('clicked()', self.UndoButtonClicked)

        #--------------------------- Advanced Part --------------------------#
        #-------------------- Collapsible button -- Clipping part ----------------------#

        self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadCollapsibleButton.text = "Planes"
        self.layout.addWidget(self.loadCollapsibleButton)

        #-------------------- Layout within the laplace collapsible button ----------------------#
        self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

        buttonFrame = qt.QFrame(self.parent)
        buttonFrame.setLayout(qt.QVBoxLayout())
        self.loadFormLayout.addWidget(buttonFrame)

        #-------------------- SAVE PLANE BUTTON ----------------------#

        save_plane = qt.QLabel("Save the planes you create as a txt file.")
        buttonFrame.layout().addWidget(save_plane)
        save = qt.QPushButton("Save plane")
        buttonFrame.layout().addWidget(save)
        save.connect('clicked(bool)', self.savePlane)

        #-------------------- READ PLANE BUTTON ----------------------#

        load_plane = qt.QLabel("Load the file with the plane you saved.")
        buttonFrame.layout().addWidget(load_plane)
        read = qt.QPushButton("Load plane")
        buttonFrame.layout().addWidget(read)
        read.connect('clicked(bool)', self.readPlane)

        #-------------------- Add vertical spacer ----------------------#
        self.layout.addStretch(1)

        #-------------------- onCloseScene ----------------------#
        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)


    def redPlaneCheckBoxClicked(self):
        self.logic.onCheckBoxClicked('red', self.red_plane_box, self.radio_red_Neg)

    def yellowPlaneCheckBoxClicked(self):
        self.logic.onCheckBoxClicked('yellow', self.yellow_plane_box, self.radio_yellow_Neg)

    def greenPlaneCheckBoxClicked(self):
        self.logic.onCheckBoxClicked('green', self.green_plane_box,  self.radio_green_Neg)

    def savePlane(self):
        self.logic.getCoord()
        self.logic.saveFunction()

    def readPlane(self):
        self.logic.readPlaneFunction(self.red_plane_box, self.yellow_plane_box, self.green_plane_box)

    def UndoButtonClicked(self):
        for key,value in self.dictionnaryModel.iteritems():
            model = slicer.mrmlScene.GetNodeByID(key)
            model.SetAndObservePolyData(value)

    def onCloseScene(self, obj, event):
        globals()["EasyClip"] = slicer.util.reloadScriptedModule("EasyClip")
        if self.image:
            self.image.__del__()

    def onComputeBox(self):
        #--------------------------- Box around the model --------------------------#
        self.image = self.logic.computeBoxFunction(self.image)

    def ClippingButtonClicked(self):
        self.logic.initializePlane()
        self.logic.getCoord()
        self.dictionnaryModel = self.logic.clipping(self.red_plane_box.isChecked(),
                                                    self.radio_red_Neg.isChecked(),
                                                    self.radio_red_Pos.isChecked(),
                                                    self.yellow_plane_box.isChecked(),
                                                    self.radio_yellow_Neg.isChecked(),
                                                    self.radio_yellow_Pos.isChecked(),
                                                    self.green_plane_box.isChecked(),
                                                    self.radio_green_Neg.isChecked(),
                                                    self.radio_green_Pos.isChecked())
class EasyClipLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.ColorNodeCorrespondence = {'red': 'vtkMRMLSliceNodeRed',
                                        'yellow': 'vtkMRMLSliceNodeYellow',
                                        'green': 'vtkMRMLSliceNodeGreen'}

    def onCheckBoxClicked(self, colorPlane, checkBox, radioButton ):
        slice = slicer.util.getNode(self.ColorNodeCorrespondence[colorPlane])
        print "Slice test", slice
        if checkBox.isChecked():
            slice.SetWidgetVisible(True)
            radioButton.setChecked(True)
        else:
            slice.SetWidgetVisible(False)

    def initializePlane(self):
        # Red Plane Definition
        self.redslice = slicer.util.getNode('vtkMRMLSliceNodeRed')
        print self.redslice
        self.matRed = self.redslice.GetSliceToRAS()
        print self.matRed

        self.matRed_init = numpy.matrix([[-1,0,0,0],
                                         [0,1,0,0],
                                         [0,0,1,0],
                                         [0,0,0,1]])


        # Yellow Plane Definition
        self.yellowslice = slicer.util.getNode('vtkMRMLSliceNodeYellow')
        self.matYellow = self.yellowslice.GetSliceToRAS()
        print self.matYellow

        self.matYellow_init = numpy.matrix([[0,0,1,0],
                                            [-1,0,0,0],
                                            [0,1,0,0],
                                            [0,0,0,1]])


        # Green Plane Definition
        self.greenslice = slicer.util.getNode('vtkMRMLSliceNodeGreen')
        self.matGreen = self.greenslice.GetSliceToRAS()
        print self.matGreen

        self.matGreen_init = numpy.matrix([[-1,0,0,0],
                                           [0,0,1,0],
                                           [0,1,0,0],
                                           [0,0,0,1]])

        #---------------------- Coefficient ----------------------#
        # Definition of the coefficient to determine the plane equation
        self.a_red = 0
        self.b_red = 0
        self.c_red = 0
        self.d_red = 0

        self.a_yellow = 0
        self.b_yellow = 0
        self.c_yellow = 0
        self.d_yellow = 0

        self.a_green = 0
        self.b_green = 0
        self.c_green = 0
        self.d_green = 0

        # The Red Slice is the first slice determined on Slicer.
        # The others are defined from a transformation matrix applied on this one (RED SLICE)
        # Normal vector to the Red slice:
        self.n_vector = numpy.matrix([[0], [0], [1], [1]])

        # point on the Red slice:
        self.A = numpy.matrix([[0], [0], [0], [1]])

    def computeBoxFunction(self, image):
        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        for i in range(3, numNodes):
            elements = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode" )
            print elements.GetName()
        node = slicer.util.getNode(elements.GetName())
        polydata = node.GetPolyData()
        bound = polydata.GetBounds()
        print "bound", bound

        dimX = bound[1]-bound[0]
        dimY = bound[3]-bound[2]
        dimZ = bound[5]-bound[4]

        print "dimension X :", dimX
        print "dimension Y :", dimY
        print "dimension Z :", dimZ

        dimX = dimX + 10
        dimY = dimY + 20
        dimZ = dimZ + 20

        center = polydata.GetCenter()
        print "Center polydata :", center

        # Creation of an Image
        image = sitk.Image(int(dimX), int(dimY), int(dimZ), sitk.sitkInt16)

        dir = (-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0)
        image.SetDirection(dir)

        spacing = (1,1,1)
        image.SetSpacing(spacing)

        tab = [-center[0]+dimX/2,-center[1]+dimY/2,center[2]-dimZ/2]
        print tab
        image.SetOrigin(tab)


        writer = sitk.ImageFileWriter()
        tempPath = slicer.app.temporaryPath
        filename = "Box.nrrd"
        filenameFull=os.path.join(tempPath, filename)
        print filenameFull
        writer.SetFileName(str(filenameFull))
        writer.Execute(image)


        slicer.util.loadVolume(filenameFull)

        #------------------------ Slice Intersection Visibility ----------------------#
        numDisplayNode = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelDisplayNode")
        for i in range (3,numDisplayNode):
            slice = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelDisplayNode" )
            slice.SetSliceIntersectionVisibility(1)

        return image


    def getCoord(self):
        #---------------------- RED SLICE -----------------------#
        # Matrix with the elements of SliceToRAS
        self.m_Red = numpy.matrix([[self.matRed.GetElement(0,0), self.matRed.GetElement(0,1), self.matRed.GetElement(0,2), self.matRed.GetElement(0,3)],
                                   [self.matRed.GetElement(1,0), self.matRed.GetElement(1,1), self.matRed.GetElement(1,2), self.matRed.GetElement(1,3)],
                                   [self.matRed.GetElement(2,0), self.matRed.GetElement(2,1), self.matRed.GetElement(2,2), self.matRed.GetElement(2,3)],
                                   [self.matRed.GetElement(3,0), self.matRed.GetElement(3,1), self.matRed.GetElement(3,2), self.matRed.GetElement(3,3)]])



        # #---------------------- YELLOW SLICE ----------------------#
        #
        # # Matrix with the elements of SliceToRAS
        self.m_Yellow = numpy.matrix([[self.matYellow.GetElement(0,0), self.matYellow.GetElement(0,1), self.matYellow.GetElement(0,2), self.matYellow.GetElement(0,3)],
                                      [self.matYellow.GetElement(1,0), self.matYellow.GetElement(1,1), self.matYellow.GetElement(1,2), self.matYellow.GetElement(1,3)],
                                      [self.matYellow.GetElement(2,0), self.matYellow.GetElement(2,1), self.matYellow.GetElement(2,2), self.matYellow.GetElement(2,3)],
                                      [self.matYellow.GetElement(3,0), self.matYellow.GetElement(3,1), self.matYellow.GetElement(3,2), self.matYellow.GetElement(3,3)]])

        #
        # #---------------------- GREEN SLICE ----------------------#
        # # Matrix with the elements of SliceToRAS
        self.m_Green = numpy.matrix([[self.matGreen.GetElement(0,0), self.matGreen.GetElement(0,1), self.matGreen.GetElement(0,2), self.matGreen.GetElement(0,3)],
                                     [self.matGreen.GetElement(1,0), self.matGreen.GetElement(1,1), self.matGreen.GetElement(1,2), self.matGreen.GetElement(1,3)],
                                     [self.matGreen.GetElement(2,0), self.matGreen.GetElement(2,1), self.matGreen.GetElement(2,2), self.matGreen.GetElement(2,3)],
                                     [self.matGreen.GetElement(3,0), self.matGreen.GetElement(3,1), self.matGreen.GetElement(3,2), self.matGreen.GetElement(3,3)]])

        #------------------- PLAN -----------------#

        # AXES FOR THE PLAN :

        #           |z
        #           |
        #           |________y
        #          /
        #         /
        #        /x

        # YELLOW PLAN : the equation is the coordinates on the x axis
        # GREEN PLAN : the equation is the coordinates on the y axis
        # RED PLAN : the equation is the coordinates on the z axis

        # RED PLAN:
        self.n_NewRedPlan = self.m_Red * self.n_vector
        print "n : \n", self.n_NewRedPlan

        self.A_NewRedPlan = self.m_Red * self.A
        print "A : \n", self.A_NewRedPlan

        self.a_red = self.n_NewRedPlan[0]
        self.b_red = self.n_NewRedPlan[1]
        self.c_red = self.n_NewRedPlan[2]
        self.d_red = self.n_NewRedPlan[0]*self.A_NewRedPlan[0] + self.n_NewRedPlan[1]*self.A_NewRedPlan[1] + self.n_NewRedPlan[2]*self.A_NewRedPlan[2]

        print "Red plan equation : \n", self.a_red ,"* x + ", self.b_red , "* y + ", self.c_red , "* z + ", self.d_red ," = 0 "

        # # YELLOW PLAN:
        self.n_NewYellowPlan = self.m_Yellow * self.n_vector
        print "n : \n", self.n_NewYellowPlan

        self.A_NewYellowPlan = self.m_Yellow * self.A
        print "A : \n", self.A_NewYellowPlan

        self.a_yellow = self.n_NewYellowPlan[0]
        self.b_yellow = self.n_NewYellowPlan[1]
        self.c_yellow = self.n_NewYellowPlan[2]
        self.d_yellow = self.n_NewYellowPlan[0]*self.A_NewYellowPlan[0] + self.n_NewYellowPlan[1]*self.A_NewYellowPlan[1]+self.n_NewYellowPlan[2]*self.A_NewYellowPlan[2]

        print "Yellow plan equation : \n", self.a_yellow, "* x + ", self.b_yellow, "* y + ", self.c_yellow, "* z + ", self.d_yellow," = 0 "

        # GREEN PLAN:
        self.n_NewGreenPlan = self.m_Green * self.n_vector
        print "n : \n", self.n_NewGreenPlan

        self.A_NewGreenPlan = self.m_Green * self.A
        print "A : \n", self.A_NewGreenPlan

        self.a_green = self.n_NewGreenPlan[0]
        self.b_green = self.n_NewGreenPlan[1]
        self.c_green = self.n_NewGreenPlan[2]
        self.d_green = self.n_NewGreenPlan[0]*self.A_NewGreenPlan[0] + self.n_NewGreenPlan[1]*self.A_NewGreenPlan[1] + self.n_NewGreenPlan[2]*self.A_NewGreenPlan[2]

        print "Green plan equation : \n", self.a_green, "* x + ", self.b_green, "* y + ", self.c_green, "* z + ", self.d_green," = 0 "


    def clipping(self,
                 red_plane_boxState,
                 radio_red_NegState,
                 radio_red_PosState,
                 yellow_plane_boxState,
                 radio_yellow_NegState,
                 radio_yellow_PosState,
                 green_plane_boxState,
                 radio_green_NegState,
                 radio_green_PosState):

        # Clipping in the direction of the normal vector
        self.plane_red = vtk.vtkPlane()
        self.plane_yellow = vtk.vtkPlane()
        self.plane_green = vtk.vtkPlane()

        self.planeCollection = vtk.vtkPlaneCollection()

        #Condition for the red plane
        print self.m_Red
        print self.n_NewRedPlan

        print self.A_NewRedPlan
        self.n_NewRedPlan1 = self.n_NewRedPlan
        self.n_NewGreenPlan1 = self.n_NewGreenPlan
        self.n_NewYellowPlan1 = self.n_NewYellowPlan

        self.n_NewRedPlan1[0] = self.n_NewRedPlan[0] - self.A_NewRedPlan[0]
        self.n_NewRedPlan1[1] = self.n_NewRedPlan[1] - self.A_NewRedPlan[1]
        self.n_NewRedPlan1[2] = self.n_NewRedPlan[2] - self.A_NewRedPlan[2]
        print self.n_NewRedPlan1

        if red_plane_boxState:
            if radio_red_NegState:
                self.plane_red.SetOrigin(self.A_NewRedPlan[0], self.A_NewRedPlan[1], self.A_NewRedPlan[2])
                if self.n_NewRedPlan1[2] >= 0:
                    self.plane_red.SetNormal(-self.n_NewRedPlan1[0], -self.n_NewRedPlan1[1], -self.n_NewRedPlan1[2])
                if self.n_NewRedPlan1[2] < 0:
                    self.plane_red.SetNormal(self.n_NewRedPlan1[0], self.n_NewRedPlan1[1], self.n_NewRedPlan1[2])
                self.planeCollection.AddItem(self.plane_red)
                print self.plane_red

            if radio_red_PosState:
                self.plane_red.SetOrigin(self.A_NewRedPlan[0], self.A_NewRedPlan[1], self.A_NewRedPlan[2])
                if self.n_NewRedPlan1[2] >= 0:
                    self.plane_red.SetNormal(self.n_NewRedPlan1[0], self.n_NewRedPlan1[1], self.n_NewRedPlan1[2])
                if self.n_NewRedPlan1[2] < 0:
                    self.plane_red.SetNormal(-self.n_NewRedPlan1[0], -self.n_NewRedPlan1[1], -self.n_NewRedPlan1[2])
                self.planeCollection.AddItem(self.plane_red)
                print self.plane_red

        #Condition for the yellow plane
        print self.m_Yellow
        print self.n_NewYellowPlan

        print self.A_NewYellowPlan
        self.n_NewYellowPlan1[0] = self.n_NewYellowPlan[0] - self.A_NewYellowPlan[0]
        self.n_NewYellowPlan1[1] = self.n_NewYellowPlan[1] - self.A_NewYellowPlan[1]
        self.n_NewYellowPlan1[2] = self.n_NewYellowPlan[2] - self.A_NewYellowPlan[2]
        print self.n_NewYellowPlan1

        if yellow_plane_boxState:
            if radio_yellow_NegState:
                self.plane_yellow.SetOrigin(self.A_NewYellowPlan[0], self.A_NewYellowPlan[1], self.A_NewYellowPlan[2])
                if self.n_NewYellowPlan1[0] >= 0:
                    self.plane_yellow.SetNormal(-self.n_NewYellowPlan1[0], -self.n_NewYellowPlan1[1], -self.n_NewYellowPlan1[2])
                if self.n_NewYellowPlan1[0] < 0:
                    self.plane_yellow.SetNormal(self.n_NewYellowPlan1[0], self.n_NewYellowPlan1[1], self.n_NewYellowPlan1[2])
                self.planeCollection.AddItem(self.plane_yellow)
                print self.plane_yellow

            if radio_yellow_PosState:
                self.plane_yellow.SetOrigin(self.A_NewYellowPlan[0], self.A_NewYellowPlan[1], self.A_NewYellowPlan[2])
                if self.n_NewYellowPlan1[0] >= 0:
                    self.plane_yellow.SetNormal(self.n_NewYellowPlan1[0], self.n_NewYellowPlan1[1], self.n_NewYellowPlan1[2])
                if self.n_NewYellowPlan1[0] < 0:
                    self.plane_yellow.SetNormal(-self.n_NewYellowPlan1[0], -self.n_NewYellowPlan1[1], -self.n_NewYellowPlan1[2])
                self.planeCollection.AddItem(self.plane_yellow)
                print self.plane_yellow

        #Condition for the green plane
        print self.m_Green
        print self.n_NewGreenPlan

        print self.A_NewGreenPlan
        self.n_NewGreenPlan1[0] = self.n_NewGreenPlan[0] - self.A_NewGreenPlan[0]
        self.n_NewGreenPlan1[1] = self.n_NewGreenPlan[1] - self.A_NewGreenPlan[1]
        self.n_NewGreenPlan1[2] = self.n_NewGreenPlan[2] - self.A_NewGreenPlan[2]
        print self.n_NewGreenPlan1

        if green_plane_boxState:
            if radio_green_NegState:
                self.plane_green.SetOrigin(self.A_NewGreenPlan[0], self.A_NewGreenPlan[1], self.A_NewGreenPlan[2])
                if self.n_NewGreenPlan1[1] >= 0:
                    self.plane_green.SetNormal(-self.n_NewGreenPlan1[0], -self.n_NewGreenPlan1[1], -self.n_NewGreenPlan1[2])
                if self.n_NewGreenPlan1[1] < 0:
                    self.plane_green.SetNormal(self.n_NewGreenPlan1[0], self.n_NewGreenPlan1[1], self.n_NewGreenPlan1[2])
                self.planeCollection.AddItem(self.plane_green)
                print self.plane_green

            if radio_green_PosState:
                self.plane_green.SetOrigin(self.A_NewGreenPlan[0], self.A_NewGreenPlan[1], self.A_NewGreenPlan[2])
                if self.n_NewGreenPlan1[1] > 0:
                    self.plane_green.SetNormal(self.n_NewGreenPlan1[0], self.n_NewGreenPlan1[1], self.n_NewGreenPlan1[2])
                if self.n_NewGreenPlan1[1] < 0:
                    self.plane_green.SetNormal(-self.n_NewGreenPlan1[0], -self.n_NewGreenPlan1[1], -self.n_NewGreenPlan1[2])
                self.planeCollection.AddItem(self.plane_green)
                print self.plane_green


        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        self.dictionnaryModel = dict()
        self.dictionnaryModel.clear()


        for i in range(3, numNodes):
            mh = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            self.model = slicer.util.getNode(mh.GetName())
            print mh.GetName()

            self.dictionnaryModel[self.model.GetID()]=self.model.GetPolyData()

            self.polyData = self.model.GetPolyData()


            PolyAlgorithm = vtk.vtkClipClosedSurface()
            PolyAlgorithm.SetInputData(self.polyData)

            clipper = vtk.vtkClipClosedSurface()
            clipper.SetClippingPlanes(self.planeCollection)
            clipper.SetInputConnection(PolyAlgorithm.GetOutputPort())
            clipper.SetGenerateFaces(1)
            clipper.SetScalarModeToLabels()
            clipper.Update()
            polyDataNew = clipper.GetOutput()
            self.model.SetAndObservePolyData(polyDataNew)
        return self.dictionnaryModel


    def saveFunction(self):
        filename = qt.QFileDialog.getSaveFileName(parent=self,caption='Save file')
        fichier = open(filename, "w")
        fichier.write("SliceToRAS Red Slice: \n")
        fichier.write(str(self.m_Red) + '\n')
        fichier.write('\n')

        fichier.write("SliceToRAS Yellow Slice: \n")
        fichier.write(str(self.m_Yellow) + '\n')
        fichier.write('\n')

        fichier.write("SliceToRAS Green Slice: \n")
        fichier.write(str(self.m_Green) + '\n')
        fichier.write('\n')

        fichier.write("Coefficients for the Red plane: \n")
        fichier.write("a:" + str(self.a_red) + '\n')
        fichier.write("b:" + str(self.b_red) + '\n')
        fichier.write("c:" + str(self.c_red) + '\n')
        fichier.write("d:" + str(self.d_red) + '\n')

        fichier.write('\n')
        fichier.write("Coefficients for the Yellow plane: \n")
        fichier.write("a:" + str(self.a_yellow) + '\n')
        fichier.write("b:" + str(self.b_yellow) + '\n')
        fichier.write("c:" + str(self.c_yellow) + '\n')
        fichier.write("d:" + str(self.d_yellow) + '\n')

        fichier.write('\n')
        fichier.write("Coefficients for the Green plane: \n")
        fichier.write("a:" + str(self.a_green) + '\n')
        fichier.write("b:" + str(self.b_green) + '\n')
        fichier.write("c:" + str(self.c_green) + '\n')
        fichier.write("d:" + str(self.d_green) + '\n')


        fichier.close()

    def readPlaneFunction(self, red_plane_box, yellow_plane_box, green_plane_box):
        filename = qt.QFileDialog.getOpenFileName(parent=self,caption='Open file')
        print 'filename:', filename
        fichier2 = open(filename, 'r')
        fichier2.readline()
        NodeRed = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        matRed = NodeRed.GetSliceToRAS()

        for i in range(0, 4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matRed.SetElement(i, j, float(items[j]))


        print matRed
        compare_red = 0
        self.matRed_init = numpy.matrix([[-1,0,0,0],
                                         [0,1,0,0],
                                         [0,0,1,0],
                                         [0,0,0,1]])
        print "self.matRed_init", self.matRed_init
        for i in range(0,4):
            for j in range(0,4):
                if matRed.GetElement(i,j) == self.matRed_init[i,j]:
                    compare_red = compare_red + 1

        print compare_red

        if compare_red != 16:
            self.redslice = slicer.util.getNode('vtkMRMLSliceNodeRed')
            if red_plane_box.isChecked():
                red_plane_box.setChecked(False)
                self.redslice.SetWidgetVisible(False)
            red_plane_box.setChecked(True)
            # widget.redPlaneCheckBoxClicked()
            self.redslice.SetWidgetVisible(True)

        fichier2.readline()
        fichier2.readline()


        self.matYellow_init = numpy.matrix([[0,0,1,0],
                                            [-1,0,0,0],
                                            [0,1,0,0],
                                            [0,0,0,1]])
        NodeYellow = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
        matYellow = NodeYellow.GetSliceToRAS()
        for i in range(0, 4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matYellow.SetElement(i, j, float(items[j]))


        print matYellow

        compare_yellow = 0
        for i in range(0,4):
            for j in range(0,4):
                if matYellow.GetElement(i,j) == self.matYellow_init[i,j]:
                    compare_yellow = compare_yellow + 1

        print compare_yellow

        if compare_yellow != 16:
            self.yellowslice = slicer.util.getNode('vtkMRMLSliceNodeYellow')
            if yellow_plane_box.isChecked():
                yellow_plane_box.setChecked(False)
                self.yellowslice.SetWidgetVisible(False)

            yellow_plane_box.setChecked(True)
            # self.yellowPlaneCheckBoxClicked()
            self.yellowslice.SetWidgetVisible(True)

        fichier2.readline()
        fichier2.readline()

        self.matGreen_init = numpy.matrix([[-1,0,0,0],
                                           [0,0,1,0],
                                           [0,1,0,0],
                                           [0,0,0,1]])
        NodeGreen = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
        matGreen = NodeGreen.GetSliceToRAS()
        for i in range (0,4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matGreen.SetElement(i, j, float(items[j]))


        print matGreen


        compare_green = 0
        for i in range(0,4):
            for j in range(0,4):
                if matGreen.GetElement(i,j) == self.matGreen_init[i,j]:
                    compare_green = compare_green + 1

        print compare_green

        if compare_green != 16:
            self.greenslice = slicer.util.getNode('vtkMRMLSliceNodeGreen')
            if green_plane_box.isChecked():
                green_plane_box.setChecked(False)
                self.greenslice.SetWidgetVisible(False)

            green_plane_box.setChecked(True)
            # self.greenPlaneCheckBoxClicked()
            self.greenslice.SetWidgetVisible(True)

        fichier2.close()

class EasyClipTest(ScriptedLoadableModuleTest):
    def setUp(self):
        # reset the state - clear scene
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        # run all tests needed
        self.setUp()
        self.test_EasyClip()

    def test_EasyClip(self):

        self.delayDisplay("Starting the test")
        ###################################################################################################
        #                                        Loading some data                                        #
        ###################################################################################################
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=167065', 'model.vtk', slicer.util.loadModel),
            )

        for url,name,loader in downloads:
          filePath = slicer.app.temporaryPath + '/' + name
          if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
            print('Requesting download %s from %s...\n' % (name, url))
            urllib.urlretrieve(url, filePath)
          if loader:
            print('Loading %s...\n' % (name,))
            loader(filePath)
        self.delayDisplay('Finished with download and loading\n')


        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()

        self.delayDisplay('Model loaded')

        ###################################################################################################
        #                                 Initialize Plane Position                                       #
        ###################################################################################################

        redslice = slicer.util.getNode('vtkMRMLSliceNodeRed')
        yellowslice = slicer.util.getNode('vtkMRMLSliceNodeYellow')
        greenslice = slicer.util.getNode('vtkMRMLSliceNodeGreen')
        # print redslice, yellowslice, greenslice
        self.delayDisplay('Planes are displayed!')

        #Put planes at specific places
        matRed = redslice.GetSliceToRAS()

        matRed.SetElement(0,3,0)
        matRed.SetElement(1,3,0)
        matRed.SetElement(2,3,8)
        redslice.SetWidgetVisible(True)
        print matRed

        matYellow = yellowslice.GetSliceToRAS()
        matYellow.SetElement(0,3,-3)
        matYellow.SetElement(1,3,0)
        matYellow.SetElement(2,3,0)
        print matYellow
        yellowslice.SetWidgetVisible(True)

        matGreen = greenslice.GetSliceToRAS()
        matGreen.SetElement(0,3,0)
        matGreen.SetElement(1,3,-9)
        matGreen.SetElement(2,3,0)
        print matGreen
        greenslice.SetWidgetVisible(True)

        self.delayDisplay('planes are placed!')

        image = None

        logic = EasyClipLogic()
        image = logic.computeBoxFunction(image)
        logic.initializePlane()
        logic.getCoord()
        logic.clipping(True, False, True, False, False, False, False, False, False)


        print 'DONE'

        self.delayDisplay('Test passed!')

