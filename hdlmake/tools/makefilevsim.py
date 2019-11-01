#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
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
#

"""Module providing common stuff for Modelsim, Vsim... like simulators"""

from __future__ import absolute_import
import os
import string

from .makefilesim import MakefileSim
from ..util import shell
from ..sourcefiles.srcfile import VerilogFile, VHDLFile, SVFile
from ..util import path as path_mod
import six


class MakefileVsim(MakefileSim):

    """A Makefile writer for simulation suitable for vsim based simulators.

    Currently used by:
      - Modelsim
      - Riviera
    """

    HDL_FILES = {VerilogFile: '', VHDLFile: '', SVFile: ''}

    def __init__(self):
        super(MakefileVsim, self).__init__()
        # These are variables that will be set in the makefile
        # The key is the variable name, and the value is the variable value
        self.custom_variables = {}
        # Additional sim dependencies (e.g. modelsim.ini)
        self.additional_deps = []
        # These are files copied into your working directory by a make rule
        # The key is the filename, the value is the file source path
        self.copy_rules = {}

    def _makefile_sim_options(self):
        """Print the vsim options to the Makefile"""
        def __get_rid_of_vsim_incdirs(vlog_opt=""):
            """Parse the VLOG options and purge the included dirs"""
            if not vlog_opt:
                vlog_opt = ""
            vlogs = vlog_opt.split(' ')
            ret = []
            for vlog_aux in vlogs:
                if not vlog_aux.startswith("+incdir+"):
                    ret.append(vlog_aux)
            return ' '.join(ret)
        vcom_flags = "-quiet " + self.manifest_dict.get("vcom_opt", '')
        vsim_flags = "" + self.manifest_dict.get("vsim_opt", '')
        vlog_flags = "-quiet " + __get_rid_of_vsim_incdirs(
            self.manifest_dict.get("vlog_opt", ''))
        vmap_flags = "" + self.manifest_dict.get("vmap_opt", '')
        for var, value in six.iteritems(self.custom_variables):
            self.writeln("%s := %s" % (var, value))
        self.writeln()
        self.writeln("VCOM_FLAGS := %s" % vcom_flags)
        self.writeln("VSIM_FLAGS := %s" % vsim_flags)
        self.writeln("VLOG_FLAGS := %s" % vlog_flags)
        self.writeln("VMAP_FLAGS := %s" % vmap_flags)

    def _makefile_sim_compilation(self):
        """Write a properly formatted Makefile for the simulator.
        The Makefile format is shared, but flags, dependencies, clean rules,
        etc are defined by the specific tool.
        """
        fileset = self.fileset
        if self.manifest_dict.get("include_dirs") is None:
            self.writeln("INCLUDE_DIRS :=")
        else:
            self.writeln("INCLUDE_DIRS := +incdir+%s" %
                ('+'.join(self.manifest_dict.get("include_dirs"))))
        libs = sorted(set(f.library for f in fileset))
        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        # tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib + shell.makefile_slash_char() +
                   "." + lib for lib in libs]))
        self.write('\n')
        self.writeln()
        self.writeln(
            "simulation: %s $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ)" %
            (' '.join(self.additional_deps)),)
        self.writeln("$(VERILOG_OBJ): " + ' '.join(self.additional_deps))
        self.writeln("$(VHDL_OBJ): $(LIB_IND) " + ' '.join(self.additional_deps))
        self.writeln()
        for filename, filesource in six.iteritems(self.copy_rules):
            self.writeln("{}: {}".format(filename, filesource))
            self.writeln("\t\t{} $< . 2>&1".format(shell.copy_command()))
        for lib in libs:
            self.write(lib + shell.makefile_slash_char() + "." + lib + ":\n")
            self.writeln("\t(vlib {lib} && vmap $(VMAP_FLAGS) {lib} "
                         "&& {touch} {lib}{slash}.{lib}) || {rm} {lib}".format(
                lib=lib, touch=shell.touch_command(), slash=shell.makefile_slash_char(),
                rm=shell.del_command()))
            self.writeln()
        # rules for all _primary.dat files for sv
        for vlog in fileset.filter(VerilogFile).sort():
            self._makefile_sim_file_rule(vlog)
            self.writeln("\t\tvlog -work {library} $(VLOG_FLAGS) {sv_option} $(INCLUDE_DIRS) $<".format(
                library=vlog.library, sv_option="-sv" if isinstance(vlog, SVFile) else ""))
            self._makefile_touch_stamp_file()
            self.writeln()
        # list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile).sort():
            self._makefile_sim_file_rule(vhdl)
            self.writeln("\t\tvcom $(VCOM_FLAGS) -work {} $< ".format(vhdl.library))
            self._makefile_touch_stamp_file()
            self.writeln()
