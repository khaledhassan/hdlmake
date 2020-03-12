"""Module providing the synthesis functionality for writing Makefiles"""

from __future__ import absolute_import
import os, sys
import logging

from .makefile import ToolMakefile
from ..util import shell

from ..sourcefiles.srcfile import VHDLFile, VerilogFile, SVFile


def _check_synthesis_manifest(top_manifest):
    """Check the manifest contains all the keys for a synthesis project"""
    for v in ["syn_top"]:
        if v not in top_manifest.manifest_dict:
            raise Exception(
                "'{}' variable must be set in the top manifest.".format(v))


class GhdlSyn(ToolMakefile):

    """Class that provides the synthesis Makefile writing methods and status"""

    TOOL_INFO = {
        'name': 'Ghdl',
        'id': 'ghdl',
        'windows_bin': 'ghdl',
        'linux_bin': 'ghdl',
        'project_ext': ''}

    CLEAN_TARGETS = {'clean': [],
                     'mrproper': []}
    SYSTEM_LIBS = ['vhdl']

    HDL_FILES = {VHDLFile: '$(sourcefile)'}

    def __init__(self):
        super(GhdlSyn, self).__init__()
        self._tcl_controls = {}

    def write_makefile(self, top_manifest, fileset, filename=None):
        """Generate a Makefile for the specific synthesis tool"""
        _check_synthesis_manifest(top_manifest)
        self.makefile_setup(top_manifest, fileset, filename=filename)
        self.makefile_check_tool('syn_path')
        self.makefile_includes()
        self._makefile_syn_top()
        self._makefile_syn_local()
        self._makefile_syn_files()
        self._makefile_syn_build()
        self._makefile_syn_clean()
        self._makefile_syn_phony()
        self.makefile_close()
        logging.info(self.TOOL_INFO['name'] + " synthesis makefile generated.")

    def _makefile_syn_top(self):
        """Create the top part of the synthesis Makefile"""
        self.writeln("TOP_MODULE := {}".format(self.manifest_dict["syn_top"]))
        self.writeln("TOOL_PATH := {}".format(self.manifest_dict["syn_path"]))
        self.writeln("GHDL := ghdl")
        self.writeln("GHDL_OPT := {}".format(self.manifest_dict.get("ghdl_opt", '')))

    def _makefile_syn_files(self):
        """Write the files TCL section of the Makefile"""
        ret = []
        fileset_dict = {}
        sources_list = []
        fileset_dict.update(self.HDL_FILES)
        fileset_dict.update(self.SUPPORTED_FILES)
        for filetype in fileset_dict:
            file_list = []
            for file_aux in self.fileset:
                if isinstance(file_aux, filetype):
                    if filetype == VerilogFile and isinstance(file_aux, SVFile):
                        # Discard SVerilog files for verilog type.
                        continue
                    file_list.append(shell.tclpath(file_aux.rel_path()))
            if not file_list == []:
                ret.append(
                   'SOURCES_{0} := \\\n'
                   '{1}\n'.format(filetype.__name__,
                               ' \\\n'.join(file_list)))
                if not fileset_dict[filetype] is None:
                    sources_list.append(filetype)
        self.writeln('\n'.join(ret))
        self.writeln('files.tcl:')
        if "files" in self._tcl_controls:
            echo_command = '\t\t@echo {0} >> $@'
            tcl_command = []
            for command in self._tcl_controls["files"].split('\n'):
                tcl_command.append(echo_command.format(command))
            command_string = "\n".join(tcl_command)
            if shell.check_windows_commands():
                command_string = command_string.replace("'", "")
            self.writeln(command_string)
        for filetype in sources_list:
            filetype_string = ('\t\t@$(foreach sourcefile,'
                ' $(SOURCES_{0}), echo "{1}" >> $@ &)'.format(
                filetype.__name__, fileset_dict[filetype]))
            if shell.check_windows_commands():
                filetype_string = filetype_string.replace(
                    '"', '')
            self.writeln(filetype_string)
        self.writeln()

    def _makefile_syn_local(self):
        """Generic method to write the synthesis Makefile local target"""
        self.writeln("#target for performing local synthesis\n"
                     "all: synthesis\n")

    def _makefile_syn_build(self):
        """Generate the synthesis Makefile targets for handling design build"""
        self.writeln("""\
synthesis: files.tcl
\t$(GHDL) --synth $(GHDL_OPT) @files.tcl -e $(TOP_MODULE)
""")

    def _makefile_syn_clean(self):
        """Print the Makefile clean target for synthesis"""
        self.makefile_clean()
        self.makefile_mrproper()

    def _makefile_syn_phony(self):
        """Print synthesis PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean all")
