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

import datetime, hashlib, sys
from collections import MutableSequence, namedtuple

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

import XMLHelpers
from Helpers import DurationAsTimedelta

from AudioTracks import AudioTrack, AudioTracks
from AudioTrackStates import AudioTrackState, AudioTrackStates
from Cells import Cells
from ChapterRanges import ChapterRangeEpisode, ChapterRanges
from Chapters import Chapter, Chapters
from Crop import AutoCrop, CustomCrop
from SubtitleTracks import SubtitleTrack, SubtitleTracks
from SubtitleTrackStates import SubtitleTrackState, SubtitleTrackStates

MatchingTitles = namedtuple('MatchingTitles', 'matchingTitles, longestMatchingTitle, defaultTitle, longestTitle')

class TitleVisibleSingleton(object):
    """ This class stores the data used to determine whether a title is 'visible'.

        The data is a combination of the 'MinimumTitleSeconds' from the preferences
        and the 'hideShortTitles' checkbox on the GUI.  It must be updated whenever
        they change.

        This class implements the singleton pattern so only one instance of this
        class exists.

        That one instance should be updated whenever the preferences are updated or
        whenerver the checkbox changes.
    """

    __instance = None

    def __new__(cls):
        if TitleVisibleSingleton.__instance is None:
            TitleVisibleSingleton.__instance = object.__new__(cls)

            TitleVisibleSingleton.__instance.minimumTitleSeconds = 30
            TitleVisibleSingleton.__instance.hideShortTitles = False

        return TitleVisibleSingleton.__instance

    def __str__(self):
        return 'TitleVisibleSingleton: minimumTitleSeconds={}, hideShortTitles={}' \
            .format(self.minimumTitleSeconds, self.hideShortTitles)

    def set(self, minimumTitleSeconds, hideShortTitles):
        """ Set/update the title visible attributes.
        """

        self.minimumTitleSeconds = minimumTitleSeconds
        self.hideShortTitles = hideShortTitles

class TitleSize(object):
    """ Contains the width and height of the title.
    """

    XMLNAME = 'TitleSize'

    def __init__(self, parent):
        self.__parent = parent
        self.clear()

    def __str__(self):
        return '{}: width: {}, height: {}'.format(self.XMLNAME,
            self.width, self.height)

    def clear(self):
        """ Set all object members to their initial values.
        """
        self.width = 0
        self.height = 0

    @property
    def durationAsTimedelta(self):
        return DurationAsTimedelta(self.duration)

    @property
    def parent(self):
        return self.__parent

    @property
    def range(self):
        return '{}x{}'.format(self.width, self.height)

    def fromXML(self, element):
        """ Read the object from an XML file.
        """
        self.clear()

        self.width = XMLHelpers.GetXMLAttributeAsInt(element, 'Width', 0)
        self.height = XMLHelpers.GetXMLAttributeAsInt(element, 'Height', 0)

    def toXML(self, doc, parentElement):
        """ Write the object to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        element.setAttribute('Width', str(self.width))
        element.setAttribute('Height', str(self.height))

        return element

class Title(object):
    """ This class holds the information for a single DVD or BluRay title.
    """

    XMLNAME = 'Title'

    def __init__(self, parent):
        self.__parent = parent
        self.__titleVisibleSingleton = TitleVisibleSingleton()        # This is a singleton class.

        # The following variables are from HandBrake.
        # ===============================================
        self.titleNumber = 0

        self.vts = 0
        self.ttn = 0
        self.cells = Cells(self)
        self.blocks = 0

        self.duration = ''            # duration can vary by +- 1; maybe because of rounding?

        self.size = TitleSize(self)            # width, height
        self.pixelAspectRatio = ''
        self.displayAspectRatio = 0.0
        self.framesPerSecond = 0.0

        self.autoCrop = AutoCrop(self)

        self.chapters = Chapters(self)
        self.audioTracks = AudioTracks(self)
        self.subtitleTracks = SubtitleTracks(self)

        # The remaining variables contain state information for this title
        # ========================================================================

        self.title = ''
        self.selected = False
        self.orderNumber = 0        # Make sure Titles.setNaturalTitleOrder() is called at some point.

        self.customCrop = CustomCrop(self)
        self.audioTrackStates = AudioTrackStates(self)
        self.subtitleTrackStates = SubtitleTrackStates(self)
        self.chapterRanges = ChapterRanges(self)

        # Used by self.parse(line) to keep track of the current object type
        # (audio track, subtitle track, etc.) between calls.
        self.currentObjectType = None

        # This attribute is saved by toXML() (as a convenience) but it's not read
        # by fromXML().  Instead, it's set by refreshVisible().
        self.visible = True

    def __str__(self):
        s = '{} {}:\n' \
        '  vts: {}, ttn: {}, cells: {}->{}, blocks: {}\n' \
        '  duration: {}\n' \
        '  size: {}x{}, pixel aspect: {}, display aspect: {:.2f}, fps: {:.3f}\n' \
        '  autoCrop: {}/{}/{}/{}'.format(self.XMLNAME,
        self.titleNumber,
        self.vts, self.ttn, self.cells.first, self.cells.last, self.blocks,
        self.duration,
        self.size.width, self.size.height,
        self.pixelAspectRatio, self.displayAspectRatio, self.framesPerSecond,
        self.autoCrop.top, self.autoCrop.bottom, self.autoCrop.left, self.autoCrop.right)

        s += '\n  {}:'.format(self.chapters)
        for chapter in self.chapters:
            s += '\n    {}'.format(chapter)

        s += '\n  {}:'.format(self.audioTracks)
        for audioTrack in self.audioTracks:
            s += '\n    {}'.format(audioTrack)

        s += '\n  {}:'.format(self.subtitleTracks)
        for subtitleTrack in self.subtitleTracks:
            s += '\n    {}'.format(subtitleTrack)

        s += '\n  State data:\n' \
        '    title: "{}"\n' \
        '    selected: {}, visible: {}, orderNumber: {}\n' \
        '    crop: {}, customCrop: {}/{}/{}/{}\n'.format(self.title,
        self.selected, self.visible, self.orderNumber,
        self.customCrop.processChoice, self.customCrop.top, self.customCrop.bottom, self.customCrop.left, self.customCrop.right)

        # s += '\n  State data:\n' \
        # '    title: "{}"\n' \
        # '    selected: {}, visible: {}, orderNumber: {}\n' \
        # '    crop: {}, customCrop: {}/{}/{}/{}\n' \
        # '    audioChoice: {}\n' \
        # '      customAudioTrackState 1: {:s}\n' \
        # '      customAudioTrackState 2: {:s}\n' \
        # '      customAudioTrackState 3: {:s}\n' \
        # '    subtitlesChoice: {}\n' \
        # '      customSubtitleTrackState 1: {:s}\n' \
        # '      customSubtitleTrackState 2: {:s}\n' \
        # '      customSubtitleTrackState 3: {:s}\n' \
        # '    chapterMarkers: {}, firstChapterNumber {}\n' \
        # '    {:s}'.format(self.title,
        # self.selected, self.visible, self.orderNumber,
        # self.customCrop.processChoice, self.customCrop.top, self.customCrop.bottom, self.customCrop.left, self.customCrop.right,
        # self.audioChoice, self.customAudioTrackStates[0], self.customAudioTrackStates[1], self.customAudioTrackStates[2],
        # self.subtitlesChoice, self.customSubtitleTrackStates[0], self.customSubtitleTrackStates[1], self.customSubtitleTrackStates[2],
        # self.chapterMarkers, self.firstChapterNumber,
        # self.chapterRanges)

        return s

    def clear(self):
        """ Set all object members to their initial values.
        """

        # The following variables are from the encoder (Handbrake)
        # ===============================================================

        self.titleNumber = 0

        self.vts = 0
        self.ttn = 0
        self.cells.clear()
        self.blocks = 0

        self.duration = ''                            # duration can vary by +- 1; maybe because of rounding?

        self.size.clear()            # width, height
        self.pixelAspectRatio = ''
        self.displayAspectRatio = 0.0
        self.framesPerSecond = 0.0

        self.autoCrop.clear()        # top, bottom, left, right
        self.audioTracks.clear()
        self.subtitleTracks.clear()
        self.chapters.clear()

        # The remaining variables contain state information for this title
        # ========================================================================

        self.title = ''
        self.selected = False
        # self.orderNumber = None
        self.orderNumber = 0

        self.customCrop.clear()
        self.audioTrackStates.clear()
        self.subtitleTrackStates.clear()
        self.chapterRanges.clear()

        self.visible = True         # This attribute is not read from the XML file.
        self.currentObject = None   # This attribute is not saved in the XML file.

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

        return 'TitleNumber: {}, ' \
        'VTS: {}, TTN: {}, First Cell: {}, Last Cell: {}, Blocks: {}, ' \
        'Width: {}, Height: {}, Pixel Aspect Ratio {}, Display Aspect Ratio {}, ' \
        'Frames Per Second {}'.format(
        self.titleNumber,
        self.vts,
        self.ttn,
        self.cells.first, self.cells.last,
        self.blocks,
        self.size.width, self.size.height,
        self.pixelAspectRatio,
        self.displayAspectRatio,
        self.framesPerSecond
        )

    @property
    def parent(self):
        return self.__parent

    def fromXML(self, element):
        """ Populate the object from an XML element.
        """

        self.clear()

        # The following variables are from the encoder (Handbrake)
        # ===============================================================

        self.titleNumber = XMLHelpers.GetXMLAttributeAsInt(element, 'TitleNumber', 0)

        self.vts = XMLHelpers.GetXMLAttributeAsInt(element, 'VTS', 0)
        self.ttn = XMLHelpers.GetXMLAttributeAsInt(element, 'TTN', 0)
        self.blocks = XMLHelpers.GetXMLAttributeAsInt(element, 'Blocks', 0)

        # Legacy support: Cells was not always an object.
        if (element.hasAttribute('FirstCell')):
            self.cells.first = XMLHelpers.GetXMLAttributeAsInt(element, 'FirstCell', 0)
            self.cells.last = XMLHelpers.GetXMLAttributeAsInt(element, 'LastCell', 0)
        else:
            for childNode in element.childNodes:
                if (childNode.localName == Cells.XMLNAME):
                    self.cells.fromXML(childNode)

        self.duration = XMLHelpers.GetXMLAttribute(element, 'Duration', '').strip()

        # Legacy support: TitleSize was not always an object.
        if (element.hasAttribute('Width')):
            self.size.width = XMLHelpers.GetXMLAttributeAsInt(element, 'Width', 0)
            self.size.height = XMLHelpers.GetXMLAttributeAsInt(element, 'Height', 0)
        else:
            for childNode in element.childNodes:
                if (childNode.localName == TitleSize.XMLNAME):
                    self.size.fromXML(childNode)

        self.pixelAspectRatio = XMLHelpers.GetXMLAttribute(element, 'PixelAspectRatio', '')
        self.displayAspectRatio = XMLHelpers.GetXMLAttributeAsFloat(element, 'DisplayAspectRatio', 0.0)
        self.framesPerSecond = XMLHelpers.GetXMLAttributeAsFloat(element, 'FramesPerSecond', 0.0)

        # Legacy support: Autocrop was not always an object.
        if (element.hasAttribute('AutocropTop')):
            self.autoCrop.top = XMLHelpers.GetXMLAttributeAsInt(element, 'AutocropTop', 0)
            self.autoCrop.bottom = XMLHelpers.GetXMLAttributeAsInt(element, 'AutocropBottom', 0)
            self.autoCrop.left = XMLHelpers.GetXMLAttributeAsInt(element, 'AutocropLeft', 0)
            self.autoCrop.right = XMLHelpers.GetXMLAttributeAsInt(element, 'AutocropRight', 0)

        # The remaining variables contain state information for this title
        # ========================================================================

        self.title = XMLHelpers.GetXMLAttribute(element, 'Title', '')
        self.selected = XMLHelpers.GetXMLAttributeAsBool(element, 'Selected', False)
        self.orderNumber = XMLHelpers.GetXMLAttributeAsInt(element, 'OrderNumber', 0)

        # Legacy support: This attribute was moved to the AudioTrackStates class.
        if (element.hasAttribute('Crop')):
            self.customCrop.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'Crop',
                customCrop.PROCESS_DEFAULT, customCrop.PROCESS_CHOICES)

        # Legacy support: Customcrop was not always an object.
        if (element.hasAttribute('CustomcropTop')):
            self.customCrop.top = XMLHelpers.GetXMLAttributeAsInt(element, 'CustomcropTop', self.autoCrop.top)
            self.customCrop.bottom = XMLHelpers.GetXMLAttributeAsInt(element, 'CustomcropBottom', self.autoCrop.bottom)
            self.customCrop.left = XMLHelpers.GetXMLAttributeAsInt(element, 'CustomcropLeft', self.autoCrop.left)
            self.customCrop.right = XMLHelpers.GetXMLAttributeAsInt(element, 'CustomcropRight', self.autoCrop.right)

        # Legacy support: This attribute was moved to the AudioTrackStates class.
        if (element.hasAttribute('Audio')):
            self.audioTrackStates.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'Audio',
                AudioTrackStates.PROCESS_DEFAULT, AudioTrackStates.PROCESS_CHOICES)

        # Legacy support: This attribute was moved to the AudioTrackStates class.
        if (element.hasAttribute('Subtitles')):
            self.subtitleTrackStates.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'Subtitles',
                SubtitleTrackStates.PROCESS_DEFAULT, SubtitleTrackStates.PROCESS_CHOICES)

        # Legacy support: This attribute was moved to the Chapters class.
        if (element.hasAttribute('ChapterMarkers')):
            self.customCrop.processChoice = XMLHelpers.GetValidXMLAttribute(element, 'ChapterMarkers',
                CustomCrop.PROCESS_DEFAULT, CustomCrop.PROCESS_CHOICES)

        # Legacy support: This attribute was moved to the Chapters class.
        if (element.hasAttribute('FirstChapterNumber')):
            self.chapters.firstChapterNumber = XMLHelpers.GetXMLAttributeAsInt(element, 'FirstChapterNumber', 1)

        # ----- Child elements ----- #

        for childNode in element.childNodes:
            if (childNode.localName == AutoCrop.XMLNAME):
                self.autoCrop.fromXML(childNode)

            if (childNode.localName == Chapters.XMLNAME):
                self.chapters.fromXML(childNode)

            elif (childNode.localName == AudioTracks.XMLNAME):
                self.audioTracks.fromXML(childNode)

            elif (childNode.localName == SubtitleTracks.XMLNAME):
                self.subtitleTracks.fromXML(childNode)

            elif (childNode.localName == AudioTrackStates.XMLNAME):
                self.audioTrackStates.fromXML(childNode)

            elif (childNode.localName == SubtitleTrackStates.XMLNAME):
                self.subtitleTrackStates.fromXML(childNode)

            elif (childNode.localName == ChapterRanges.XMLNAME):
                self.chapterRanges.fromXML(childNode)

            # Legacy support: Before the creation of the AudioTrackStates object.
            elif (childNode.localName == 'CustomAudioTrack0'):
                self.audioTrackStates[0].fromXML(childNode)
            elif (childNode.localName == 'CustomAudioTrack1'):
                self.audioTrackStates[1].fromXML(childNode)
            elif (childNode.localName == 'CustomAudioTrack2'):
                self.audioTrackStates[2].fromXML(childNode)

            # Legacy support: Before the creation of the AudioTrackStates object.
            elif (childNode.localName == 'CustomSubtitleTrack0'):
                self.customSubtitleTrackStates[0].fromXML(childNode, SubtitleTrackState.SUBTITLE_TRACK_CHOICES)
            elif (childNode.localName == 'CustomSubtitleTrack1'):
                self.customSubtitleTrackStates[1].fromXML(childNode, SubtitleTrackState.SUBTITLE_TRACK_CHOICES)
            elif (childNode.localName == 'CustomSubtitleTrack2'):
                self.customSubtitleTrackStates[2].fromXML(childNode, SubtitleTrackState.SUBTITLE_TRACK_CHOICES)

        for childNode in element.childNodes:
            if (childNode.localName == CustomCrop.XMLNAME):         # This must be done after autoCrop
                self.customCrop.fromXML(childNode, self.autoCrop)

        self.refreshVisible()

    def parse(self, line):
        """ Extract the title, chapter, audio track and subtitle track information
            into the object memebers from Handbrakes output.
        """

        if (line.startswith('+ title')):
            line = line.rstrip(':')
            self.titleNumber = int(line[8:])
            self.orderNumber = None

        elif (line.startswith('  + vts')):
            line = line[4:]
            line = line.replace(' (', ', ')
            parms = line.split(', ')

            for parm in parms:
                if (parm.startswith('vts')):
                    self.vts = int(parm.split()[1])

                elif (parm.startswith('ttn')):
                    self.ttn = int(parm.split()[1])

                elif (parm.startswith('cells')):
                    cells = parm.split()[1].split('->')
                    self.cells.first = int(cells[0])
                    self.cells.last = int(cells[1])

                elif (parm.endswith('blocks)')):
                    self.blocks = int(parm.split()[0])

        elif (line.startswith('  + duration:')):
            self.duration = line[4:].split()[1]
            self.refreshVisible()

        elif (line.startswith('  + size:')):
            parms = line[4:].split(', ')

            for parm in parms:
                if (parm.startswith('size:')):
                    sizes = parm.split()[1].split('x')
                    self.size.width = int(sizes[0])
                    self.size.height = int(sizes[1])

                elif (parm.startswith('pixel aspect:')):
                    self.pixelAspectRatio = parm.split()[2]

                elif (parm.startswith('display aspect:')):
                    self.displayAspectRatio = float(parm.split()[2])

                elif (parm.endswith('fps')):
                    self.framesPerSecond = float(parm.split()[0])

        elif (line.startswith('  + autocrop:')):
            parms = line[4:].split()[1].split('/')

            self.autoCrop.top = self.customCrop.top = int(parms[0])
            self.autoCrop.bottom = self.customCrop.bottom = int(parms[1])
            self.autoCrop.left = self.customCrop.left = int(parms[2])
            self.autoCrop.right = self.customCrop.right = int(parms[3])

        elif (line.startswith('  + chapters:')):
            self.currentObjectType = Chapter.XMLNAME

        elif (line.startswith('  + audio tracks:')):
            self.currentObjectType = AudioTrack.XMLNAME

        elif (line.startswith('  + subtitle tracks:')):
            self.currentObjectType = SubtitleTrack.XMLNAME

        elif (line.startswith('    +')):
            if (self.currentObjectType == Chapter.XMLNAME):
                o = Chapter(self.chapters)
                o.parse(line)
                self.chapters.append(o)

            elif (self.currentObjectType == AudioTrack.XMLNAME):
                o = AudioTrack(self.audioTracks)
                o.parse(line)
                self.audioTracks.append(o)

            elif (self.currentObjectType == SubtitleTrack.XMLNAME):
                o = SubtitleTrack(self.subtitleTracks)
                o.parse(line)
                self.subtitleTracks.append(o)

    def refreshVisible(self):
        """ Update the 'visible' flag based on the current visiblity settings.
        """

        self.visible = True
        if (self.__titleVisibleSingleton.hideShortTitles and self.duration != ''):
            minimumTitleSeconds = datetime.timedelta(seconds=self.__titleVisibleSingleton.minimumTitleSeconds)
            if (self.durationAsTimedelta <= minimumTitleSeconds):
                self.visible = False

    def toXML(self, doc, parentElement):
        """ Create a new XML element from the title and append it to the
            parentElement.
        """

        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        # The following variables are from the encoder (Handbrake)
        # ===============================================================

        element.setAttribute('TitleNumber', str(self.titleNumber))

        element.setAttribute('VTS', str(self.vts))
        element.setAttribute('TTN', str(self.ttn))
        element.setAttribute('Blocks', str(self.blocks))

        element.setAttribute('Duration', self.duration)

        element.setAttribute('PixelAspectRatio', self.pixelAspectRatio)
        element.setAttribute('DisplayAspectRatio', str(self.displayAspectRatio))
        element.setAttribute('FramesPerSecond', str(self.framesPerSecond))

        self.cells.toXML(doc, element)
        self.size.toXML(doc, element)
        self.autoCrop.toXML(doc, element)
        self.chapters.toXML(doc, element)
        self.audioTracks.toXML(doc, element)
        self.subtitleTracks.toXML(doc, element)

        # # The remaining variables contain state information for this title
        # # ========================================================================

        element.setAttribute('Title', self.title)
        element.setAttribute('Selected', XMLHelpers.BoolToString(self.selected))
        element.setAttribute('OrderNumber', str(self.orderNumber))

        self.customCrop.toXML(doc, element)
        self.audioTrackStates.toXML(doc, element)
        self.subtitleTrackStates.toXML(doc, element)
        self.chapterRanges.toXML(doc, element)

        # These are "convenience" attributes for other applications that read the XML file.
        # They are ignored by self.fromXML().
        element.setAttribute('visible', XMLHelpers.BoolToString(self.visible))

        return element

    def updateHash(self, hash):
        """ Updates a hash object based on the title data.
        """

        hash.update(self.hashString.encode('utf-8'))

        hashString = 'Audio Track Count: {}, Subtitle Track Count: {}, Chapter Count: {}' \
        .format(len(self.audioTracks), len(self.subtitleTracks), len(self.chapters))
        hash.update(hashString.encode('utf-8'))

        for audioTrack in self.audioTracks:
            hash.update(audioTrack.hashString.encode('utf-8'))

        for subtitleTrack in self.subtitleTracks:
            hash.update(subtitleTrack.hashString.encode('utf-8'))

        for chapter in self.chapters:
            hash.update(chapter.hashString.encode('utf-8'))

class Titles(MutableSequence):
    """ Contains the information for all the titles from a DVD or BluRay.
    """

    XMLNAME = 'Titles'

    FLAG_SELECTED = 0x0001
    FLAG_VISIBLE  = 0x0002

    def __init__(self, parent):
        self.__parent = parent
        self.__titleVisibleSingleton = TitleVisibleSingleton()        # This is a singleton class.

        self.titles = []

        self.titlesById = {}
        self.titlesByTitleNumber = {}
        self.titlesByOrderNumber = {}

        # This value is not what python usually means by 'hash', 'hashable' or __hash()__.
        # In python, the hash value for an object must not change during the object's lifetime
        # and is usually derived from the object's id().  This va;ie is created using hashlib.sha256()
        # and is calculated using strings derived from the disc content (i.e. audio tracks,
        # subtitle tracks, ets.).  It is used to create a (so far) unique file name
        # based, in part, on the hashlib.sha256()hexdigest().  The file name is used by the
        # toXML() method to store the disc information.
        self.hash = None

    def __str__(self):
        return '{}: len: {}, hash: "{}"'.format(self.XMLNAME,
        len(self.titles), self.hash)

    # MutableSequence abstract methods
    # ==========================================================================
    def __getitem__(self, idx):
        return self.titles[idx]

    def __setitem__(self, idx, obj):
        assert(isinstance(obj, Title))

        self.titlesById.pop(id(self.titles[idx]))
        self.titlesByTitleNumber.pop(self.titles[idx].titleNumber)
        self.titlesByOrderNumber.pop(self.titles[idx].orderNumber)

        self.titles[idx] = obj

        self.titlesById[id(obj)] = obj
        self.titlesByTitleNumber[obj.titleNumber] = obj
        self.titlesByOrderNumber[obj.orderNumber] = obj

    def __delitem__(self, idx):
        self.titlesById.pop(id(self.titles[idx]))
        self.titlesByTitleNumber.pop(self.titles[idx].titleNumber)
        self.titlesByOrderNumber.pop(self.titles[idx].orderNumber)

        del self.titles[idx]

    def __len__(self):
        return len(self.titles)

    def insert(self, idx, obj):
        assert(isinstance(obj, Title))

        self.titles.insert(idx, obj)

        self.titlesById[id(obj)] = obj
        self.titlesByTitleNumber[obj.titleNumber] = obj
        self.titlesByOrderNumber[obj.orderNumber] = obj
    # ==========================================================================

    def clear(self):
        """ Set all object members to their initial values.
        """

        del self.titles[:]

        self.titlesById.clear()
        self.titlesByTitleNumber.clear()
        self.titlesByOrderNumber.clear()

    @property
    def hasTitles(self):
        """ Returns true if one or more title objects are present.
        """
        return (len(self.titles) > 0)

    @property
    def parent(self):
        return self.__parent

    def clearFlaggedAttributes(self, flags):
        """ Iterate through the titles.  Clear the visible and/or selected
            attributes, depending on the flags.
        """
        clearSelected = (flags & self.FLAG_SELECTED)
        clearVisible = (flags & self.FLAG_VISIBLE)

        for title in self.titles:
            if (clearSelected): title.selected = False
            if (clearVisible): title.visible = False

    def fromXML(self, element):
        """ Read the titles from an XML file.
        """

        self.clear()

        # Here's the problem: if the OrderNumber attribute is missing from the XML
        # file, all of the titles in titlesByOrderNumber will overwrite each other (index=0).
        # BUT, we don't want to setNaturalTitleOrder() unless the attribute is missing because
        # that would overwrite the order information from the XML file.  We start with
        # orderNumberFound=True because we want to setNaturalTitleOrder() if any
        # title doesn't have an OrderNumber attribute.
        orderNumberFound = True

        for childNode in element.childNodes:
            if (childNode.localName == Title.XMLNAME):
                title = Title(self)
                title.fromXML(childNode)

                self.append(title)

                if (not childNode.hasAttribute('OrderNumber')):
                    orderNumberFound = False

        if (not orderNumberFound):
            self.setNaturalTitleOrder()
        self.refreshVisible()

        # Store the hash so it's not constantly being re-calculate.  It should never change.
        self.hash = self.getHash()

    def getById(self, objectId):
        """ Returns the title based on it's python object id.
        """
        assert (objectId in self.titlesById.keys())

        return self.titlesById[objectId]

    def getByTitleNumber(self, titleNumber):
        """ Returns the title for a title number.

            Returns None if the requested track doesn't exist.
        """
        if (titleNumber in self.titlesByTitleNumber.keys()):
            return self.titlesByTitleNumber[titleNumber]

        return None

    def getByOrderNumber(self, orderNumber):
        """ Returns the title for a title number.

            Returns None if the requested track doesn't exist.
        """
        if (orderNumber in self.titlesByOrderNumber.keys()):
            return self.titlesByOrderNumber[orderNumber]

        return None

    def getHash(self):
        """ Returns a string containing the hash value calculated from the titles.
        """
        if (not len(self.titles)):
            return None

        hash = hashlib.sha256()

        hashString = "Title Count: {}".format(len(self.titles))
        hash.update(hashString.encode('utf-8'))

        titleKeys = sorted(self.titlesByTitleNumber.keys())
        for titleKey in titleKeys:
            title = self.titlesByTitleNumber[titleKey]
            title.updateHash(hash)

        return hash.hexdigest()

    def hasAudioTrackNumber(self, titleNumber, audioTrackNumber):
        """ Verify existence of a specific audio track in a specific title
            and return True/False if the audio track is found.

            Always return false if the title is not found.
        """
        if (titleNumber in self.titlesByTitleNumber.keys()):
            return self.titlesByTitleNumber[titleNumber].hasAudioTrackNumber(audioTrackNumber)

        return False

    def hasAudioTrack(self):
        """ Returns true if at least on title has at least one audio track.
        """
        for title in self.titles:
            if (len(title.audioTracks)):
                return True

        return False

    def hasSubtitleTrackNumber(self, titleNumber, subtitleTrackNumber):
        """ Verify existence of a specific subtitle track in a specific title
            and return True/False if the subtitle track is found.

            Always return false if the title is not found.
        """
        if (titleNumber in self.titlesByTitleNumber.keys()):
            return self.titlesByTitleNumber[titleNumber].hasSubtitleTrackNumber(subtitleTrackNumber)

        return False

    def hasSubtitleTrack(self):
        """ Returns true if at least on title has at least one subtitle track.
        """
        for title in self.titles:
            if (len(title.subtitleTracks)):
                return True

        return False

    def hasTitleNumber(self, titleNumber):
        """ Returns true/false if a track number exists.
        """
        if (titleNumber in self.titlesByTitleNumber.keys()):
            return True

        return False

    def matchingTitles(self, flags=0):
        """ We always want to return something; so either a list of titles that
            match the flags or a default title.  This method returns a named
            tuple containing:

            matchingTitles - A list of titles that match the flags (ex. visible,
                selected).  The list will be empty if none of the titles match.

            longestMatchingTitle: The longest title in the matchingTitles list.
                This will be None if the list is empty.

            defaultTitle - This is complicated.  The default title is None if
                matchingTitles are found.

                First: It's the first selected, visible title
                Then:  It's the first selected title
                Then:  It's the first visible title
                Then:  It's the first title in the list

            longestTitle: The longest title in the original titles list.

            The matchingTitles list is orderd by Title.orderNumber, not by
            Title.titleNumber.
        """
        if (not self.hasTitles):
            return MatchingTitles([], None, None, None)

        wantSelected = (flags & self.FLAG_SELECTED)
        wantVisible = (flags & self.FLAG_VISIBLE)

        matchingTitles = []
        longestMatchingTitle = None
        defaultTitle = None
        longestTitle = self.titles[0]
        longestTitleLength = longestTitle.durationAsTimedelta

        firstSelectedVisibleTitle = None
        firstSelectedTitle = None
        firstVisibleTitle = None

        # Iterate through the list of titles, finding the titles we want.
        titleKeys = sorted(self.titlesByOrderNumber.keys())
        for key in titleKeys:
            title = self.titlesByOrderNumber[key]

            if (title.selected
            and title.visible
            and firstSelectedVisibleTitle is None):
                firstSelectedVisibleTitle = title

            if (title.selected and (firstSelectedTitle is None)):
                firstSelectedTitle = title

            if (title.visible and (firstVisibleTitle is None)):
                firstVisibleTitle = title

            titleLength = title.durationAsTimedelta
            if (titleLength > longestTitleLength):
                longestTitleLength = titleLength
                longestTitle = title

            if (wantSelected and (not title.selected)):
                continue

            if (wantVisible and (not title.visible)):
                continue

            matchingTitles.append(title)

        if (len(matchingTitles)):
            # Check the list of titles.  Find the longest one.,
            longestMatchingTitle = matchingTitles[0]
            longestMatchingTitleLength = longestTitle.durationAsTimedelta

            for title in matchingTitles:
                titleLength = title.durationAsTimedelta
                if (titleLength > longestMatchingTitleLength):
                    longestMatchingTitle = titleLength
                    longestMatchingTitle = title
        else:
            # Select a default title because none of the titles passed the filters.
            if (firstSelectedVisibleTitle is not None):
                defaultTitle = firstSelectedVisibleTitle
            elif (firstSelectedTitle is not None):
                defaultTitle = firstSelectedTitle
            elif (firstVisibleTitle is not None):
                defaultTitle = firstVisibleTitle
            else:
                defaultTitle = self.titles[0]

        return MatchingTitles(matchingTitles, longestMatchingTitle, defaultTitle,
            longestTitle)

    def moveBottom(self, title):
        """ Re-order the titles moving the selected title to the end of the list.
        """
        orderNumber = title.orderNumber
        lastOrderNumber = len(self.titles) - 1
        if (orderNumber == lastOrderNumber):
            return

        for i in range(orderNumber, lastOrderNumber):
            swapTitle = self.getByOrderNumber(i + 1)
            swapTitle.orderNumber = i
            self.titlesByOrderNumber[i] = swapTitle

        title.orderNumber = lastOrderNumber
        self.titlesByOrderNumber[lastOrderNumber] = title

    def moveDown(self, title):
        """ Re-order the titles moving the selected title down by one.
        """
        # Here's where the visible/not visible thing gets tricky.  We don't
        # just want to move below the next item, we want to move below the
        # next VISIBLE item.

        lastOrderNumber = len(self.titles) - 1
        while (True):
            orderNumber = title.orderNumber
            if (orderNumber >= lastOrderNumber):
                return

            swapOrderNumber = orderNumber + 1
            if (swapOrderNumber not in self.titlesByOrderNumber):
                return

            swapTitle = self.titlesByOrderNumber[swapOrderNumber]
            self.__swapTitleOrders(title, swapTitle)

            if (swapTitle.visible):
                break

    def moveTop(self, title):
        """ Re-order the titles moving the selected title to the beginning of
            the list.
        """

        orderNumber = title.orderNumber
        if (not orderNumber):
            return

        for i in range(orderNumber, 0, -1):
            swapTitle = self.getByOrderNumber(i - 1)
            swapTitle.orderNumber = i
            self.titlesByOrderNumber[i] = swapTitle

        title.orderNumber = 0
        self.titlesByOrderNumber[0] = title

    def moveUp(self, title):
        """ Re-order the titles moving the selected title up by one.
        """
        # Here's where the visible/not visible thing gets tricky.  We don't
        # just want to move above the next item, we want to move above the
        # next VISIBLE item.

        while (True):
            orderNumber = title.orderNumber
            if (orderNumber <= 0):
                return

            swapOrderNumber = orderNumber - 1
            if (swapOrderNumber not in self.titlesByOrderNumber):
                return

            swapTitle = self.titlesByOrderNumber[swapOrderNumber]
            self.__swapTitleOrders(title, swapTitle)

            if (swapTitle.visible):
                break

    def __swapTitleOrders(self, titleA, titleB):
        """ Swap the posisions of the titles in the titlesByOrderNumber map.
        """
        orderNumberA = titleA.orderNumber
        orderNumberB = titleB.orderNumber

        titleA.orderNumber = orderNumberB
        titleB.orderNumber = orderNumberA

        self.titlesByOrderNumber[titleA.orderNumber] = titleA
        self.titlesByOrderNumber[titleB.orderNumber] = titleB

    def parse(self, buffer):
        """ Parse the output from the HandBrake command line and extract the
            title information.  Use the informtion to create Title objects.
        """
        self.clear()

        lines = buffer.split('\n')

        currentTitle = None
        for line in lines:
            line = line.rstrip()
            print (line)

            if (line.lstrip().startswith('+ ')):
                if (line.startswith('+ title')):

                    if (currentTitle is not None):
                        self.append(currentTitle)

                    currentTitle = Title(self)
                    currentTitle.parse(line)

                else:
                    if (currentTitle is not None):
                        currentTitle.parse(line)

        if (currentTitle is not None):
            self.append(currentTitle)

        self.setNaturalTitleOrder()
        self.refreshVisible()

        # Store the hash so it's not constantly being re-calculate.  It should never change.
        self.hash = self.getHash()

    def refreshVisible(self):
        """ Update the 'visible' flag for all titles.
        """
        for title in self.titles:
            title.refreshVisible()

    def setNaturalTitleOrder(self):
        """ Sets the titles to their natural (default) order.
        """
        self.titlesByOrderNumber.clear()
        orderNumber = 0

        titleNumbers = sorted(self.titlesByTitleNumber.keys())

        for titleNumber in titleNumbers:
            title = self.getByTitleNumber(titleNumber)
            title.orderNumber = orderNumber
            self.titlesByOrderNumber[orderNumber] = title
            orderNumber += 1

    def toXML(self, doc, parentElement):
        """ Write the titles to an XML file.
        """
        element = doc.createElement(self.XMLNAME)
        parentElement.appendChild(element)

        # These are "convenience" attributes for other applications that read the XML file.
        # They are ignored by self.fromXML().
        element.setAttribute('hash', self.hash)
        element.setAttribute('count', str(len(self.titles)))

        for title in self.titles:
            title.toXML(doc, element)

        return element

if __name__ == '__main__':

    import os, xml.dom, xml.dom.minidom as minidom

    titleVisibleSingleton = TitleVisibleSingleton()
    print (titleVisibleSingleton)
    titleVisibleSingleton.set(45, True)
    print (TitleVisibleSingleton())

    discTitles = Titles(None)
    print (discTitles)
    print ()

    # ********************************************************
    filename = 'TestFiles/TestTitles.xml'
    elementName = 'TestTitles'
    if (os.path.exists(filename)):
        doc = minidom.parse(filename)
        print ('{} read.'.format(filename))

        if (doc.documentElement.nodeName != elementName):
            print ('Can''t find element "{}" in "{}".'.format(elementName, filename))
        else:
            childNode = doc.documentElement.childNodes[1]
            if (childNode.localName == Titles.XMLNAME):
                discTitles.fromXML(childNode)
                print (discTitles)
                for discTitle in discTitles:
                    print (discTitle)
            else:
                print ('Can''t find element "{}" in "{}".'.format(Titles.XMLNAME, filename))
        print ()

    print (discTitles)
    for discTitle in discTitles:
        print (discTitle)
    print ()

    # ********************************************************
    filename = 'TestFiles/test.buffer'
    if (os.path.exists(filename)):
        with open('TestFiles/test.buffer', 'r') as f:
            buffer = f.read()
    else:
        print ('ERROR!  Unable to find file "{}".'.format(filename))
        sys.exit(1)

    discTitles.parse(buffer)

    discTitles[0].chapterRanges.addEpisode(1, 3, 'Testing')

    print (discTitles)
    for discTitle in discTitles:
        print (discTitle)
    print ()

    # ********************************************************

    discTitles.moveDown(discTitles[0])
    discTitles.moveUp(discTitles[-1])
    discTitles.moveBottom(discTitles[0])
    discTitles.moveTop(discTitles[-1])

    # ============================================================
    dom = minidom.getDOMImplementation()
    doc = dom.createDocument(None, 'TestTitles', None)
    parentElement = doc.documentElement

    discTitles.toXML(doc, parentElement)

    xmlFile = open('TestFiles/TestTitles.xml', 'w')
    doc.writexml(xmlFile, '', '\t', '\n')
    xmlFile.close()

    doc.unlink()
