#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
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

"""Module providing the core functionality for writing Makefiles"""

from __future__ import absolute_import
import os
import logging
import six

from ..util import shell
from ..util import path as path_mod


class ToolMakefile(object):

    """Class that provides the Makefile writing methods and status"""

    HDL_FILES = {}
    TOOL_INFO = {}
    STANDARD_LIBS = []
    CLEAN_TARGETS = {}
    SUPPORTED_FILES = {}

    def __init__(self):
        super(ToolMakefile, self).__init__()
        self._file = None
        self._initialized = False
        self.fileset = None
        self.manifest_dict = {}
        self._filename = "Makefile"

    def __del__(self):
        if self._file:
            self._file.close()

    def get_standard_libs(self):
        """Get the standard libs supported by the tool"""
        return self.STANDARD_LIBS

    def get_parseable_files(self):
        """Get the parseable HDL file types supported by the tool"""
        return self.HDL_FILES

    def get_privative_files(self):
        """Get the privative format file types supported by the tool"""
        return self.SUPPORTED_FILES

    def makefile_setup(self, top_manifest, fileset, filename=None):
        """Set the Makefile configuration"""
        self.manifest_dict = top_manifest.manifest_dict
        self.fileset = fileset
        if filename:
            self._filename = filename

    def _get_path(self):
        """Get the directory in which the tool binary is at Host"""
        bin_name = self.get_tool_bin()
        locations = shell.which(bin_name)
        if len(locations) == 0:
            return None
        logging.debug("location for %s: %s", bin_name, locations[0])
        return os.path.dirname(locations[0])

    def _is_in_path(self, path_key):
        """Check if the directory is in the system path"""
        path = self.manifest_dict.get(path_key)
        bin_name = self.get_tool_bin()
        return os.path.exists(os.path.join(path, bin_name))

    def _check_in_system_path(self):
        """Check if if in the system path exists a file named (name)"""
        return self._get_path() is not None

    def get_tool_bin(self):
        if shell.check_windows_tools():
            return self.TOOL_INFO["windows_bin"]
        else:
            return self.TOOL_INFO["linux_bin"]

    def get_stamp_file(self, dep_file):
        """Stamp file for source file :param file:"""
        name = dep_file.purename
        return os.path.join(dep_file.library, name, ".{}_{}".format(name, dep_file.extension()))

    def _makefile_touch_stamp_file(self):
        self.write("\t\t@" + shell.mkdir_command() + " $(dir $@)")
        self.writeln(" && " + shell.touch_command()  + " $@\n")

    def makefile_check_tool(self, path_key):
        """Check if the binary is available in the O.S. environment"""
        name = self.TOOL_INFO['name']
        logging.debug("Checking if " + name + " tool is available on PATH")
        if path_key in self.manifest_dict:
            if self._is_in_path(path_key):
                logging.info("%s found under HDLMAKE_%s: %s",
                             name, path_key.upper(),
                             self.manifest_dict[path_key])
            else:
                logging.warning("%s NOT found under HDLMAKE_%s: %s",
                                name, path_key.upper(),
                                self.manifest_dict[path_key])
                self.manifest_dict[path_key] = ''
        else:
            if self._check_in_system_path():
                self.manifest_dict[path_key] = self._get_path()
                logging.info("%s found in system PATH: %s",
                             name, self.manifest_dict[path_key])
            else:
                logging.warning("%s cannnot be found in system PATH", name)
                self.manifest_dict[path_key] = ''

    def makefile_includes(self):
        """Add the included makefiles that need to be previously loaded"""
        if self.manifest_dict.get("incl_makefiles") is not None:
            for file_aux in self.manifest_dict["incl_makefiles"]:
                if os.path.exists(file_aux):
                    self.writeln("include %s" % file_aux)
            self.writeln()

    def makefile_clean(self):
        """Print the Makefile target for cleaning intermediate files"""
        self.writeln("CLEAN_TARGETS := $(LIBS) " +
            ' '.join(self.CLEAN_TARGETS["clean"]) + "\n")
        self.writeln("clean:")
        tmp = "\t\t" + shell.del_command() + " $(CLEAN_TARGETS)"
        self.writeln(tmp)
        if shell.check_windows_commands():
            tmp = "\t\t@-" + shell.rmdir_command() + \
            " $(CLEAN_TARGETS) >nul 2>&1"
            self.writeln(tmp)

    def makefile_mrproper(self):
        """Print the Makefile target for cleaning final files"""
        self.writeln("mrproper: clean")
        tmp = "\t\t" + shell.del_command() + \
            " " + ' '.join(self.CLEAN_TARGETS["mrproper"]) + "\n"
        self.writeln(tmp)

    def initialize(self):
        """Open the Makefile file and print a header"""
        if os.path.exists(self._filename):
            os.remove(self._filename)

        self._file = open(self._filename, "w")
        self.writeln("########################################")
        self.writeln("#  This file was generated by hdlmake  #")
        self.writeln("#  http://ohwr.org/projects/hdl-make/  #")
        self.writeln("########################################")
        self.writeln()

    def makefile_close(self):
        self._file.close()
        self._file = None

    def write(self, line=None):
        """Write a string in the manifest, no new line"""
        if not self._initialized:
            self._initialized = True
            self.initialize()
        if shell.check_windows_commands():
            self._file.write(line.replace('\\"', '"'))
        else:
            self._file.write(line)

    def writeln(self, text=None):
        """Write a string in the manifest, automatically add new line"""
        if text is None:
            self.write("\n")
        else:
            self.write(text + "\n")
