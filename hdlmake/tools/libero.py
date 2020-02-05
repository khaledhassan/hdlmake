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

"""Module providing support for Microsemi Libero IDE synthesis"""


from __future__ import absolute_import
from .makefilesyn import MakefileSyn
from ..sourcefiles.srcfile import VHDLFile, VerilogFile, SDCFile, PDCFile


class ToolLibero(MakefileSyn):

    """Class providing the interface for Microsemi Libero IDE synthesis"""

    TOOL_INFO = {
        'name': 'Libero',
        'id': 'libero',
        'windows_bin': 'libero.exe SCRIPT:',
        'linux_bin': 'libero SCRIPT:',
        'project_ext': 'prjx'}

    STANDARD_LIBS = ['ieee', 'std']

    _LIBERO_SOURCE = 'create_links {0} $(sourcefile)'

    SUPPORTED_FILES = {
        SDCFile: _LIBERO_SOURCE.format('-sdc'),
        PDCFile: _LIBERO_SOURCE.format('-pdc')}

    HDL_FILES = {
        VHDLFile: _LIBERO_SOURCE.format('-hdl_source'),
        VerilogFile: _LIBERO_SOURCE.format('-hdl_source')}

    CLEAN_TARGETS = {'clean': ["$(PROJECT)"],
                     'mrproper': ["*.pdb", "*.stp"]}

    TCL_CONTROLS = {
        'create': 'new_project -location {{./{project}}} -name {{{project}}}'
                  ' -hdl {{VHDL}} -family {{{family}}} -die {{{device}}}'
                  ' -package {{{package}}} -speed {{{grade}}} -die_voltage {{1.5}}',
        'open': 'open_project -file {$(PROJECT)/$(PROJECT_FILE)}',
        'save': 'save_project',
        'close': 'close_project',
        'project': '$(TCL_CREATE)\n'
                   'source files.tcl\n'
                   '{0}\n'
                   '$(TCL_SAVE)\n'
                   '$(TCL_CLOSE)',
        'bitstream': '$(TCL_OPEN)\n'
                     'update_and_run_tool'
                     ' -name {GENERATEPROGRAMMINGDATA}\n'
                     '$(TCL_SAVE)\n'
                     '$(TCL_CLOSE)',
        'install_source': '$(PROJECT)/designer/impl1/$(SYN_TOP).pdb'}

    # Override the build command, because no space is expected between TCL_INTERPRETER and the tcl file
    MAKEFILE_SYN_BUILD_CMD="""\
{0}.tcl:
{3}

{0}: {1} {0}.tcl
\t$(SYN_PRE_{2}_CMD)
\t$(TCL_INTERPRETER)$@.tcl
\t$(SYN_POST_{2}_CMD)
\t{4} $@
"""

    def __init__(self):
        super(ToolLibero, self).__init__()
        self._tcl_controls.update(ToolLibero.TCL_CONTROLS)

    def _makefile_syn_tcl(self):
        """Create a Libero synthesis project by TCL"""
        syn_project = self.manifest_dict["syn_project"]
        syn_family = self.manifest_dict["syn_family"]
        syn_device = self.manifest_dict["syn_device"]
        syn_grade = self.manifest_dict["syn_grade"]
        syn_package = self.manifest_dict["syn_package"]
        # Template substitute for 'create'.
        create_tmp = self._tcl_controls["create"]
        self._tcl_controls["create"] = create_tmp.format(project=syn_project,
                                                         family=syn_family,
                                                         device=syn_device,
                                                         package=syn_package,
                                                         grade=syn_grade)
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
                '-module {$(TOP_MODULE)::work} -input_type {constraint}'
            ret.append(line)
        # Third stage: Organizing / activating compilation constraints (the top
        # module needs to be present!)
        if compilation_constraints:
            line = 'organize_tool_files -tool {COMPILE} '
            for file_aux in compilation_constraints:
                line = line + '-file {' + file_aux.rel_path() + '} '
            line = line + \
                '-module {$(TOP_MODULE)::work} -input_type {constraint}'
            ret.append(line)
        # Fourth stage: set root/top module
        line = 'set_root -module {$(TOP_MODULE)::work}'
        ret.append(line)
        self._tcl_controls['project'] = project_tmp.format('\n'.join(ret))
        super(ToolLibero, self)._makefile_syn_tcl()
