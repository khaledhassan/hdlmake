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

from ..tools.makefile_writer import load_syn_tool, load_sim_tool
from ..util import shell
from ..sourcefiles import new_dep_solver as dep_solver
from ..sourcefiles.srcfile import VHDLFile, VerilogFile, SVFile
from ..sourcefiles.sourcefileset import SourceFileSet
from ..module.module import Module, ModuleArgs

class Action(object):

    """This is the base class providing the common Action methods"""

    def __init__(self, options):
        super(Action, self).__init__()
        self.top_manifest = None
        self.manifests = []
        self.parseable_fileset = SourceFileSet()
        self.privative_fileset = SourceFileSet()
        self._deps_solved = False
        self.options = options

    def __contains(self, module):
        """Check if the pool contains the given module by checking the URL"""
        for mod in self.manifests:
            if mod.url == module.url:
                return True
        return False

    def _add(self, new_module):
        """Add the given new module if this is not already in the pool"""
        assert isinstance(new_module, Module), "Expect a Module instance"
        if self.__contains(new_module):
            return
        if new_module.isfetched:
            for mod in new_module.submodules():
                self._add(mod)
        self.manifests.append(new_module)

    def new_module(self, parent, url, source, fetchto):
        """Add new module to the pool.

        This is the only way to add new modules to the pool
        Thanks to it the pool can easily control its content
        """
        self._deps_solved = False
        args = ModuleArgs()
        args.set_args(parent, url, source, fetchto)
        new_module = Module(args, self)
        self._add(new_module)
        return new_module

    def load_all_manifests(self):
        # Top level module.
        assert self.top_manifest is None
        self.top_manifest = self.new_module(parent=None,
                                            url=os.getcwd(),
                                            source=None,
                                            fetchto=".")
        # Parse the top manifest and all sub-modules.
        self.top_manifest.parse_manifest()
        self.config = self._get_config_dict()

    def setup(self):
        """Set tool and top_entity"""
        action = self.config.get("action")
        if action == None:
            self.tool = None
            self.top_entity = self.config.get("top_module", None)
        elif action == "simulation":
            tool = self.config.get("sim_tool")
            if tool is None:
                raise Exception("'sim_tool' variable is not defined")
            self.tool = load_sim_tool(tool)
            self.top_entity = self.config.get("sim_top") \
                or self.config.get("top_module")
            self.config["sim_top"] = self.top_entity
        elif action == "synthesis":
            tool = self.config.get("syn_tool")
            if tool is None:
                raise Exception("'syn_tool' variable is not defined")
            self.tool = load_syn_tool(tool)
            self.top_entity = self.config.get("syn_top") \
                or self.config.get("top_module")
            self.config["syn_top"] = self.top_entity
        else:
            raise Exception("Unknown requested action: {}".format(action))

    def build_complete_file_set(self):
        """Build file set with all the files listed in the complete pool"""
        logging.debug("Begin build complete file set")
        all_manifested_files = SourceFileSet()
        for manifest in self.manifests:
            all_manifested_files.add(manifest.files)
        logging.debug("End build complete file set")
        return all_manifested_files

    def build_file_set(self):
        """Initialize the parseable and privative fileset contents"""
        total_files = self.build_complete_file_set()
        for file_aux in total_files:
            if self.tool == None:
                if any(isinstance(file_aux, file_type)
                       for file_type in [VHDLFile, VerilogFile, SVFile]):
                    self.parseable_fileset.add(file_aux)
                else:
                    self.privative_fileset.add(file_aux)
            else:
                if any(isinstance(file_aux, file_type)
                       for file_type in self.tool.get_parseable_files()):
                    self.parseable_fileset.add(file_aux)
                elif any(isinstance(file_aux, file_type)
                       for file_type in self.tool.get_privative_files()):
                    self.privative_fileset.add(file_aux)
                else:
                    logging.debug("File not supported by the tool: %s",
                                  file_aux.path)
        if len(self.privative_fileset) > 0:
            logging.info("Detected %d supported files that are not parseable",
                         len(self.privative_fileset))
            for f in self.privative_fileset:
                logging.info("not parseable: %s", f)
        if len(self.parseable_fileset) > 0:
            logging.info("Detected %d supported files that can be parsed",
                         len(self.parseable_fileset))

    def solve_file_set(self):
        """Build file set with only those files required by the top entity"""
        if not self._deps_solved:
            if self.tool == None:
                dep_solver.solve(self.parseable_fileset)
            else:
                dep_solver.solve(self.parseable_fileset,
                                 self.tool.get_standard_libs())
            self._deps_solved = True
        if self.options.all_files:
            return
        solved_files = SourceFileSet()
        solved_files.add(dep_solver.make_dependency_set(
            self.parseable_fileset, self.top_entity,
            self.config.get("extra_modules")))
        self.parseable_fileset = solved_files

    def get_top_manifest(self):
        """Get the Top module from the pool"""
        return self.top_manifest

    def _get_config_dict(self):
        """Get the combined hierarchical Manifest dictionary from the pool"""
        config_dict = {}
        for mod in self.manifests:
            manifest_dict_tmp = mod.manifest_dict
            if manifest_dict_tmp is not None:
                if 'fetchto' in manifest_dict_tmp:
                    manifest_dict_tmp['fetchto'] = os.path.relpath(os.path.join(
                        mod.path,
                        mod.manifest_dict['fetchto']))
                manifest_dict_tmp.update(config_dict)
                config_dict = manifest_dict_tmp
        return config_dict

    def __str__(self):
        """Cast the module list as a list of strings"""
        return str([str(m) for m in self.manifests])
