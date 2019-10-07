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

"""Module providing support for Xilinx Vivado synthesis"""


from __future__ import absolute_import
from .xilinx import ToolXilinx
from ..sourcefiles.srcfile import (VHDLFile, VerilogFile, SVFile,
                                   XDCFile, XCIFile, NGCFile, XMPFile,
                                   XCOFile, COEFile, BDFile, TCLFile, BMMFile,
                                   MIFFile, RAMFile, VHOFile, VEOFile, XCFFile)


class ToolVivado(ToolXilinx):

    """Class providing the interface for Xilinx Vivado synthesis"""

    TOOL_INFO = {
        'name': 'vivado',
        'id': 'vivado',
        'windows_bin': 'vivado -mode tcl -source',
        'linux_bin': 'vivado -mode tcl -source',
        'project_ext': 'xpr'
    }

    STANDARD_LIBS = ['ieee', 'std']

    SUPPORTED_FILES = {
         XDCFile: ToolXilinx._XILINX_SOURCE,
         XCFFile: ToolXilinx._XILINX_SOURCE,
         NGCFile: ToolXilinx._XILINX_SOURCE,
         XMPFile: ToolXilinx._XILINX_SOURCE,
         XCOFile: ToolXilinx._XILINX_SOURCE,
         COEFile: ToolXilinx._XILINX_SOURCE,
         BDFile: ToolXilinx._XILINX_SOURCE,
         BMMFile: ToolXilinx._XILINX_SOURCE,
         TCLFile: ToolXilinx._XILINX_SOURCE,
         MIFFile: ToolXilinx._XILINX_SOURCE,
         RAMFile: ToolXilinx._XILINX_SOURCE,
         VHOFile: ToolXilinx._XILINX_SOURCE,
         VEOFile: ToolXilinx._XILINX_SOURCE}
    SUPPORTED_FILES.update(ToolXilinx.SUPPORTED_FILES)

    HDL_FILES = {
        VHDLFile:    ToolXilinx._XILINX_SOURCE,
        VerilogFile: ToolXilinx._XILINX_SOURCE,
        SVFile:      ToolXilinx._XILINX_SOURCE,
        XCIFile:     ToolXilinx._XILINX_SOURCE}

    CLEAN_TARGETS = {'clean': [".Xil", "*.jou", "*.log", "*.pb", "*.dmp",
                               "$(PROJECT).cache", "$(PROJECT).data", "work",
                               "$(PROJECT).runs", "$(PROJECT).hw",
                               "$(PROJECT).ip_user_files", "$(PROJECT_FILE)"]}
    CLEAN_TARGETS.update(ToolXilinx.CLEAN_TARGETS)

    TCL_CONTROLS = {'bitstream': '$(TCL_OPEN)\n'
                                 'launch_runs impl_1 -to_step write_bitstream'
                                 '\n'
                                 'wait_on_run impl_1\n'
                                 '$(TCL_CLOSE)'}

    def __init__(self):
        super(ToolVivado, self).__init__()
        self._tcl_controls.update(ToolVivado.TCL_CONTROLS)
