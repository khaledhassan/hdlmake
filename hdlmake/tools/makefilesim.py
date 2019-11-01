"""Module providing the simulation functionality for writing Makefiles"""

from __future__ import absolute_import
import os
import sys
import logging

from .makefile import ToolMakefile
from ..util import shell
from ..sourcefiles.srcfile import VerilogFile, VHDLFile, SVFile
from ..util import path as path_mod

def _check_simulation_manifest(top_manifest):
    """Check if the simulation keys are provided by the top manifest"""
    if top_manifest.manifest_dict.get("sim_top") is None:
        raise Exception("sim_top variable must be set in the top manifest.")


class MakefileSim(ToolMakefile):

    """Class that provides the Makefile writing methods and status"""

    SIMULATOR_CONTROLS = {}

    def __init__(self):
        super(MakefileSim, self).__init__()
        
    def write_makefile(self, top_manifest, fileset, filename=None):
        """Execute the simulation action"""
        _check_simulation_manifest(top_manifest)
        self.makefile_setup(top_manifest, fileset, filename=filename)
        self.makefile_check_tool('sim_path')
        self.makefile_includes()
        self._makefile_sim_top()
        self._makefile_sim_options()
        self._makefile_sim_local()
        self._makefile_sim_sources()
        self._makefile_sim_compilation()
        self._makefile_sim_command()
        self._makefile_sim_clean()
        self._makefile_sim_phony()
        self.makefile_close()

    def _makefile_sim_top(self):
        """Generic method to write the simulation Makefile top section"""
        top_parameter = """\
TOP_MODULE := {top_module}
"""
        self.writeln(top_parameter.format(
            top_module=self.manifest_dict["sim_top"]))

    def _makefile_sim_options(self):
        """End stub method to write the simulation Makefile options section"""
        pass

    def _makefile_sim_compilation(self):
        """End stub method to write the simulation Makefile compilation
        section"""
        pass

    def _makefile_sim_local(self):
        """Generic method to write the simulation Makefile local target"""
        self.writeln("#target for performing local simulation\n"
                     "local: sim_pre_cmd simulation sim_post_cmd\n")

    def _makefile_sim_sources_lang(self, name, klass):
        """Generic method to write the simulation Makefile HDL sources"""
        fileset = self.fileset
        self.write("{}_SRC := ".format(name))
        for vlog in fileset.filter(klass).sort():
            self.writeln(vlog.rel_path() + " \\")
        self.writeln()
        self.write("{}_OBJ := ".format(name))
        for vlog in fileset.filter(klass).sort():
            # make a file compilation indicator (these .dat files are made even
            # if the compilation process fails) and add an ending according
            # to file's extension (.sv and .vhd files may have the same
            # corename and this causes a mess
            self.writeln(self.get_stamp_file(vlog) + " \\")
        self.writeln()

    def _makefile_sim_sources(self):
        """Generic method to write the simulation Makefile HDL sources"""
        self._makefile_sim_sources_lang("VERILOG", VerilogFile)
        self._makefile_sim_sources_lang("VHDL", VHDLFile)

    def _makefile_sim_file_rule(self, file_aux):
        """Generate target and prerequisites for :param file_aux:"""
        cwd = os.getcwd()
        self.write("{}: {}".format(self.get_stamp_file(file_aux), file_aux.rel_path()))
        # list dependencies, do not include the target file
        for dep_file in sorted(file_aux.depends_on, key=(lambda x: x.path)):
            if dep_file is file_aux:
                # Do not depend on itself.
                continue
            self.write(" \\\n" + self.get_stamp_file(dep_file))
        # Add included files
        for dep_file in sorted(file_aux.included_files):
            self.write(" \\\n{}".format(path_mod.relpath(dep_file, cwd)))
        self.writeln()

    def _makefile_sim_dep_files(self):
        """Print dummy targets to handle file dependencies"""
        for file_aux in self.fileset.sort():
            # Consider only HDL files.
            if isinstance(file_aux, tuple(self.HDL_FILES)):
                self._makefile_sim_file_rule(file_aux)
                if isinstance(file_aux, VHDLFile):
                    command_key = 'vhdl'
                elif isinstance(file_aux, VerilogFile):
                    command_key = 'vlog'
                self.writeln("\t\t" + self.SIMULATOR_CONTROLS[command_key].format(work=file_aux.library))
                self._makefile_touch_stamp_file()
                self.writeln()

    def _makefile_sim_command(self):
        """Generic method to write the simulation Makefile user commands"""
        sim_pre_cmd = self.manifest_dict.get("sim_pre_cmd", '')
        sim_post_cmd = self.manifest_dict.get("sim_post_cmd", '')
        sim_command = """# USER SIM COMMANDS
sim_pre_cmd:
\t\t{sim_pre_cmd}
sim_post_cmd:
\t\t{sim_post_cmd}
"""
        self.writeln(sim_command.format(sim_pre_cmd=sim_pre_cmd,
                                        sim_post_cmd=sim_post_cmd))

    def _makefile_sim_clean(self):
        """Generic method to write the simulation Makefile user clean target"""
        self.makefile_clean()
        self.makefile_mrproper()

    def _makefile_sim_phony(self):
        """Print simulation PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean sim_pre_cmd sim_post_cmd simulation")
