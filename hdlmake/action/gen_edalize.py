#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# Generate a file (from hdlmake manifests) that runs edalize
# The idea is to not depend directly on edalize and to also avoid
# to reparse all the manifest files at each step.

import os.path
from ..sourcefiles.srcfile import VHDLFile, SVFile, VerilogFile

class Edalize():
    def __init__(self, action):
        self.action = action
        self.out = None


    def w(self, s=''):
        print(s, file=self.out)

    def gen_source_file(self, src):
        self.w(" {{ 'name': '{}',".format(src))
        if isinstance(src, VHDLFile):
            lang = 'vhdlSource'
        elif isinstance(src, SVFile):
            lang = 'systemVerilogSource'
        elif isinstance(src, VerilogFile):
            lang = 'verilogSource'
        else:
            lang = 'unknown'
        self.w("   'file_type': '{}'}},".format(lang))

    def gen_tool(self):
        name = self.action.tool.TOOL_INFO['id']
        self.w("tool = '{}'".format(name))

    def gen_top(self):
        project_name = self.action.top_manifest.manifest_dict.get("syn_project", None)
        if project_name is None:
            project_name = self.action.top_entity
        else:
            project_name = os.path.splitext(project_name)[0]

        self.w("edam = {")
        self.w("  'files'        : files,")
        self.w("  'name'         : '{}',".format(project_name))
        self.w("  'toplevel'     : '{}'".format(self.action.top_entity))
        self.w("}")

    def generate_file(self, f):
        self.out = f
        self.w("import sys")
        self.w("import os")
        self.w("from edalize import *")
        self.w()
        self.w("files = [")
        for src in self.action.parseable_fileset:
            self.gen_source_file(src)
        for src in self.action.privative_fileset:
            self.gen_source_file(src)
        self.w("]")
        self.w()
        self.gen_tool()
        self.w()
        self.gen_top()
        self.w()
        self.w("work_root = 'build'")
        self.w("backend = get_edatool(tool)(edam=edam, work_root=work_root)")
        self.w()
        self.w("# Very simplistic code")
        self.w("if len(sys.argv) == 2 and sys.argv[1] == 'configure':")
        self.w("  os.makedirs(work_root)")
        self.w("  backend.configure([])")
        self.w("elif len(sys.argv) == 2 and sys.argv[1] == 'build':")
        self.w("  backend.build()")
        self.w("elif len(sys.argv) == 2 and sys.argv[1] == 'run':")
        self.w("  backend.run([])")
        self.w("else:")
        self.w("  print('usage: {} build|run'.format(sys.argv[0]))")
