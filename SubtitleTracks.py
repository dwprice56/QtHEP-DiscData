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

import re, sys
from collections import MutableSequence

sys.path.insert(0, '../Helpers')

import XMLHelpers

class SubtitleTrack(object):
    """ Contains the information for a single subtitle track.
    """

    XMLNAME = 'SubtitleTrack'

    def __init__(self, parent):
        self.__parent = parent

        self.clear()

        self.reLanguage = re.compile(r'\(iso639-2: ([a-z]{3})\)')

    def __str__(self):
        return '{} {}: {}, Language: {}'.format(self.XMLNAME,
            self.trackNumber, self.description, self.language)

    def clear(self):
        """ Set all object members to their initial values.
        """

        self.trackNumber = 0
        self.description = ''

    @property
    def language(self):
        """ Return the 3 character language string (ex. eng, spa, fra) from the
            description.

            Returns None if the language can't be found.
        """

        if (self.description is None or self.description == ''):
            return None

        match = self.reLanguage.search(self.description)
        if (match is None):
            return None

        return match.groups()[0]

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.trackNumber = XMLHelpers.GetXMLAttributeAsInt(element, 'TrackNumber', 0)
        self.description = XMLHelpers.GetXMLAttribute(element, 'Description', '').strip()

    @property
    def hashString(self):
        """ Generate a string used to update the hash; the string is based on
            the object contents.
        """

        return 'Subtitle Track: {}, Language: {}'.format(
            self.trackNumber, self.language
        )

    def parse(self, line):
        """ Extract the subtitle track information into the object memebers from
            Handbrakes output.
        """

        parms = line[6:].split(', ')

        self.trackNumber = int(parms[0])
        self.description = parms[1]

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('TrackNumber', str(self.trackNumber))
        element.setAttribute('Description', self.description)

        return element

class SubtitleTracks(MutableSequence):
    """Container for a list of SubtitleTracks."""

    XMLNAME = 'SubtitleTracks'

    def __init__(self, parent):
        self.__parent = parent

        self.subtitleTracks = []
        self.subtitleTracksByTrackNumber = {}

    def __str__(self):
        return '{}: len: {}'.format(self.XMLNAME, len(self.subtitleTracks))

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.subtitleTracks[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, SubtitleTrack))

        self.subtitleTracksByTrackNumber.pop(self.subtitleTracks[idx].trackNumber)
        self.subtitleTracks[idx] = obj
        self.subtitleTracksByTrackNumber[obj.trackNumber] = obj

    def __delitem__(self, idx):
        self.subtitleTracksByTrackNumber.pop(self.subtitleTracks[idx].trackNumber)
        del self.subtitleTracks[idx]

    def __len__(self):
        return len(self.subtitleTracks)

    def insert(self, idx, obj):
        assert(isinstance(obj, SubtitleTrack))

        self.subtitleTracks.insert(idx, obj)
        self.subtitleTracksByTrackNumber[obj.trackNumber] = obj
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """

        del self.subtitleTracks[:]
        self.subtitleTracksByTrackNumber.clear()

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Read the object from an XML file.
        """

        self.clear()

        for childNode in element.childNodes:
            if (childNode.localName == SubtitleTrack.XMLNAME):

                subtitleTrack = SubtitleTrack(self)
                subtitleTrack.fromXML(childNode)
                self.append(subtitleTrack)

    def getByTrackNumber(self, trackNumber):
        """ Returns the subtitle track for a track number.
            Returns None if the requested track doesn't exist.
        """
        if (trackNumber in self.subtitleTracksByTrackNumber.keys()):
            return self.subtitleTracksByTrackNumber[trackNumber]

        return None

    def hasTrackNumber(self, trackNumber):
        """ Returns true/false if a track number exists.
        """
        if (trackNumber in self.subtitleTracksByTrackNumber.keys()):
            return True

        return False

    def getAutoSubtitle(self, preferencesAutoSubtitle):
        """ Return a subtitle object for this title based on the application
            settings.

            Return None if nothing is found.
        """
        selectedSubtitleTrack = None
        if (len(self.subtitleTracks) > 0):
            for subtitleTrack in self.subtitleTracks:

                if (preferencesAutoSubtitle.autoSelectPreferredLanguage and
                    preferencesAutoSubtitle.preferredLanguage != "" and
                    subtitleTrack.description.find(preferencesAutoSubtitle.preferredLanguage) == -1):

                    continue

                selectedSubtitleTrack = subtitleTrack
                break

        return selectedSubtitleTrack

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        if (len(self.subtitleTracks) > 0):
            element = doc.createElement(self.XMLNAME)
            parentElement.appendChild(element)

            # These are "convenience" attributes for other applications that read the XML file.
            # They are ignored by self.fromXML().
            element.setAttribute('count', str(len(self.subtitleTracks)))

            for subtitleTrack in self.subtitleTracks:
                subtitleTrack.toXML(doc, element)

            return element

        return None

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    subtitleTracks = SubtitleTracks(None)
    print (subtitleTracks)
    print ()

    lines = [
        '    + 1, English (iso639-2: eng) (Bitmap)(VOBSUB)'
    ]

    for line in lines:
        subtitleTrack = SubtitleTrack(subtitleTracks)
        subtitleTrack.parse(line)
        subtitleTracks.append(subtitleTrack)

    print (subtitleTracks)
    for subtitleTrack in subtitleTracks:
        print (subtitleTrack)
    print ()

    # ********************************************************
    filename = 'TestFiles/TestSubtitleTracks.xml'
    elementName = 'TestSubtitleTracks'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == SubtitleTracks.XMLNAME):
                subtitleTracks.fromXML(childNode)
                print (subtitleTracks)
                for subtitleTrack in subtitleTracks:
                    print (subtitleTrack)
            else:
                print ('Can''t find element "{}" in "{}".'.format(SubtitleTracks.XMLNAME, filename))
        print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestSubtitleTracks', None)
    parentElement = doc.documentElement

    subtitleTracks.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestSubtitleTracks.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
