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
from collections import MutableSequence, namedtuple

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

import XMLHelpers

AutoAudioTracks = namedtuple('AutoAudioTracks', 'track51, trackDTS, trackFallback')

class AudioTrack(object):
    """ Contains the information for a single audio track.
    """

    XMLNAME = 'AudioTrack'

    def __init__(self, parent):
        self.__parent = parent

        self.clear()

        self.reLanguage = re.compile(r'\(iso639-2: ([a-z]{3})\)')
        self.reChannels = re.compile(r'\((\d.\d) ch\)')
        self.reDolbySurround = re.compile(r'\((Dolby Surround)\)')

    def __str__(self):
        return '{} {}: {}, hz: {}, bps: {}, ' \
        'Language: {}, ChannelText: {}, Channels: {}'.format(self.XMLNAME,
            self.trackNumber, self.description, self.hertz, self.bitsPerSecond,
            self.language, self.channelsText, self.channels)

    def clear(self):
        """ Set all object members to their initial values.
        """

        self.trackNumber = 0
        self.description = ''

        self.hertz = 0
        self.bitsPerSecond = 0

    @property
    def channels(self):
        """ Return the number of channels from the description.

            Returns None if the number of channels can't be found.
        """

        if (self.description is None or self.description == ''):
            return None

        match = self.reChannels.search(self.description)
        if (match is not None):
            channelsString = match.groups()[0]

            bits = match.groups()[0].split('.')
            assert (len(bits) == 2)
            c = int(bits[0]) + int(bits[1])

            return c

        match = self.reDolbySurround.search(self.description)
        if (match is not None):
            return 2

        return None

    @property
    def channelsText(self):
        """ Return the number of channels from the description.

            Returns None if the number of channels can't be found.
        """

        if (self.description is None or self.description == ''):
            return None

        match = self.reChannels.search(self.description)
        if (match is not None):
            return match.groups()[0]

        match = self.reDolbySurround.search(self.description)
        if (match is not None):
            return match.groups()[0]

        return None

    @property
    def hashString(self):
        """ Generate a string used to update the hash; the string is based on
            the object contents.

            Omit 'description', it seems to be a calculated field subject to change
        """
        return 'Audio Track: {}, Hertz: {}, Bits Per Second: {}, Language: {}, ' \
            'Channels: {}'.format(
            self.trackNumber,
            self.hertz,
            self.bitsPerSecond,
            self.language,
            self.channels
        )

    @property
    def isAC3(self):
        """ Return True if the description contains the string "AC3".
        """

        return (self.description.upper().find('AC3') != -1)

    @property
    def isDTS(self):
        """ Return True if description contains the string "DTS" but not "DTSHD".
        """

        if (self.isDTSHD):
            return False

        return (self.description.upper().find('DTS') != -1)

    @property
    def isDTSHD(self):
        """ Return True if the description contains the string "DTSHD".
        """

        return (self.description.upper().find('DTSHD') != -1)

    @property
    def is51(self):
        """ Return True if the description contains the string "5.1".
        """

        channelsText = self.channelsText
        if (channelsText is None):
            return False

        return (channelsText == '5.1')

    @property
    def language(self):
        """ Return the 3 character language string (ex. eng, spa, fra) from the description.

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

        self.hertz = XMLHelpers.GetXMLAttributeAsInt(element, 'Hertz', 0)
        self.bitsPerSecond = XMLHelpers.GetXMLAttributeAsInt(element, 'BitsPerSecond', 0)

    def IsLanguage(self, language):
        """ Returns true if the track language is a match.
        """

        return (language.lower() == self.language.lower())

    def parse(self, line):
        """ Extract the audio track information into the object memebers from
            Handbrakes output.
        """

        parms = line[6:].split(', ')

        self.trackNumber = int(parms[0])
        self.description = parms[1]

        if (len(parms) >= 3 and parms[2].lower().endswith('hz')):
            parm = parms[2].lower().strip('hz')
            self.hertz = int(parm)

        if (len(parms) >= 4 and parms[3].lower().endswith('bps')):
            parm = parms[3].lower().strip('bps')
            self.bitsPerSecond = int(parm)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """

        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('TrackNumber', str(self.trackNumber))
        element.setAttribute('Description', self.description)

        element.setAttribute('Hertz', str(self.hertz))
        element.setAttribute('BitsPerSecond', str(self.bitsPerSecond))

        return element

class AudioTracks(MutableSequence):
    """ Container for a list of audioTracks.
    """

    XMLNAME = 'AudioTracks'

    def __init__(self, parent):
        super().__init__()

        self.__parent = parent

        self.audioTracks = []
        self.audioTracksByTrackNumber = {}

    def __str__(self):
        return '{}: len: {}'.format(self.XMLNAME, len(self.audioTracks))

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.audioTracks[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, AudioTrack))

        self.audioTracksByTrackNumber.pop(self.audioTracks[idx].trackNumber)
        self.audioTracks[idx] = obj
        self.audioTracksByTrackNumber[obj.trackNumber] = obj

    def __delitem__(self, idx):
        self.audioTracksByTrackNumber.pop(self.audioTracks[idx].trackNumber)
        del self.audioTracks[idx]

    def __len__(self):
        return len(self.audioTracks)

    def insert(self, idx, obj):
        assert(isinstance(obj, AudioTrack))

        self.audioTracks.insert(idx, obj)
        self.audioTracksByTrackNumber[obj.trackNumber] = obj
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """

        del self.audioTracks[:]
        self.audioTracksByTrackNumber.clear()

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Read the object from an XML file.
        """

        self.clear()

        for childNode in element.childNodes:
            if (childNode.localName == AudioTrack.XMLNAME):

                audioTrack = AudioTrack(self)
                audioTrack.fromXML(childNode)
                self.append(audioTrack)

    def getByTrackNumber(self, trackNumber):
        """ Returns the audio track for a track number.
            Returns None if the requested track doesn't exist.
        """

        if (trackNumber in self.audioTracksByTrackNumber.keys()):
            return self.audioTracksByTrackNumber[trackNumber]

        return None

    def hasTrackNumber(self, trackNumber):
        """ Returns true/false if a track number exists.
        """

        if (trackNumber in self.audioTracksByTrackNumber.keys()):
            return True

        return False

    def getAutoAudio(self, preferencesAutoAudioTracks):
        """ Return an audio object for this title based on the application settings.

            Return a named tuple of (track51, trackDTS, trackFallback).
            They may all be None if nothing if found.
        """
        track51 = None
        trackDTS = None
        trackFallback = None

        preferredLanguage = None
        if (preferencesAutoAudioTracks.autoSelectPreferredLanguage
        and preferencesAutoAudioTracks.preferredLanguage):
            preferredLanguage = preferencesAutoAudioTracks.preferredLanguage

        for audioTrack in self.audioTracks:
            if (preferredLanguage
            and (not audioTrack.IsLanguage(preferredLanguage))):
                continue

            if (preferencesAutoAudioTracks.autoSelect51
            and audioTrack.is51
            and (track51 is None)):
                track51 = audioTrack

            if (preferencesAutoAudioTracks.autoSelectDTS
            and (audioTrack.isDTS or audioTrack.isDTSHD)
            and (trackDTS is None)):
                trackDTS = audioTrack

            if (preferencesAutoAudioTracks.autoSelectFallback
            and (trackFallback is None)):
                trackFallback = audioTrack

        if (trackFallback is None
        and preferencesAutoAudioTracks.autoSelectFallback
        and len(self.audioTracks)):
            trackFallback = self.audioTracks[0]

        # print ('AudioTracks')
        # print (track51)
        # print (trackDTS)
        # print (trackFallback)

        return AutoAudioTracks(track51, trackDTS, trackFallback)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """

        if (len(self.audioTracks) > 0):
            element = doc.createElement(self.XMLNAME)
            parentElement.appendChild(element)

            # These are "convenience" attributes for other applications that read the XML file.
            # They are ignored by self.fromXML().
            element.setAttribute('count', str(len(self.audioTracks)))

            for audioTrack in self.audioTracks:
                audioTrack.toXML(doc, element)

            return element

        return None

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    audioTracks = AudioTracks(None)
    print (audioTracks)
    print ()

    lines = [
        '    + 1, English (AC3) (1.0 ch) (iso639-2: eng), 48000Hz, 192000bps',
        '    + 2, English (AC3) (1.0 ch) (iso639-2: eng), 48000Hz, 192000bps'
    ]

    for line in lines:
        audioTrack = AudioTrack(audioTracks)
        audioTrack.parse(line)
        audioTracks.append(audioTrack)

    print (audioTracks)
    for audioTrack in audioTracks:
        print (audioTrack)
    print ()

    # ********************************************************
    filename = 'TestFiles/TestAudioTracks.xml'
    elementName = 'TestAudioTracks'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == AudioTracks.XMLNAME):
                audioTracks.fromXML(childNode)
                print (audioTracks)
                for audioTrack in audioTracks:
                    print (audioTrack)
            else:
                print ('Can''t find element "{}" in "{}".'.format(AudioTracks.XMLNAME, filename))
        print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestAudioTracks', None)
    parentElement = doc.documentElement

    audioTracks.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestAudioTracks.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
