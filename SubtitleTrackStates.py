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

class SubtitleTrackState(object):
    """ Contains the subtitle track encoding information for a single subtitle
        track.
    """

    XMLNAME = 'SubtitleTrackState'

    SUBTITLE_TRACK_CHOICES = ['', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    def __init__(self, parent, index):
        self.__parent = parent
        self.index = index

        self.clear()

    def __str__(self):
        return '{}: id={}, index={}, track={}, forced={}, ' \
        'burn={}, default={}'.format(self.XMLNAME, id(self),
        self.index, self.track, self.forced, self.burn, self.default)

    @property
    def isTrackSelected(self):
        """ Returns true if the state has a track selected.
        """

        return (self.track != self.SUBTITLE_TRACK_CHOICES[0])

    @property
    def parent(self):
        return self.__parent

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.track = self.SUBTITLE_TRACK_CHOICES[0]
        self.forced = False
        self.burn = False
        self.default = False

    def FromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.index = XMLHelpers.GetXMLAttributeAsInt(element, 'Index', 0)
        self.track = XMLHelpers.GetXMLAttribute(element, 'Track', self.SUBTITLE_TRACK_CHOICES[0])

        self.forced = XMLHelpers.GetXMLAttributeAsBool(element, 'Forced', False)
        self.burn = XMLHelpers.GetXMLAttributeAsBool(element, 'Burn', False)
        self.default = XMLHelpers.GetXMLAttributeAsBool(element, 'Default', False)

        if (self.track not in self.SUBTITLE_TRACK_CHOICES):
            self.track = self.SUBTITLE_TRACK_CHOICES[0]

    def ToXML(self, doc, rootElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        rootElement.appendChild(element)

        element.setAttribute('Index', str(self.index))
        element.setAttribute('Track', self.track)

        element.setAttribute('Forced', XMLHelpers.BoolToString(self.forced))
        element.setAttribute('Burn', XMLHelpers.BoolToString(self.burn))
        element.setAttribute('Default', XMLHelpers.BoolToString(self.default))

        return element

class SubtitleTrackStates(MutableSequence):
    """Container for a list of SubtitleTrackStates."""

    XMLNAME = 'SubtitleTrackStates'

    PROCESS_DEFAULT = 'Default'
    PROCESS_CUSTOM = 'Custom'
    PROCESS_CHOICES = [PROCESS_DEFAULT, PROCESS_CUSTOM]

    def __init__(self, parent, count=3):
        self.__parent = parent

        self.processChoice = self.PROCESS_DEFAULT
        self.subtitleTrackStates = []

        for index in range(count):
            subtitleTrackState = SubtitleTrackState(self, index)
            self.append(subtitleTrackState)

    def __str__(self):
        return '{}: id={}, len={}, processChoice="{}"'.format(self.XMLNAME, id(self),
        len(self.subtitleTrackStates), self.processChoice)

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.subtitleTrackStates[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, SubtitleTrackState))
        self.subtitleTrackStates[idx] = obj

    def __delitem__(self, idx):
        del self.subtitleTrackStates[idx]

    def __len__(self):
        return len(self.subtitleTrackStates)

    def insert(self, idx, obj):
        assert(isinstance(obj, SubtitleTrackState))
        self.subtitleTrackStates.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.processChoice = self.PROCESS_DEFAULT
        for subtitleTrackState in self.subtitleTrackStates:
            subtitleTrackState.clear()

    @property
    def parent(self):
        return self.__parent

    def FromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'ProcessChoice',
            self.PROCESS_DEFAULT, self.PROCESS_CHOICES)

        for childNode in element.childNodes:
            if (childNode.localName == SubtitleTrackState.XMLNAME):
                index = XMLHelpers.GetXMLAttributeAsInt(childNode, 'Index', 0)
                if (index in range(len(self.subtitleTrackStates))):
                    self.subtitleTrackStates[index].FromXML(childNode)

        # TODO Handle index not in range condition.

    def AutoSet_From_SubtitleTracks(self, subtitleTracks, preferences):
        """ Set the subtitle track states based on the auto settings and the
            available subtitle tracks.
        """
        self.clear()
        subtitleTrack = subtitleTracks.GetAutoSubtitle(preferences.autoSubtitle)

        if (subtitleTrack is not None):
            self.subtitleTrackStates[0].track = str(subtitleTrack.trackNumber)
            self.subtitleTrackStates[0].forced =  False
            self.subtitleTrackStates[0].burn = preferences.autoSubtitle.subtitleBurn
            self.subtitleTrackStates[0].default = preferences.autoSubtitle.subtitleDefault


    def ToXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        if (len(self.subtitleTrackStates) > 0):
            element = doc.createElement(self.XMLNAME)
            parentElement.appendChild(element)

            element.setAttribute('ProcessChoice', self.processChoice)

            # These are "convenience" attributes for other applications that read the XML file.
            # They are ignored by self.FromXML().
            element.setAttribute('count', str(len(self.subtitleTrackStates)))

            for subtitleTrackState in self.subtitleTrackStates:
                subtitleTrackState.ToXML(doc, element)

            return element

        return None

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    def PrintObject(subtitleTrackStates):
        print (subtitleTrackStates)
        for subtitleTrackState in subtitleTrackStates:
            print (subtitleTrackState)
        print ()

    subtitleTrackStates = SubtitleTrackStates(None)
    PrintObject (subtitleTrackStates)

    # ********************************************************
    filename = 'TestFiles/TestSubtitleTrackStates.xml'
    elementName = 'TestSubtitleTrackStates'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == SubtitleTrackStates.XMLNAME):
                subtitleTrackStates.FromXML(childNode)
                PrintObject (subtitleTrackStates)
            else:
                print ('Can''t find element "{}" in "{}".'.format(SubtitleTrackStates.XMLNAME, filename))
                print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestSubtitleTrackStates', None)
    parentElement = doc.documentElement

    subtitleTrackStates.ToXML(doc, parentElement)

    xmlFile = open('TestFiles/TestSubtitleTrackStates.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
