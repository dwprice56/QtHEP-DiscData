#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017 David Price
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, xml.dom, xml.dom.minidom as minidom

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

import XMLHelpers

class Crop(object):
    """ Store cropping information.
    """

    XMLNAME = 'Crop'

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: top {}, bottom {}, left {}, right {}' \
            .format(self.XMLNAME, self.top, self.bottom, self.left, self.right)

    def clear(self):
        """ Set all object members to their initial values.
        """

        self.top = 0
        self.bottom = 0
        self.left = 0
        self.right = 0

    @property
    def displayString(self):
        """ Returns the crop information as a formatted string.
        """
        return '{}/{}/{}/{}'.format(self.top, self.bottom, self.left, self.right)

    @property
    def parent(self):
        return self.__parent

    def copy(self, cropObject):
        """ Copy the elements from another Crop object.
        """

        assert(isinstance(cropObject, Crop))

        self.top = cropObject.top
        self.bottom = cropObject.bottom
        self.left = cropObject.left
        self.right = cropObject.right

    def fromXML(self, element, defaultCrop=None):
        """ Read the object from an XML file.
        """

        self.clear()

        if (defaultCrop):
            self.top = XMLHelpers.GetXMLAttributeAsInt(element, 'Top', defaultCrop.top)
            self.bottom = XMLHelpers.GetXMLAttributeAsInt(element, 'Bottom', defaultCrop.bottom)
            self.left = XMLHelpers.GetXMLAttributeAsInt(element, 'Left', defaultCrop.left)
            self.right = XMLHelpers.GetXMLAttributeAsInt(element, 'Right', defaultCrop.right)
        else:
            self.top = XMLHelpers.GetXMLAttributeAsInt(element, 'Top', 0)
            self.bottom = XMLHelpers.GetXMLAttributeAsInt(element, 'Bottom', 0)
            self.left = XMLHelpers.GetXMLAttributeAsInt(element, 'Left', 0)
            self.right = XMLHelpers.GetXMLAttributeAsInt(element, 'Right', 0)

    def set(self, top, bottom, left, right):
        """ Set the attributes.
        """

        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """

        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('Top', str(self.top))
        element.setAttribute('Bottom', str(self.bottom))
        element.setAttribute('Left', str(self.left))
        element.setAttribute('Right', str(self.right))

        return element

class AutoCrop(Crop):
    """ Store automatic cropping information.
    """

    XMLNAME = 'AutoCrop'

    def __init__(self, parent):
        super().__init__(parent)

class CustomCrop(Crop):
    """ Store the custom cropping information.
    """

    XMLNAME = 'CustomCrop'

    PROCESS_DEFAULT   = "Default"
    PROCESS_AUTOMATIC = "Automatic"
    PROCESS_CUSTOM    = "Custom"
    PROCESS_CHOICES   = [PROCESS_DEFAULT, PROCESS_AUTOMATIC, PROCESS_CUSTOM]

    def __init__(self, parent):
        super().__init__(parent)

        self.processChoice = self.PROCESS_DEFAULT

    def __str__(self):
        return '{}: processChoice="{}", top {}, bottom {}, left {}, right {}' \
            .format(self.XMLNAME, self.processChoice, self.top, self.bottom, self.left, self.right)

    def clear(self):
        """ Set all object members to their initial values.
        """
        super().clear()

        self.processChoice = self.PROCESS_DEFAULT

    def copy(self, cropObject):
        """ Copy the elements from another Crop object.
        """
        super().copy(cropObject)

        # This is neccessary because cropObject might be an instance of Crop or AutoCrop.
        if (isinstance(cropObject, CustomCrop)):
            self.processChoice = cropObject.processChoice
        else:
            self.processChoice = self.PROCESS_DEFAULT

    def fromXML(self, element, defaultCrop=None):
    # def fromXML(self, element, customCrop):
        """ Read the object from an XML file.
        """
        super().fromXML(element, defaultCrop)

        self.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'ProcessChoice',
            self.PROCESS_DEFAULT, self.PROCESS_CHOICES)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = super().toXML(doc, parentElement)

        element.setAttribute('ProcessChoice', self.processChoice)

        return element

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    crop = Crop(None)
    autoCrop = AutoCrop(None)
    customCrop = CustomCrop(None)

    print ()

    print (crop)
    print ()
    print ()

    print (autoCrop)
    print ()
    print ()

    print (customCrop)
    print ()
    print ()

    # ********************************************************
    filename = 'TestFiles/TestCrop.xml'
    elementName = 'TestCrop'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == Crop.XMLNAME):
                crop.fromXML(childNode)
                print (crop)
            else:
                print ('Can''t find element "{}" in "{}".'.format(Crop.XMLNAME, filename))
        print ()

    # ********************************************************
    filename = 'TestFiles/TestAutoCrop.xml'
    elementName = 'TestAutoCrop'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == AutoCrop.XMLNAME):
                autoCrop.fromXML(childNode)
                print (autoCrop)
            else:
                print ('Can''t find element "{}" in "{}".'.format(AutoCrop.XMLNAME, filename))
        print ()

    # ********************************************************
    filename = 'TestFiles/TestCustomCrop.xml'
    elementName = 'TestCustomCrop'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == CustomCrop.XMLNAME):
                customCrop.fromXML(childNode)
                print (customCrop)
            else:
                print ('Can''t find element "{}" in "{}".'.format(CustomCrop.XMLNAME, filename))
        print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestCrop', None)
    parentElement = doc.documentElement

    crop.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestCrop.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestAutoCrop', None)
    parentElement = doc.documentElement

    autoCrop.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestAutoCrop.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestCustomCrop', None)
    parentElement = doc.documentElement

    customCrop.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestCustomCrop.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()

    # ********************************************************
    print ('Set, copy, clear test')
    print (crop)
    print (autoCrop)
    print ()

    autoCrop.set(10, 20, 30, 40)
    print (crop)
    print (autoCrop)
    print ()

    crop.copy(autoCrop)
    print (crop)
    print (autoCrop)
    print ()

    autoCrop.clear()
    print (crop)
    print (autoCrop)
    print ()
