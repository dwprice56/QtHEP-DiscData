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

import datetime, sys
from collections import MutableSequence

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

import XMLHelpers
from Helpers import DurationAsTimedelta

class Chapter(object):

    XMLNAME = 'Chapter'

    def __init__(self, parent):
        self.__parent = parent

        self.cells = [0, 0]
        self.clear()

        self.shortChapterDuration = datetime.timedelta(seconds=5)

    def __str__(self):
        return '{} {}: cells {}:{}, duration {}, blocks {}, name "{}"'.format(self.XMLNAME,
            self.chapterNumber, self.cells[0], self.cells[1],
            self.duration, self.blocks, self.title)

    def clear(self):
        """ Set all object members to their initial values.
        """

        self.chapterNumber = 0

        self.cells[0], self.cells[1] = (0, 0)
        self.blocks = 0
        self.duration = ''
        self.title = ''

    def cellsString(self):
        return '{}:{}'.format(self.cells[0], self.cells[1])

    @property
    def defaultName(self):


        # TODO The default name should be the chapter number plus the offset first chapter number (a state value)
        #      Maybe the offset should be stored in the Chapters() object.
        #      But what about decoupling the Chapter() object from state?


        return 'Chapter {}'.format(self.chapterNumber)
        # return 'Chapter {}'.format(self.chapterNumber + self.parent.parent.firstChapterNumber - 1)

    @property
    def durationAsTimedelta(self):
        return DurationAsTimedelta(self.duration)

    @property
    def hashString(self):
        """ Generate a string used to update the hash; the string is based on
            the object contents.

            Omit duration; it seems to be a calculated field subject to rounding
            errors.
        """

        return 'Chapter Number: {}, First Cell: {}, Last Cell: {}, Blocks: {}'.format(
            self.chapterNumber,
            self.cells[0],
            self.cells[1],
            self.blocks
        )

    @property
    def isDefaultName(self):
        """ Return True if the chapter name is the default name.
        """

        return (self.title == self.defaultName)

    @property
    def isShortChapter(self):
        """ Is this chapter <= the short chapter length of 5 seconds?
        """

        return (self.durationAsTimedelta <= self.shortChapterDuration)

    @property
    def parent(self):
        return self.__parent

    def FromXML(self, element):
        """ Read the object from an XML file.
        """

        self.clear()

        self.chapterNumber = XMLHelpers.GetXMLAttributeAsInt(element, 'ChapterNumber', 0)

        self.cells[0] = XMLHelpers.GetXMLAttributeAsInt(element, 'FirstCell', 0)
        self.cells[1] = XMLHelpers.GetXMLAttributeAsInt(element, 'LastCell', 0)
        self.blocks = XMLHelpers.GetXMLAttributeAsInt(element, 'Blocks', 0)
        self.duration = XMLHelpers.GetXMLAttribute(element, 'Duration', '').strip()
        self.title = XMLHelpers.GetXMLAttribute(element, 'Title', self.defaultName).strip()

    def Parse(self, line):
        """ Extract the chapter information into the object memebers from
            Handbrakes output.
        """

        parms = line[6:].split(': ')

        self.chapterNumber = int(parms[0])
        parms = parms[1].split(', ')

        for parm in parms:
            if (parm.startswith('cells')):
                cells = parm.split()[1].split('->')
                self.cells[0] = int(cells[0])
                self.cells[1] = int(cells[1])

            elif (parm.endswith('blocks')):
                self.blocks = int(parm.split()[0])

            elif (parm.startswith('duration')):
                self.duration = parm.split()[1]

        self.SetDefaultName()

    def SetDefaultName(self):
        self.title = self.defaultName

    def SetName(self, name):
        self.title = name

    def ToXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """

        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('ChapterNumber', str(self.chapterNumber))

        element.setAttribute('FirstCell', str(self.cells[0]))
        element.setAttribute('LastCell', str(self.cells[1]))
        element.setAttribute('Blocks', str(self.blocks))
        element.setAttribute('Duration', self.duration)
        element.setAttribute('Title', self.title)

        return element

class Chapters(MutableSequence):
    """ Container for a list of Chapters.
    """

    XMLNAME = 'Chapters'

    PROCESS_MARKERS = "MARKERS"
    PROCESS_NAMES = "NAMES"
    PROCESS_NONE = "NONE"
    PROCESS_CHOICES = [PROCESS_MARKERS, PROCESS_NAMES, PROCESS_NONE]

    def __init__(self, parent):
        super(Chapters, self).__init__()

        self.__parent = parent

        self.processChoice = self.PROCESS_MARKERS

        self.chapters = []
        self.chaptersByChapterNumber = {}

        self.firstChapterNumber = 1

        self._lowestChapterNumber = 0
        self._highestChapterNumber = 0

    def __str__(self):
        return '{}: len: {}, processChoice="{}", FirstChapterNumber: {}, HighestChapterNumber: {}, ' \
            'LowestChapterNumber: {}'.format(self.XMLNAME, len(self.chapters), self.processChoice,
            self.firstChapterNumber, self._lowestChapterNumber, self._highestChapterNumber)

    # MutableSequence abstract methods
    # ==========================================================================
    def _refreshLowestHighestChapterNumbers(self):

        self._lowestChapterNumber = 0
        self._highestChapterNumber = 0

        for chapter in self.chapters:
            self._updateLowestHighestChapterNumbers(chapter)

    def _updateLowestHighestChapterNumbers(self, obj):
        """Support method for the MutableSequence abstract methods.

        Updates the _lowerChapterNumber and _highestChapterNumber.

        Raises a RuntimeError if a chapter number of less than one is found."""

        if (obj.chapterNumber < 1):
            raise RuntimeError('A chapter number, "{}", of less than one was encountered.'.format(obj.chapterNumber))

        if (self._lowestChapterNumber == 0):
            self._lowestChapterNumber = obj.chapterNumber
        elif (obj.chapterNumber < self._lowestChapterNumber):
            self._lowestChapterNumber = obj.chapterNumber

        if (self._highestChapterNumber == 0):
            self._highestChapterNumber = obj.chapterNumber
        elif (obj.chapterNumber > self._highestChapterNumber):
            self._highestChapterNumber = obj.chapterNumber

    def __getitem__(self, idx):
        return self.chapters[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, Chapter))

        self.chaptersByChapterNumber.pop(self.chapters[idx].chapterNumber)
        self.chapters[idx] = obj
        self.chaptersByChapterNumber[obj.chapterNumber] = obj

        self._refreshLowestHighestChapterNumbers()

    def __delitem__(self, idx):
        self.chaptersByChapterNumber.pop(self.chapters[idx].chapterNumber)
        del self.chapters[idx]

        self._refreshLowestHighestChapterNumbers()

    def __len__(self):
        return len(self.chapters)

    def insert(self, idx, obj):
        assert(isinstance(obj, Chapter))

        self.chapters.insert(idx, obj)
        self.chaptersByChapterNumber[obj.chapterNumber] = obj

        self._updateLowestHighestChapterNumbers(obj)
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.processChoice = self.PROCESS_MARKERS

        del self.chapters[:]
        self.chaptersByChapterNumber.clear()

        self._lowestChapterNumber = 0
        self._highestChapterNumber = 0

    @property
    def highestChapterNumber(self):
        return self._highestChapterNumber

    @property
    def lowestChapterNumber(self):
        return self._lowestChapterNumber

    @property
    def parent(self):
        return self.__parent

    def FromXML(self, element):
        """ Read the object from an XML file.
        """

        self.clear()

        self.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'ProcessChoice',
            self.PROCESS_MARKERS, self.PROCESS_CHOICES)

        self.firstChapterNumber = XMLHelpers.GetXMLAttributeAsInt(element, "FirstChapterNumber", 1)

        for childNode in element.childNodes:
            if (childNode.localName == Chapter.XMLNAME):

                chapter = Chapter(self)
                chapter.FromXML(childNode)
                self.append(chapter)            # highest, lowest chapter number set by append()

    def GetByChapterNumber(self, chapterNumber):
        """ Returns the chapter for a chapter number.
            Returns None if the requested chapter doesn't exist.
        """

        if (chapterNumber in self.chaptersByChapterNumber.keys()):
            return self.chaptersByChapterNumber[chapterNumber]

        return None

    def GetChapterNumbers(self):
        """ Return a list of chapter numbers.
        """
        chapterNumbers = []

        for chapter in self.chapters:
            chapterNumbers.append(str(chapter.chapterNumber))

        return chapterNumbers

    def HasChapterNumber(self, chapterNumber):
        """ Returns true/false if a track number exists.
        """
        if (chapterNumber in self.chaptersByChapterNumber.keys()):
            return True

        return False

    def InRange(self, chapterNumber):
        """ Is the chapter number in the range of available chapter numbers?
        """
        return (chapterNumber >= self._lowestChapterNumber and chapterNumber <= self._highestChapterNumber)

    def SetChapterName(self, chapterNumber, name):
        """ Sets the name for the specified chapter.
        """

        # TODO: handle invalid chapterNumber condition

        chapter = self.GetByChapterNumber(chapterNumber)
        if (chapter is not None):
            chapter.title = name

    def SetDefaultNames(self):
        """ Sets the chapter titles to "Chapter 1", "Chapter 2", etc.
        """
        for chapter in self.chapters:
            chapter.SetDefaultName()

    def ToXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        if (len(self.chapters) > 0):
            element = doc.createElement(self.XMLNAME)
            parentElement.appendChild(element)

            element.setAttribute('ProcessChoice', self.processChoice)

            element.setAttribute("FirstChapterNumber", str(self.firstChapterNumber))

            # These are "convenience" attributes for other applications that read the XML file.
            # They are ignored by self.FromXML().
            element.setAttribute('count', str(len(self.chapters)))
            element.setAttribute('lowestChapterNumber', str(self._lowestChapterNumber))
            element.setAttribute('highestChapterNumber', str(self._highestChapterNumber))

            for chapter in self.chapters:
                chapter.ToXML(doc, element)

            return element

        return None

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    chapters = Chapters(None)
    print (chapters)
    print ()

    lines = [
        '    + 1: cells 0->1, 147111 blocks, duration 00:05:05',
        '    + 2: cells 2->2, 177403 blocks, duration 00:06:45',
        '    + 3: cells 3->3, 234661 blocks, duration 00:08:48',
        '    + 4: cells 4->4, 200114 blocks, duration 00:07:22',
        '    + 5: cells 5->5, 270139 blocks, duration 00:09:53',
        '    + 6: cells 6->6, 283336 blocks, duration 00:10:17',
        '    + 7: cells 7->7, 303305 blocks, duration 00:10:57',
        '    + 8: cells 8->9, 177464 blocks, duration 00:06:34',
        '    + 9: cells 10->10, 184133 blocks, duration 00:06:43',
        '    + 10: cells 11->11, 315172 blocks, duration 00:11:34',
        '    + 11: cells 12->12, 145711 blocks, duration 00:05:29',
        '    + 12: cells 13->13, 287641 blocks, duration 00:10:39',
        '    + 13: cells 14->14, 158104 blocks, duration 00:05:24',
        '    + 14: cells 15->15, 20 blocks, duration 00:00:01'
    ]

    for line in lines:
        chapter = Chapter(chapters)
        chapter.Parse(line)
        chapters.append(chapter)

    print (chapters)
    for chapter in chapters:
        print (chapter)
    print ()

    # ********************************************************
    filename = 'TestFiles/TestChapters.xml'
    elementName = 'TestChapters'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == Chapters.XMLNAME):
                chapters.FromXML(childNode)
                print (chapters)
                for chapter in chapters:
                    print (chapter)
            else:
                print ('Can''t find element "{}" in "{}".'.format(Chapters.XMLNAME, filename))
        print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestChapters', None)
    parentElement = doc.documentElement

    chapters.ToXML(doc, parentElement)

    xmlFile = open('TestFiles/TestChapters.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
