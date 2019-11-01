# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 CERN
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.
#

from .dep_file import File
import logging

class SourceFileSet(set):

    """Class providing a extension of the 'set' object that includes
    methods that allow for an easier management of a collection of HDL
    source files"""

    def __init__(self):
        super(SourceFileSet, self).__init__()
        self = []

    def add(self, files):
        """Add a set of files to the source fileset instance"""
        if files is None:
            logging.debug("Got None as a file.\n Ommiting")
            return
        if isinstance(files, (SourceFileSet, set)):
            for file_aux in files:
                super(SourceFileSet, self).add(file_aux)
        else:
            assert isinstance(files, File)
            super(SourceFileSet, self).add(files)

    def filter(self, filetype):
        """Method that filters and returns all of the HDL source files
        contained in the instance SourceFileSet matching the provided type"""
        out = SourceFileSet()
        for file_aux in self:
            if isinstance(file_aux, filetype):
                out.add(file_aux)
        return out

    def sort(self):
        """Return a sorted list of the fileset.  This is useful to have always
        the same output"""
        return sorted(self, key=(lambda x: x.path))

