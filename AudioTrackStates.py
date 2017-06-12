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

class AudioTrackState(object):
    """ Contains the mixdown information for a single audio track.
    """

    XMLNAME = 'AudioTrackState'

    AUDIO_TRACK_CHOICES = ['', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    MIXDOWN_DEFAULT = ''

    def __init__(self, parent, index):
        self.__parent = parent
        self.index = index              # The index is needed for ToXML()

        self.clear()

    def __str__(self):
        return '{}: id={}, index={}, track={}, primaryMixdown={}, secondaryMixdown={}'\
            .format(self.XMLNAME, id(self),
            self.index, self.track, self.primaryMixdown, self.secondaryMixdown)

    def clear(self):
        """ Set all object members to their initial values.
        """

        self.track = self.AUDIO_TRACK_CHOICES[0]

        self.primaryMixdown = self.MIXDOWN_DEFAULT
        self.secondaryMixdown = self.MIXDOWN_DEFAULT

    @property
    def hasPrimaryMixdown(self):
        """ Returns true if the state has a primary mixdown.
        """

        if (not self.primaryMixdown):
            return False

        return True

    @property
    def hasSecondaryMixdown(self):
        """ Returns true if the state has a secondary mixdown.
        """

        if (not self.secondaryMixdown):
            return False

        return True

    @property
    def isTrackSelected(self):
        """ Returns true if the state has a track selected.
        """

        return (self.track != self.AUDIO_TRACK_CHOICES[0])

    @property
    def parent(self):
        return self.__parent

    def FromXML(self, element):
        """ Read the object from an XML file.
        """

        self.clear()

        self.index = XMLHelpers.GetXMLAttributeAsInt(element, 'Index', 0)
        self.track = XMLHelpers.GetXMLAttribute(element, 'Track', self.AUDIO_TRACK_CHOICES[0])

        # TODO Validate mixdowns

        self.primaryMixdown = XMLHelpers.GetXMLAttribute(element, 'Primary', None)
        self.secondaryMixdown = XMLHelpers.GetXMLAttribute(element, 'Secondary', None)

        if (self.track not in self.AUDIO_TRACK_CHOICES):
            self.track = self.AUDIO_TRACK_CHOICES[0]

    def GetMixdowns(self):
        """ Return an array of mixdown names.
        """

        mixdowns = []

        if (self.hasPrimaryMixdown):
            mixdowns.append(self.primaryMixdown)

        if (self.hasSecondaryStream):
            mixdowns.append(self.secondaryMixdown)

        return mixdowns

    def ToXML(self, doc, rootElement):
        """ Write the object to an XML file.
        """

        element = doc.createElement(self.XMLNAME)
        rootElement.appendChild(element)

        element.setAttribute('Index', str(self.index))
        element.setAttribute('Track', self.track)

        element.setAttribute('Primary', self.primaryMixdown)
        element.setAttribute('Secondary', self.secondaryMixdown)

        return element

class AudioTrackStates(MutableSequence):
    """ Container for a list of AudioTrackStates.
    """

    XMLNAME = 'AudioTrackStates'

    PROCESS_DEFAULT = 'Default'
    PROCESS_CUSTOM = 'Custom'
    PROCESS_CHOICES = [PROCESS_DEFAULT, PROCESS_CUSTOM]

    def __init__(self, parent, count=3):
        self.__parent = parent

        self.processChoice = self.PROCESS_DEFAULT
        self.audioTrackStates = []

        for index in range(count):
            audioTrackState = AudioTrackState(self, index)
            self.append(audioTrackState)

    def __str__(self):
        return '{}: id={}, len={}, processChoice="{}"'.format(self.XMLNAME, id(self),
        len(self.audioTrackStates), self.processChoice)

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.audioTrackStates[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, AudioTrackState))
        self.audioTrackStates[idx] = obj

    def __delitem__(self, idx):
        del self.audioTrackStates[idx]

    def __len__(self):
        return len(self.audioTrackStates)

    def insert(self, idx, obj):
        assert(isinstance(obj, AudioTrackState))
        self.audioTrackStates.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """

        self.processChoice = self.PROCESS_DEFAULT
        for audioTrackState in self.audioTrackStates:
            audioTrackState.clear()

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
            if (childNode.localName == AudioTrackState.XMLNAME):
                index = XMLHelpers.GetXMLAttributeAsInt(childNode, 'Index', 0)
                if (index in range(len(self.audioTrackStates))):
                    self.audioTrackStates[index].FromXML(childNode)

        # TODO Handle index not in range condition.

    def AutoSet_From_AudioTracks(self, audioTracks, preferences):
        """ Set the audio track states based on the auto settings and the
            available audio tracks.

            Returns the number of audio track states that are set.
        """
        # assert(len(audioTrackStates) == 3)
        self.clear()
        track51, trackDTS, trackFallback = audioTracks.GetAutoAudio(preferences.autoAudioTracks)
        trackIndex = 0

        # Process the 5.1 audio
        # -----------------------
        if (track51 is not None):
            audioTrackState = self.audioTrackStates[trackIndex]
            trackIndex += 1

            audioTrackState.track = str(track51.trackNumber)

            if (track51.isAC3):
                audioTrackState.primaryMixdown = preferences.autoMixdown.ac351Primary
                audioTrackState.secondaryMixdown = preferences.autoMixdown.ac351Secondary
            else:
                audioTrackState.primaryMixdown = preferences.autoMixdown.otherPrimary
                audioTrackState.secondaryMixdown = preferences.autoMixdown.otherSecondary

        # Process the DTS audio
        # -------------------------
        if (trackDTS is not None):
            audioTrackState = self.audioTrackStates[trackIndex]
            trackIndex += 1

            audioTrackState.track = str(trackDTS.trackNumber)

            if (trackDTS.isDTS):
                audioTrackState.primaryMixdown = preferences.autoMixdown.dtsPrimary
                audioTrackState.secondaryMixdown = preferences.autoMixdown.dtsSecondary
            else:
                audioTrackState.primaryMixdown = preferences.autoMixdown.dtshdPrimary
                audioTrackState.secondaryMixdown = preferences.autoMixdown.dtshdSecondary

        # Process the fallback audio
        # -----------------------------
        if (trackIndex == 0 and trackFallback is not None):
            audioTrackState = self.audioTrackStates[trackIndex]
            trackIndex += 1

            audioTrackState.track = str(trackFallback.trackNumber)

            if (trackFallback.isAC3):
                audioTrackState.primaryMixdown = preferences.autoMixdown.ac3Primary
                audioTrackState.secondaryMixdown = preferences.autoMixdown.ac3Secondary
            else:
                audioTrackState.primaryMixdown = preferences.autoMixdown.otherPrimary
                audioTrackState.secondaryMixdown = preferences.autoMixdown.otherSecondary

        return trackIndex

    def ToXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """

        if (len(self.audioTrackStates) > 0):
            element = doc.createElement(self.XMLNAME)
            parentElement.appendChild(element)

            element.setAttribute('ProcessChoice', self.processChoice)

            # These are "convenience" attributes for other applications that read the XML file.
            # They are ignored by self.FromXML().
            element.setAttribute('count', str(len(self.audioTrackStates)))

            for audioTrackState in self.audioTrackStates:
                audioTrackState.ToXML(doc, element)

            return element

        return None

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    def PrintObject(audioTrackStates):
        print (audioTrackStates)
        for audioTrackState in audioTrackStates:
            print (audioTrackState)
        print ()

    audioTrackStates = AudioTrackStates(None)
    PrintObject (audioTrackStates)

    # ********************************************************
    filename = 'TestFiles/TestAudioTrackStates.xml'
    elementName = 'TestAudioTrackStates'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == AudioTrackStates.XMLNAME):
                audioTrackStates.FromXML(childNode)
                PrintObject (audioTrackStates)
            else:
                print ('Can''t find element "{}" in "{}".'.format(AudioTrackStates.XMLNAME, filename))
                print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestAudioTrackStates', None)
    parentElement = doc.documentElement

    audioTrackStates.ToXML(doc, parentElement)

    xmlFile = open('TestFiles/TestAudioTrackStates.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
