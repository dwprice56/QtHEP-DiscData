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

import sys
from collections import MutableSequence

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

import XMLHelpers

class ChapterRangeEpisode(object):

    XMLNAME = 'ChapterRangeEpisode'

    def __init__(self, parent):
        self.__parent = parent

        self.clear()

    def __str__(self):
        return '{}: id={}, firstChapter {}, lastChapter {}, title {}' \
            .format(self.XMLNAME, id(self), self.firstChapter, self.lastChapter, self.title)

    def clear(self):
        """ Set all object members to their initial values.
        """

        self.firstChapter = 0
        self.lastChapter = 0
        self.title = ''

    @property
    def parent(self):
        return self.__parent

    def FromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.firstChapter = XMLHelpers.GetXMLAttributeAsInt(element, 'FirstChapter', 0)
        self.lastChapter = XMLHelpers.GetXMLAttributeAsInt(element, 'LastChapter', 0)
        self.title = XMLHelpers.GetXMLAttribute(element, 'Title', '').strip()

    def Set(self, firstChapter, lastChapter, title):
        """ Set the values for the object.
        """
        self.firstChapter = firstChapter
        self.lastChapter = lastChapter
        self.title = title

    def ToXML(self, doc, rootElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        rootElement.appendChild(element)

        element.setAttribute('FirstChapter', str(self.firstChapter))
        element.setAttribute('LastChapter', str(self.lastChapter))
        element.setAttribute('Title', self.title)

        return element

class ChapterRanges(MutableSequence):

    XMLNAME = 'ChapterRanges'

    PROCESS_ALL = 'ALL'
    PROCESS_RANGE = 'RANGE'
    PROCESS_EPISODES = 'EPISODES'
    PROCESS_CHOICES = [PROCESS_ALL, PROCESS_RANGE, PROCESS_EPISODES]

    def __init__(self, parent):
        self.__parent = parent

        self.processChoice = self.PROCESS_ALL

        self.firstChapter = 0
        self.lastChapter = 0

        self.episodes = []

    def __str__(self):
        s = '{}: len={}, processChoice={}, firstChapter={}, lastChapter={}'.format(self.XMLNAME,
            len(self.episodes), self.processChoice, self.firstChapter, self.lastChapter)

        return s

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.episodes[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, ChapterRangeEpisode))
        self.episodes[idx] = obj

    def __delitem__(self, idx):
        del self.episodes[idx]

    def __len__(self):
        return len(self.episodes)

    def insert(self, idx, obj):
        assert(isinstance(obj, ChapterRangeEpisode))
        self.episodes.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.processChoice = self.PROCESS_ALL

        self.firstChapter = 0
        self.lastChapter = 0

        del self.episodes[:]

    def clearEpisodes(self):
        """ Set range members (only) to their initial values.
        """
        del self.episodes[:]

    def clearRange(self):
        """ Set range members (only) to their initial values.
        """
        self.firstChapter = 0
        self.lastChapter = 0

    @property
    def parent(self):
        return self.__parent

    # def GetChoices(self):
    #     return self.parent.chapters.GetChoices()

    def AddEpisode(self, firstChapter, lastChapter, title):
        """ Add an episode to the list.  Return the new episode.
        """
        episode = ChapterRangeEpisode(self)
        episode.Set(firstChapter, lastChapter, title)
        self.append(episode)

        return episode

    def FromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.processChoice = XMLHelpers.GetXMLAttribute(element, 'RangeType', 0)
        self.firstChapter = XMLHelpers.GetXMLAttributeAsInt(element, 'FirstChapter', 0)
        self.lastChapter = XMLHelpers.GetXMLAttributeAsInt(element, 'LastChapter', 0)

        for childNode in element.childNodes:
            if (childNode.localName in [ChapterRangeEpisode.XMLNAME, 'ChapterRange', 'Episode']):

                episode = ChapterRangeEpisode(self)
                episode.FromXML(childNode)
                self.append(episode)

    def ToXML(self, doc, rootElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        rootElement.appendChild(element)

        element.setAttribute('RangeType', self.processChoice)
        element.setAttribute('FirstChapter', str(self.firstChapter))
        element.setAttribute('LastChapter', str(self.lastChapter))

        for episode in self.episodes:
            episode.ToXML(doc, element)

        return element

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    def PrintObject(chapterRanges):
        print (chapterRanges)
        for audioTrackState in chapterRanges:
            print (audioTrackState)
        print ()

    chapterRanges = ChapterRanges(None)
    chapterRanges.AddEpisode(1, 1, 'First')
    chapterRanges.AddEpisode(2, 5, 'Second')
    chapterRanges.AddEpisode(6, 6, 'Third')
    chapterRanges.AddEpisode(7, 10, 'Fourth')

    PrintObject (chapterRanges)

    # ********************************************************
    filename = 'TestFiles/TestChapterRanges.xml'
    elementName = 'TestChapterRanges'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == ChapterRanges.XMLNAME):
                chapterRanges.FromXML(childNode)
                PrintObject (chapterRanges)
            else:
                print ('Can''t find element "{}" in "{}".'.format(ChapterRanges.XMLNAME, filename))
                print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestChapterRanges', None)
    parentElement = doc.documentElement

    chapterRanges.ToXML(doc, parentElement)

    xmlFile = open('TestFiles/TestChapterRanges.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
