#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2019 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
#		  Adopted to LiberoSoC v12.x by Severin Haas (severin.haas@cern.ch)
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

"""Module providing support for Microsemi Libero SoC 12.x synthesis"""


from __future__ import absolute_import
from .makefilesyn import MakefileSyn
from ..sourcefiles.srcfile import VHDLFile, VerilogFile, SDCFile, PDCFile


class ToolLiberoSoC(MakefileSyn):

    """Class providing the interface for Microsemi Libero SoC 12.x synthesis"""

    TOOL_INFO = {
        'name': 'LiberoSoC',
        'id': 'liberosoc',
        'windows_bin': 'libero.exe SCRIPT:',
        'linux_bin': 'libero SCRIPT:',
        'project_ext': 'prjx'}

    STANDARD_LIBS = ['ieee', 'std']

    _LIBERO_SOURCE = 'create_links {0} $(sourcefile)'

    SUPPORTED_FILES = {
        SDCFile: _LIBERO_SOURCE.format('-sdc'),
        PDCFile: _LIBERO_SOURCE.format('-io_pdc')}

    HDL_FILES = {
        VHDLFile: _LIBERO_SOURCE.format('-hdl_source'),
        VerilogFile: _LIBERO_SOURCE.format('-hdl_source')}

    CLEAN_TARGETS = {'clean': ["$(PROJECT)"],
                     'mrproper': ["*.pdb", "*.stp"]}

    TCL_CONTROLS = {
        'create': 'new_project -location {{./{0}}} '
                  '-name {{{0}}} -hdl {{{1}}} '
                  '-family {{{2}}} -die {{{3}}} '
                  '-package {{{4}}} -speed {{{5}}} ',
        'open': 'open_project -file {$(PROJECT)/$(PROJECT_FILE)}',
        'save': 'save_project',
        'close': 'close_project',
        'project': '$(TCL_CREATE)\n'
                   'source files.tcl\n'
                   'refresh\n'
                   '{0}\n'
                   '$(TCL_SAVE)\n'
                   '$(TCL_CLOSE)',
        'bitstream': '$(TCL_OPEN)\n'
                     'run_tool -name {GENERATEPROGRAMMINGDATA}\n'
                     'file mkdir ./$(PROJECT)/bitstream\n'
                     'export_bitstream_file '
                     '-file_name {$(PROJECT)} '
                     '-export_dir {$(PROJECT)/bitstream} '
                     '-format {STP} -trusted_facility_file 1 '
                     '-trusted_facility_file_components {FABRIC} '
                     '-serialization_stapl_type {SINGLE} '
                     '-serialization_target_solution {FLASHPRO_3_4_5}\n'
                     '$(TCL_SAVE)\n'
                     '$(TCL_CLOSE)',
        'install_source': '$(PROJECT)/designer/impl1/$(SYN_TOP).pdb'}

    def __init__(self):
        super(ToolLiberoSoC, self).__init__()
        self._tcl_controls.update(ToolLiberoSoC.TCL_CONTROLS)

    def _makefile_syn_tcl(self):
        """Create a Libero synthesis project by TCL"""
        syn_project = self.manifest_dict["syn_project"]
        syn_device = self.manifest_dict["syn_device"]
        syn_family = self.manifest_dict["syn_family"]
        syn_grade = self.manifest_dict["syn_grade"]
        syn_package = self.manifest_dict["syn_package"]
        syn_lang = self.manifest_dict.get("language")
        # Default language is VHDL, so might not be defined by the user
        if syn_lang == None:
            syn_lang = "VHDL"

        create_tmp = self._tcl_controls["create"]

        self._tcl_controls["create"] = create_tmp.format(syn_project,
                                                         syn_lang.upper(),
                                                         syn_family,
                                                         syn_device.upper(),
                                                         syn_package.upper(),
                                                         syn_grade)
        project_tmp = self._tcl_controls["project"]
        synthesis_constraints = []
        compilation_constraints = []
        ret = []
        # First stage: linking files
        for file_aux in self.fileset.sort():
            if isinstance(file_aux, SDCFile):
                synthesis_constraints.append(file_aux)
                compilation_constraints.append(file_aux)
            elif isinstance(file_aux, PDCFile):
                compilation_constraints.append(file_aux)
        # Second stage: Organizing / activating synthesis constraints (the top
        # module needs to be present!)
        if synthesis_constraints:
            line = 'organize_tool_files -tool {SYNTHESIZE} '
            for file_aux in synthesis_constraints:
                line = line + '-file {' + file_aux.rel_path() + '} '
            line = line + \
                '-module {$(TOP_MODULE)::work} -input_type {constraint} '
            ret.append(line)
        # Third stage: Organizing / activating compilation constraints (the top
        # module needs to be present!)
        if compilation_constraints:
            line = 'organize_tool_files -tool {PLACEROUTE} '
            for file_aux in compilation_constraints:
                line = line + '-file {' + file_aux.rel_path() + '} '
            line = line + \
                '-module {$(TOP_MODULE)::work} -input_type {constraint} '
            ret.append(line)
        # Fourth stage: set root/top module
        line = 'set_root -module {$(TOP_MODULE)::work}'
        ret.append(line)
        self._tcl_controls['project'] = project_tmp.format('\n'.join(ret))
        super(ToolLiberoSoC, self)._makefile_syn_tcl()
