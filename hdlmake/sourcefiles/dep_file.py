#!/usr/bin/python
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
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

"""Module providing the Classes used to provide and handle dependable files"""

from __future__ import absolute_import
from __future__ import print_function
import os
import logging

from ..util import path as path_mod
import six


class DepRelation(object):

    """Class used to create instances representing HDL dependency relations"""

    # rel_type
    # Architecture is never required.
    ENTITY = 1
    PACKAGE = 2
    ARCHITECTURE = 3
    MODULE = ENTITY

    def __init__(self, obj_name, lib_name, rel_type):
        assert rel_type in [
            DepRelation.ENTITY,
            DepRelation.PACKAGE,
            DepRelation.ARCHITECTURE,
            DepRelation.MODULE]
        self.rel_type = rel_type
        self.obj_name = obj_name.lower()
        self.lib_name = None if lib_name is None else lib_name.lower()

    def satisfies(self, rel_b):
        """Check if the current dependency relation matches the provided one"""
        return (rel_b.rel_type == self.rel_type 
                and rel_b.obj_name == self.obj_name
                and rel_b.lib_name == self.lib_name)

    def __repr__(self):
        ostr = {
            self.ENTITY: "entity",
            self.PACKAGE: "package",
            self.ARCHITECTURE: "architecture",
            self.MODULE: "module"}
        return "%s '%s.%s'" % (ostr[self.rel_type],
                               self.lib_name or '',
                               self.obj_name)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


class File(object):

    """This is the base class for all of the different files in HDLMake"""

    def __init__(self, path, module=None):
        self.path = path
        assert not isinstance(module, six.string_types)
        self.module = module

    @property
    def name(self):
        """Property defined as a method that gets the basename of the file
        path, i.e. it strips the path and takes the full file name"""
        return os.path.basename(self.path)

    @property
    def purename(self):
        """Property defined as a method that gets the name of the file
        and strips put the extension from the file"""
        return os.path.splitext(self.name)[0]

    @property
    def dirname(self):
        """Property defined as a method that gets the name of the directory
        in which the file is stored"""
        return os.path.dirname(self.path)

    def rel_path(self, directory=None):
        """Returns the relative path for the file calculated with (directory)
        as the origin reference -- if none, it will be defaulted to current
        folder from which we are launching the program"""
        if directory is None:
            directory = os.getcwd()
        return path_mod.relpath(self.path, directory)

    def __str__(self):
        return self.path

    def __hash__(self):
        return hash(self.path)

    def extension(self):
        """Method that gets the extension for the file instance"""
        tmp = self.path.rsplit('.')
        ext = tmp[len(tmp) - 1]
        return ext


class DepFile(File):

    """Class that serves as base to all those HDL files that can be
    parsed and solved (Verilog, SystemVerilog, VHDL).  Inherit from
    File but also provides dependencies"""

    def __init__(self, path, module):
        assert isinstance(path, six.string_types)
        File.__init__(self, path=path, module=module)
        self.provides = set()
        self.requires = set()
        self.depends_on = set()     # Set of files this file depends on.
        self.included_files = set()
        self.dep_level = None
        self.is_parsed = False

    def add_require(self, rel):
        """Add dependency :param rel:"""
        self.requires.add(rel)

    def add_provide(self, rel):
        """Add provide :param rel:"""
        self.provides.add(rel)

    def satisfies(self, rel_b):
        """Check if any of the file object relations match any of the relations
        listed in the parameter (rel_b)"""
        assert isinstance(rel_b, DepRelation)
        # self._parse_if_needed()
        return any([x.satisfies(rel_b) for x in self.provides])

    def get_dep_level(self):
        """Get the dependency level for the file instance, so we can order
        later the full fileset"""
        if self.dep_level is None:
            if len(self.depends_on) == 0:
                self.dep_level = 0
            else:
                # set dep_level to a negative value so we can detect
                # if the recusion below brings us back to
                # this file in a circular reference, that would otherwise
                # result in an infinite loop.
                self.dep_level = -1
                # recurse, to find the largest number of levels below.
                self.dep_level = 1 + \
                    max([dep.get_dep_level() for dep in self.depends_on])
        elif self.dep_level < 0:
            logging.warning("Probably run into a circular reference of file "
                            "dependencies. It appears %s depends on itself, "
                            "indirectly via atleast one other file.",
                            self.path)
        return self.dep_level
