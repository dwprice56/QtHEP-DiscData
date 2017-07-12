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

class DiscMixdownsSingleton(MutableSequence):
    """This class stores the data used to validate mixdowns in Disc.fromXML().

    This class implements the singleton pattern so only one instance of this
    class exists.  We don't want to implement the Preferences.Mixdowns class as
    a singleton because we need to make a copy for the Preferences dialog (in
    case it's canceled).

    That one instance should be updated whenever the preferences are updated."""

    __instance = None

    def __new__(cls):
        if DiscMixdownsSingleton.__instance is None:
            DiscMixdownsSingleton.__instance = object.__new__(cls)

            DiscMixdownsSingleton.__instance.mixdowns = []

        return DiscMixdownsSingleton.__instance

    def __str__(self):
        s = 'DiscMixdownsSingleton: len={}\n  '.format(len(self.mixdowns))

        s += '\n  '.join(self.mixdowns)

        return s

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.mixdowns[idx]

    def __setitem__(self, idx, obj):
        self.mixdowns[idx] = obj

    def __delitem__(self, idx):
        del self.mixdowns[idx]

    def __len__(self):
        return len(self.mixdowns)

    def insert(self, idx, obj):
        self.mixdowns.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """Set all object members to their initial values."""

        del self.mixdowns[:]

    def set(self, mixdowns):
        """Set/update the name list."""

        self.clear()
        for mixdown in mixdowns:
            self.append(mixdown)

class AudioTrackState(object):
    """ Contains the mixdown information for a single audio track.
    """

    XMLNAME = 'AudioTrackState'

    AUDIO_TRACK_CHOICES = ['', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    MIXDOWN_DEFAULT = ''

    def __init__(self, parent, index):
        self.__parent = parent
        self.index = index              # The index is needed for toXML()

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
    def hasMixdown(self):
        """ Returns true if the state has a primary or secondary mixdown.
        """
        if (self.primaryMixdown or self.secondaryMixdown):
            return True

        return False

    @property
    def hasPrimaryMixdown(self):
        """ Returns true if the state has a primary mixdown.
        """
        if (self.primaryMixdown):
            return True

        return False

    @property
    def hasSecondaryMixdown(self):
        """ Returns true if the state has a secondary mixdown.
        """
        if (self.secondaryMixdown):
            return True

        return False

    @property
    def isTrackSelected(self):
        """ Returns true if the state has a track selected.
        """
        return (self.track != self.AUDIO_TRACK_CHOICES[0])

    @property
    def mixdowns(self):
        """ Return an array of mixdown names.

            The array will be empty if no midowns are selected.
        """
        mixdowns = []

        if (self.hasPrimaryMixdown):
            mixdowns.append(self.primaryMixdown)

        if (self.hasSecondaryMixdown):
            mixdowns.append(self.secondaryMixdown)

        return mixdowns

    @property
    def parent(self):
        return self.__parent

    @property
    def row(self):
        return (self.index + 1)

    def fromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.index = XMLHelpers.GetXMLAttributeAsInt(element, 'Index', 0)
        self.track = XMLHelpers.GetXMLAttribute(element, 'Track', self.AUDIO_TRACK_CHOICES[0])

        self.primaryMixdown = XMLHelpers.GetXMLAttribute(element, 'Primary', None)
        self.secondaryMixdown = XMLHelpers.GetXMLAttribute(element, 'Secondary', None)

        discMixdownsSingleton = DiscMixdownsSingleton()
        if (self.primaryMixdown not in discMixdownsSingleton):
            self.primaryMixdown = None
        if (self.secondaryMixdown not in discMixdownsSingleton):
            self.secondaryMixdown = None

        if (self.track not in self.AUDIO_TRACK_CHOICES):
            self.track = self.AUDIO_TRACK_CHOICES[0]

    def toXML(self, doc, rootElement):
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
    def isCustom(self):
        """ Returns True if this object has custom audio.
        """
        return (self.processChoice == self.PROCESS_CUSTOM)

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'ProcessChoice',
            self.PROCESS_DEFAULT, self.PROCESS_CHOICES)

        for childNode in element.childNodes:
            if (childNode.localName == AudioTrackState.XMLNAME):
                index = XMLHelpers.GetXMLAttributeAsInt(childNode, 'Index', 0)
                if (index in range(len(self.audioTrackStates))):
                    self.audioTrackStates[index].fromXML(childNode)
                else:
                    raise RuntimeError('AudioTrackState index "{}" is out of range in fromXML().'.format(index))

    # def selectedTrackStates(self):
    #     """ Return the selected audio tracks, with the associated mixdowns.
    #
    #         Returns a list of audio track states that are isTrackSelected.
    #     """
    #     selectedTracks = []
    #
    #     for audioTrackState in self.audioTrackStates:
    #         if (audioTrackState.isTrackSelected):
    #             selectedTracks.append(audioTrackState)
    #
    #     return selectedTracks

    def autoset_From_AudioTracks(self, audioTracks, preferences):
        """ Set the audio track states based on the auto settings and the
            available audio tracks.

            Returns the number of audio track states that are set.
        """
        # assert(len(audioTrackStates) == 3)
        self.clear()
        track51, trackDTS, trackFallback = audioTracks.getAutoAudio(preferences.autoAudioTracks)

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

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        if (len(self.audioTrackStates) > 0):
            element = doc.createElement(self.XMLNAME)
            parentElement.appendChild(element)

            element.setAttribute('ProcessChoice', self.processChoice)

            # These are "convenience" attributes for other applications that read the XML file.
            # They are ignored by self.fromXML().
            element.setAttribute('count', str(len(self.audioTrackStates)))

            for audioTrackState in self.audioTrackStates:
                audioTrackState.toXML(doc, element)

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
                audioTrackStates.fromXML(childNode)
                PrintObject (audioTrackStates)
            else:
                print ('Can''t find element "{}" in "{}".'.format(AudioTrackStates.XMLNAME, filename))
                print ()

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestAudioTrackStates', None)
    parentElement = doc.documentElement

    audioTrackStates.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestAudioTrackStates.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
