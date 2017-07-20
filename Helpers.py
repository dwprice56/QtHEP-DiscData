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

import datetime, os.path, sys

sys.path.insert(0, '../Helpers')

from PyHelpers import GetVolumeLabel

def DurationAsTimedelta(duration):
    """ Convert a string in HH:MM:SS format to a datetime.timedelta object.
    """
    bits = duration.split(':')
    return datetime.timedelta(hours=int(bits[0]), minutes=int(bits[1]), seconds=int(bits[2]))

def TimedeltaAsDuration(td):
    """ Convert datetime.timedelta object to a string in HH:MM:SS format.
    """
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

def GetFolderVolumeLabel(folder):
    """ Get the volume label for the disk where the folder is located.

        Windows drives may or may not have volume labels.  If we're running on
        Windows and the drive has a volume label, use it.

        If we're not running on Windows, or if the drive does not have a label,
        look for a ".volumeLabel" file in the folder (if present).  If it's not
        there, look for it one folder level up.  When/if it's found, read the
        first line and use that as the volume label.
    """
    volumeLabel = ''
    if (sys.platform == 'win32'):
        volumeLabel = GetVolumeLabel(folder)

    if (not volumeLabel):
        volumeLabelFilename = os.path.join(folder, '.volumelabel')
        if (not os.path.exists(volumeLabelFilename)):
            head, tail = os.path.split(folder)
            if (head):
                volumeLabelFilename = os.path.join(head, '.volumelabel')
                if (not os.path.exists(volumeLabelFilename)):
                    volumeLabelFilename = ''
            else:
                volumeLabelFilename = ''

    if (volumeLabelFilename):
        with open(volumeLabelFilename, 'r') as f:
            volumeLabel = f.readline().strip()

    return volumeLabel
