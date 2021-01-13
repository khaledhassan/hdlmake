#!/usr/bin/python
#
# Author: Christos Gentsos
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
# along with Hdlmake.  If not, see .
#

"""This module provides a Microsemi CXF IP description parser for HDLMake"""

from __future__ import absolute_import
import re
import os
import logging

from xml.etree import ElementTree as ET

from .new_dep_solver import DepParser
from .dep_file import DepRelation
from ..sourcefiles.srcfile import create_source_file
from ..sourcefiles.srcfile import VHDL_EXTENSIONS, VERILOG_EXTENSIONS, SV_EXTENSIONS

class CXFParser(DepParser):
    """Class providing the Microsemi CXF parser"""

    def parse(self, dep_file, graph):
        """Parse a Microsemi CXF IP description file to determine the provided module(s)"""
        with open(dep_file.path) as f:
            xml = f.read()
            # extract namespaces with a regex
            xmlnsre = re.compile(r'\bxmlns\s*=\s*"(\w+://[^"]*)"', re.MULTILINE)
            nsobj = xmlnsre.search(xml)
            try:
                ns = '{'+nsobj.group(1)+'}'
            except e:
                ns = ''

            # find the IP core name
            xmlET = ET.fromstring(xml)
            nameobj = xmlET.find(ns+'name')
            try:
                module_name = nameobj.text
            except e:
                module_name = None

            # gather the list of source files
            for i in xmlET.iter(ns+'file'):
                for ii in i.iter(ns+'name'):
                    _, extension = os.path.splitext(ii.text)
                    if extension[1:] in VHDL_EXTENSIONS + VERILOG_EXTENSIONS + SV_EXTENSIONS + ('sdc', 'cxf'):
                        dep_file.included_files.add(ii.text)

            if not module_name is None:
                logging.debug("found module %s.%s", dep_file.library, module_name)
                # dep_file.add_provide(
                #     DepRelation(module_name, dep_file.library, DepRelation.MODULE))

        logging.debug("%s has %d includes.", str(dep_file), len(dep_file.included_files))
