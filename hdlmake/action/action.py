#!/usr/bin/python
# -*- coding: utf-8 -*-
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

"""This module provides the common stuff for the different supported actions"""


from __future__ import print_function
from __future__ import absolute_import
import os
import logging
import sys

from ..tools.load_tool import load_syn_tool, load_sim_tool
from ..util import shell
from ..sourcefiles import new_dep_solver as dep_solver
from ..sourcefiles.srcfile import VHDLFile, VerilogFile, SVFile
from ..sourcefiles.sourcefileset import SourceFileSet
from ..module.module import Module, ModuleArgs
from ..sourcefiles import systemlibs

class Action(object):

    """This is the base class providing the common Action methods"""

    def __init__(self, options):
        super(Action, self).__init__()
        self.top_manifest = None
        self.all_manifests = []
        self.system_libs = set()
        self.parseable_fileset = SourceFileSet()
        self.privative_fileset = SourceFileSet()
        self.options = options

    def new_module(self, parent, url, source, fetchto):
        """Add new module to the pool.

        This is the only way to add new modules to the pool
        Thanks to it the pool can easily control its content
        """
        # If the module is already present, do not create it.
        for mod in self.all_manifests:
            if mod.url == url:
                return None
        args = ModuleArgs()
        args.set_args(parent, url, source, fetchto)
        res = Module(args, self)
        self.all_manifests.append(res)
        return res

    def add_system_lib(self, parent, url):
        if url not in self.system_libs:
            if url not in systemlibs.all_system_libs:
                raise Exception("Unknown system module '{}' in '{}'".format(url, parent))
            self.system_libs.add(url)

    def load_all_manifests(self):
        # Load the top level module (which is in the current directory).
        assert self.top_manifest is None
        self.top_manifest = self.new_module(parent=None,
                                            url=os.getcwd(),
                                            source=None,
                                            fetchto=".")
        # Parse the top manifest and all sub-modules.
        self.top_manifest.parse_manifest()

    def setup(self):
        """Set tool and top_entity"""
        top_dict = self.top_manifest.manifest_dict
        action = top_dict.get("action")
        if action == None:
            self.tool = None
            self.top_entity = top_dict.get("top_module")
        elif action == "simulation":
            tool = top_dict.get("sim_tool")
            if tool is None:
                raise Exception("'sim_tool' variable is not defined")
            self.tool = load_sim_tool(tool)
            self.top_entity = top_dict.get("sim_top") \
                or top_dict.get("top_module")
            top_dict["sim_top"] = self.top_entity
        elif action == "synthesis":
            tool = top_dict.get("syn_tool")
            if tool is None:
                raise Exception("'syn_tool' variable is not defined")
            self.tool = load_syn_tool(tool)
            self.top_entity = top_dict.get("syn_top") \
                or top_dict.get("top_module")
            top_dict["syn_top"] = self.top_entity
        else:
            raise Exception("Unknown requested action: {}".format(action))

    def _build_complete_file_set(self):
        """Build file set with all the files listed in the complete pool"""
        logging.debug("Begin build complete file set")
        all_manifested_files = SourceFileSet()
        for manifest in self.all_manifests:
            all_manifested_files.add(manifest.files)
        logging.debug("End build complete file set")
        return all_manifested_files

    def build_file_set(self):
        """Initialize the parseable and privative fileset contents"""
        all_files = self._build_complete_file_set()
        for file_aux in all_files:
            if self.tool:
                if any(isinstance(file_aux, file_type)
                       for file_type in self.tool.get_parseable_files()):
                    self.parseable_fileset.add(file_aux)
                elif any(isinstance(file_aux, file_type)
                       for file_type in self.tool.get_privative_files()):
                    self.privative_fileset.add(file_aux)
                else:
                    logging.debug("File not supported by the tool: %s",
                                  file_aux.path)
            else:
                # Not usual case: tool is not known
                if any(isinstance(file_aux, file_type)
                       for file_type in [VHDLFile, VerilogFile, SVFile]):
                    self.parseable_fileset.add(file_aux)
                else:
                    self.privative_fileset.add(file_aux)
        if len(self.privative_fileset) > 0:
            # Do we need to warn about those files ?  This may simply confuse the user.
            logging.info("Detected %d supported files that are not parseable",
                         len(self.privative_fileset))
            logging.info("Potential dependencies cannot be extracted from them")
            for f in self.privative_fileset:
                logging.info("not parseable: %s", f)
        if len(self.parseable_fileset) > 0:
            logging.info("Detected %d supported files that can be parsed",
                         len(self.parseable_fileset))

    def solve_file_set(self):
        """Build file set with only those files required by the top entity"""
        libs = None
        system_libs = self.system_libs
        if self.tool is not None:
            # Get system libs and standard libs from the tool
            libs = self.tool.get_standard_libs()
            for l in self.tool.get_system_libs():
                system_libs.add(l)
        dep_solver.solve(self.parseable_fileset, system_libs, libs)
        if self.options.all_files:
            # If option -all is used, no need to compute dependencies.
            pass
        else:
            # Only keep top_entity, extra_modules and their dependencies
            extra_modules = self.top_manifest.manifest_dict.get("extra_modules")
            self.parseable_fileset = dep_solver.make_dependency_set(
                self.parseable_fileset, self.top_entity, extra_modules)

    def get_top_manifest(self):
        """Get the Top module from the pool"""
        return self.top_manifest

    def __str__(self):
        """Cast the module list as a list of strings"""
        return str([str(m) for m in self.all_manifests])
