#!/usr/bin/python
#
# Author: Nick Brereton
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

"""This module provides a Xilinx XCI IP description parser for HDLMake"""

from __future__ import absolute_import
import re
import logging

from xml.etree import ElementTree as ET

from .new_dep_solver import DepParser
from .dep_file import DepRelation
from ..sourcefiles.srcfile import create_source_file

class XCIParser(DepParser):
    """Class providing the Xilinx XCI parser"""

    def __init__(self, dep_file):
        DepParser.__init__(self, dep_file)

    def parse(self, dep_file):
        """Parse a Xilinx XCI IP description file to determine the provided module(s)"""
        assert not dep_file.is_parsed
        logging.debug("Parsing %s", dep_file.path)

        with open(dep_file.path) as f:
            # extract namespaces with a regex -- not really ideal, but without pulling in
            # an external xml lib I can't think of a better way.
            xmlnsre = re.compile(r'''\bxmlns:(\w+)\s*=\s*"(\w+://[^"]*)"''', re.MULTILINE)
            xml = f.read()
            nsmap = dict(xmlnsre.findall(xml))
            value = ET.fromstring(xml).find('spirit:componentInstances/spirit:componentInstance/spirit:instanceName', nsmap)
            if not value is None:
                module_name = value.text
                logging.debug("found module %s.%s", dep_file.library, module_name)
                dep_file.add_provide(
                    DepRelation(module_name, dep_file.library, DepRelation.MODULE))

        dep_file.is_parsed = True
