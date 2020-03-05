#!/usr/bin/python
#
# Copyright (c) 2020 CERN
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

from .dep_file import DepRelation

def add_entity(res, name):
    res.append(DepRelation(name, None, DepRelation.ENTITY))


def add_package(res, lib, name):
    res.append(DepRelation(name, lib, DepRelation.PACKAGE))


def build_xilinx():
    """Modules and packages provided by Xilinx system libraries"""
    res = []
    add_package(res, 'unisim', 'vcomponents')
    for n in ['ibuf', 'ibufds', 'ibufgds', 'ibufds_diff_out',
              'ibufds_gte2',
              'obufds', 'obuft', 'obuftds', 'oddr',
              'oserdes2', 'oserdese2', 'iserdese2', 'iodelay2', 'odelaye2', 'idelaye2', 'idelayctrl',
              'iobuf', 'iobufds',
              'pullup', 'pulldown',
              'bufio', 'bufio2',
              'bufgmux_ctrl', 'bufg', 'bufgce', 'bufr', 'bufpll', 'bufmr',
              'startupe2',
              'mmcme2_adv', 'mmcme2_base', 'pll_base', 'pll_adv', 'dcm_base', 'dcm_adv', 'dcm_sp',
              'bufpll_mcb', 'mcb', 'iodrp2', 'iodrp2_mcb',
              'icap_spartan6', 'bscan_spartan6',
              'gtxe2_channel', 'gtxe2_common', 'gtpa1_dual',
              'dsp48a1',
              'srlc32e']:
        add_entity(res, n)
    return res


all_system_libs = {'xilinx': build_xilinx}