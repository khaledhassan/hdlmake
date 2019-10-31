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

    def _get_stamp_file(self, dep_file):
        name = dep_file.purename
        return os.path.join(dep_file.library, name, ".{}_{}".format(name, dep_file.extension()))

    def _makefile_sim_compilation(self):
        """Write a properly formatted Makefile for the simulator.
        The Makefile format is shared, but flags, dependencies, clean rules,
        etc are defined by the specific tool.
        """
        def __create_copy_rule(name, src):
            """Get a Makefile rule named name, which depends on src,
            copying it to the local directory."""
            rule = """%s: %s
\t\t%s $< . 2>&1
""" % (name, src, shell.copy_command())
            return rule

        cwd = os.getcwd()
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
        self.writeln("$(VERILOG_OBJ) : " + ' '.join(self.additional_deps))
        self.writeln("$(VHDL_OBJ): $(LIB_IND) " + ' '.join(self.additional_deps))
        self.writeln()
        for filename, filesource in six.iteritems(self.copy_rules):
            self.write(__create_copy_rule(filename, filesource))
        for lib in libs:
            self.write(lib + shell.makefile_slash_char() + "." + lib + ":\n")
            self.write("\t(vlib {0} && vmap $(VMAP_FLAGS) {0} && {1} {0}{2}.{0})".format(
                lib, shell.touch_command(), shell.makefile_slash_char()))
            self.write(" || {} {}\n\n".format(shell.del_command(), lib))
        # rules for all _primary.dat files for sv
        for vlog in fileset.filter(VerilogFile).sort():
            self.write("%s: %s" % (self._get_stamp_file(vlog), vlog.rel_path()))
            # list dependencies, do not include the target file
            for dep_file in sorted(vlog.depends_on, key=(lambda x: x.path)):
                if dep_file is not vlog:
                    self.write(" \\\n" + self._get_stamp_file(dep_file))
            for dep_file in sorted(vlog.included_files):
                    self.write(" \\\n{}".format(path_mod.relpath(dep_file, cwd)))
            self.writeln()
            compile_template = string.Template(
                "\t\tvlog -work ${library} $$(VLOG_FLAGS) "
                "${sv_option} $${INCLUDE_DIRS} $$<")
            compile_line = compile_template.substitute(
                library=vlog.library, sv_option="-sv"
                if isinstance(vlog, SVFile) else "")
            self.writeln(compile_line)
            self.write("\t\t@" + shell.mkdir_command() + " $(dir $@)")
            self.writeln(" && " + shell.touch_command() + " $@ \n\n")
            self.writeln()
        # list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile).sort():
            # each .dat depends on corresponding .vhd file
            self.write("%s: %s" % (self._get_stamp_file(vhdl), vhdl.rel_path()))
            # list dependencies, do not include the target file
            for dep_file in sorted(vhdl.depends_on, key=(lambda x: x.path)):
                if dep_file is vhdl:
                    continue
                self.write(" \\\n" + self._get_stamp_file(dep_file))
            self.writeln()
            self.writeln("\t\tvcom $(VCOM_FLAGS) -work {} $< ".format(vhdl.library))
            self.writeln("\t\t@" + shell.mkdir_command() +
                " $(dir $@) && " + shell.touch_command() + " $@ \n\n")
