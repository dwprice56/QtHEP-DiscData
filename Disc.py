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

from AudioTrackStates import (AudioTrackState,
    AudioTrackStates)
from Crop import AutoCrop, CustomCrop
from SubtitleTrackStates import (SubtitleTrackState,
    SubtitleTrackStates)
from Titles import (Title,
    Titles,
    TitleVisibleSingleton)

class DiscFilenameTemplatesSingleton(MutableSequence):
    """ This class stores the data used to validate filename templates in
        Disc.fromXML().

        This class implements the singleton pattern so only one instance of this
        class exists.  We don't want to implement the Preferences.FilenameTemplates
        class as a singleton because we need to make a copy for the Preferences
        dialog (in case it's canceled).

        That one instance should be updated whenever the preferences are updated.
    """

    __instance = None

    def __new__(cls):
        if DiscFilenameTemplatesSingleton.__instance is None:
            DiscFilenameTemplatesSingleton.__instance = object.__new__(cls)

            DiscFilenameTemplatesSingleton.__instance.filenameTemplates = []

        return DiscFilenameTemplatesSingleton.__instance

    def __str__(self):
        s = 'DiscFilenameTemplatesSingleton: len={}\n  '.format(len(self.filenameTemplates))

        s += '\n  '.join(self.filenameTemplates)

        return s

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.filenameTemplates[idx]

    def __setitem__(self, idx, obj):
        self.filenameTemplates[idx] = obj

    def __delitem__(self, idx):
        del self.filenameTemplates[idx]

    def __len__(self):
        return len(self.filenameTemplates)

    def insert(self, idx, obj):
        self.filenameTemplates.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """Set all object members to their initial values."""

        del self.filenameTemplates[:]

    def set(self, filenameTemplates):
        """Set/update the name list."""

        self.clear()
        for filenameTemplate in filenameTemplates:
            self.append(filenameTemplate)

class DiscPresetsSingleton(MutableSequence):
    """This class stores the data used to validate preset names in Disc.fromXML().

    This class implements the singleton pattern so only one instance of this
    class exists.  We don't want to implement the Preferences.Presets class as
    a singleton because we need to make a copy for the Preferences dialog (in
    case it's canceled).

    That one instance should be updated whenever the preferences are updated."""

    __instance = None

    def __new__(cls):
        if DiscPresetsSingleton.__instance is None:
            DiscPresetsSingleton.__instance = object.__new__(cls)

            DiscPresetsSingleton.__instance.presetNames = []

        return DiscPresetsSingleton.__instance

    def __str__(self):
        s = 'DiscPresetsSingleton: len={}\n  '.format(len(self.presetNames))

        s += '\n  '.join(self.presetNames)

        return s

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.presetNames[idx]

    def __setitem__(self, idx, obj):
        self.presetNames[idx] = obj

    def __delitem__(self, idx):
        del self.presetNames[idx]

    def __len__(self):
        return len(self.presetNames)

    def insert(self, idx, obj):
        self.presetNames.insert(idx, obj)
    # ==========================================================================

    def clear(self):
        """Set all object members to their initial values."""

        del self.presetNames[:]

    def set(self, presetNames):
        """Set/update the name list."""

        self.clear()
        for presetName in presetNames:
            self.append(presetName)

class Disc(object):
    """A class that holds all of the data for a single DVD or BluRay."""

    XMLNAME = 'Disc'

    DEFAULT_FIRST_EPISODE_NUMBER = 1
    DEFAULT_EPISODE_NUMBER_PRECISION = 2
    HIDE_SHORT_TITLES_DEFAULT = False
    NODVDNAV_DEFAULT = False
    NOTES_DEFAULT = ''

    def __init__(self, parent):
        self.__parent = parent
        self.__discFilenameTemplatesSingleton = DiscFilenameTemplatesSingleton()
        # self.__discMixdownsSingleton = DiscMixdownsSingleton()
        self.__discPresetsSingleton = DiscPresetsSingleton()

        self.titles = Titles(self)

        self.customCrop = CustomCrop(self)
        self.audioTrackStates = AudioTrackStates(self)
        self.subtitleTrackStates = SubtitleTrackStates(self)

        self.clear()

    def __str__(self):
        return '{}: source="{}", sourceLabel="{}"' \
            '\n  destination="{}"' \
            '\n  title="{}"' \
            '\n  firstEpisodeNumber={}, episodeNumberPrecision={}' \
            '\n  preset="{}"' \
            '\n  hideShortTitles={}, nodvdnav={}, notes="{}"' \
            .format(self.XMLNAME, self.source, self.sourceLabel,
            self.destination,
            self.title,
            self.firstEpisodeNumber, self.episodeNumberPrecision,
            self.preset,
            self.hideShortTitles, self.nodvdnav, self.notes)

    def clear(self):
        """Set all object members to their initial values."""

        self.source = ''
        self.sourceLabel = ''
        self.destination = ''

        self.title = ''
        self.filenameTemplate = ''

        self.firstEpisodeNumber = self.DEFAULT_FIRST_EPISODE_NUMBER
        self.episodeNumberPrecision = self.DEFAULT_EPISODE_NUMBER_PRECISION

        self.preset = ''

        self.hideShortTitles = self.HIDE_SHORT_TITLES_DEFAULT
        self.nodvdnav = self.NODVDNAV_DEFAULT
        self.notes = self.NOTES_DEFAULT

        self.titles.clear()
        self.customCrop.clear()
        self.audioTrackStates.clear()
        self.subtitleTrackStates.clear()

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element, destinationOverride=None):
        """ Read the application state from an XML file.

            If the destinationOverride parameter is supplied it will be used
            instead of the destination in the state file.
        """
        self.clear()

        self.source = XMLHelpers.GetXMLAttribute(element, 'Source', '').strip()
        if (destinationOverride):
            self.destination = destinationOverride
        else:
            self.destination = XMLHelpers.GetXMLAttribute(element, 'Destination', '').strip()
        # if ((not wx.GetApp().initializing) and wx.GetApp().settings.discSession.keepDestination):
        #     self.destination = destination
        # else:
        #     self.destination = XMLHelpers.GetXMLAttribute(element, 'Destination', '').strip()
        self.sourceLabel = XMLHelpers.GetXMLAttribute(element, 'SourceLabel', '').strip()

        # ----- FILE NAME ----- #

        self.title = XMLHelpers.GetXMLAttribute(element, 'Title', '').strip()

        self.filenameTemplate = XMLHelpers.GetValidXMLAttribute(element, 'FileNameTemplate',
            self.__discFilenameTemplatesSingleton[0], self.__discFilenameTemplatesSingleton)

        self.firstEpisodeNumber = XMLHelpers.GetXMLAttributeAsInt(element, 'FirstEpisodeNumber',
            self.DEFAULT_FIRST_EPISODE_NUMBER)
        self.episodeNumberPrecision = XMLHelpers.GetXMLAttributeAsInt(element, 'EpisodeNumberPrecision',
            self.DEFAULT_EPISODE_NUMBER_PRECISION)

        self.preset = XMLHelpers.GetValidXMLAttributes(element, ['Preset','PresetName'],
            self.__discPresetsSingleton[0], self.__discPresetsSingleton)

        self.hideShortTitles = XMLHelpers.GetXMLAttributeAsBool(element, 'HideShortTitles',
            self.HIDE_SHORT_TITLES_DEFAULT)
        self.nodvdnav = XMLHelpers.GetXMLAttributeAsBool(element, 'NODVDNAV', self.NODVDNAV_DEFAULT)
        self.notes = XMLHelpers.GetXMLAttribute(element, 'Notes', self.NOTES_DEFAULT).strip()

        # ----- Child nodes ----- #

        # longestTitle = None
        for childNode in element.childNodes:
            if (childNode.localName == Titles.XMLNAME):
                self.titles.fromXML(childNode)
            elif (childNode.localName == AudioTrackStates.XMLNAME):
                self.audioTrackStates.fromXML(childNode)
            elif (childNode.localName == SubtitleTrackStates.XMLNAME):
                self.subtitleTrackStates.fromXML(childNode)

            # Legacy support: AudioTrackStates was not always an object.
            elif (childNode.localName == 'AudioTrack0'):
                self.audioTrackStates[0].fromXML(childNode)
            elif (childNode.localName == 'AudioTrack1'):
                self.audioTrackStates[1].fromXML(childNode)
            elif (childNode.localName == 'AudioTrack2'):
                self.audioTrackStates[2].fromXML(childNode)

            # Legacy support: SubtitleTrackStates was not always an object.
            elif (childNode.localName == 'SubtitleTrack0'):
                self.subtitleTrackStates[0].fromXML(childNode)
            elif (childNode.localName == 'SubtitleTrack1'):
                self.subtitleTrackStates[1].fromXML(childNode)
            elif (childNode.localName == 'SubtitleTrack2'):
                self.subtitleTrackStates[2].fromXML(childNode)

        # ----- CROPPING ----- #

        # Cropping is processed after everything else because the default
        # cropping values are taken from the autoCrop settings of the longest
        # titles.

        matchingTitles = self.titles.matchingTitles()
        if (matchingTitles.longestTitle):
            autoCrop = matchingTitles.longestTitle.autoCrop
        else:
            autoCrop = AutoCrop(self)

        for childNode in element.childNodes:
            if (childNode.localName == CustomCrop.XMLNAME):
                self.customCrop.fromXML(childNode, autoCrop)        # The autoCrop parameter provides the default values for custom cropping.

        # Legacy code: CustomCrop was not always an object.
        # This is done after reading the child nodes because the top, bottom, etc. defaults
        # come from the longestTitle.autoCrop object.
        self.customCrop.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'Crop',
            CustomCrop.PROCESS_DEFAULT, CustomCrop.PROCESS_CHOICES)

        self.customCrop.top = XMLHelpers.GetXMLAttributeAsInt(element,
            'CustomcropTop', autoCrop.top)
        self.customCrop.bottom = XMLHelpers.GetXMLAttributesAsInt(element,
            ['CustomropBottom', 'CustomcropBottom'], autoCrop.bottom)           # Attribute name was mispelled at one point.
        self.customCrop.left = XMLHelpers.GetXMLAttributesAsInt(element,
            ['CustomropLeft', 'CustomcropLeft'], autoCrop.left)                 # Attribute name was mispelled at one point.
        self.customCrop.right = XMLHelpers.GetXMLAttributeAsInt(element,
            'CustomcropRight', autoCrop.right)

        self.newSessionStuff()

    def newSessionStuff(self):
        """ Things to do when a new disc session is parsed or read from a file.
        """
        TitleVisibleSingleton().hideShortTitles = self.hideShortTitles
        for title in self.titles:
            title.chapters.calculateCumulativeDuration()

    def parse(self, buffer):
        """Parse the output from the HandBrake command line and extract the
        title information.  Use the informtion to create Title objects."""

        self.titles.parse(buffer)

        self.newSessionStuff()

    def toXML(self, doc, rootElement):
        """Write the application state to an XML file."""

        element = doc.createElement(self.XMLNAME)
        rootElement.appendChild(element)

        element.setAttribute('Source', self.source.strip())
        element.setAttribute('SourceLabel', self.sourceLabel.strip())
        element.setAttribute('Destination', self.destination.strip())

        # ----- FILE NAME ----- #

        element.setAttribute('Title', self.title.strip())
        element.setAttribute('FileNameTemplate', self.filenameTemplate.strip())

        element.setAttribute('FirstEpisodeNumber', str(self.firstEpisodeNumber))
        element.setAttribute('EpisodeNumberPrecision', str(self.episodeNumberPrecision))

        element.setAttribute('Preset', self.preset)

        element.setAttribute('HideShortTitles', XMLHelpers.BoolToString(self.hideShortTitles))
        element.setAttribute('NODVDNAV', XMLHelpers.BoolToString(self.nodvdnav))
        element.setAttribute('Notes', self.notes.strip())

        self.titles.toXML(doc, element)
        self.customCrop.toXML(doc, element)
        self.audioTrackStates.toXML(doc, element)
        self.subtitleTrackStates.toXML(doc, element)

        return element

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    sys.path.insert(0, '/home/dave/QtProjects/QtHEP')

    from Preferences import FilenameTemplates, Presets

    def PrintDisc(disc):
        print (disc)
        for title in disc.titles:
            print (title)
        print ()

    filenameTemplates = FilenameTemplates(None)
    print (filenameTemplates)
    discFilenameTemplatesSingleton = DiscFilenameTemplatesSingleton()
    print (discFilenameTemplatesSingleton)
    discFilenameTemplatesSingleton.set(filenameTemplates)
    print (discFilenameTemplatesSingleton)
    print ()

    presets = Presets(None)
    print (presets)
    discPresetsSingleton = DiscPresetsSingleton()
    print (discPresetsSingleton)
    discPresetsSingleton.set(presets.getNames())
    print (discPresetsSingleton)
    print()

    disc = Disc(None)
    PrintDisc(disc)

    # ********************************************************
    filename = 'TestFiles/TestDisc.xml'
    elementName = 'TestDisc'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == Disc.XMLNAME):
                disc.fromXML(childNode)
                print (disc)
                for title in disc.titles:
                    print (title)
            else:
                print ('Can''t find element "{}" in "{}".'.format(Titles.XMLNAME, filename))
        print ()

    PrintDisc(disc)

    # ********************************************************
    filename = 'TestFiles/test.buffer'
    if (os.path.exists(filename)):
        with open('TestFiles/test.buffer', 'r') as f:
            buffer = f.read()
    else:
        print ('ERROR!  Unable to find file "{}".'.format(filename))
        sys.exit(1)

    disc.parse(buffer)

    PrintDisc(disc)

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestDisc', None)
    parentElement = doc.documentElement

    disc.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestDisc.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
