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

# import sys
# from collections import MutableSequence
#
# sys.path.insert(0, '/home/dave/QtProjects/Helpers')
#
# import XMLHelpers
# from Helpers import DurationAsTimedelta

class Cells(object):

    XMLNAME = 'Cells'

    def __init__(self, parent):
        self.__parent = parent

        self.clear()

    def __str__(self):
        return '{}: {}:{}'.format(self.XMLNAME, self.first, self.last)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.first = 0
        self.last = 0

    @property
    def range(self):
        return '{}:{}'.format(self.first, self.last)

    @property
    def parent(self):
        return self.__parent

    def FromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.first = XMLHelpers.GetXMLAttributeAsInt(element, 'First', 0)
        self.last = XMLHelpers.GetXMLAttributeAsInt(element, 'Last', 0)

    def ToXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('First', str(self.first))
        element.setAttribute('Last', str(self.last))

        return element

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    cells = Cells(None)
    print (cells)
