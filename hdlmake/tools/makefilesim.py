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
        self.writeln("TOP_MODULE := {}".format(self.manifest_dict["sim_top"]))
        self.writeln()

    def _makefile_sim_options(self):
        """End stub method to write the simulation Makefile options section"""
        pass

    def _makefile_sim_compilation(self):
        """End stub method to write the simulation Makefile compilation
        section"""
        pass

    def get_stamp_file(self, dep_file):
        """Stamp file for source file :param file:"""
        name = dep_file.purename
        return os.path.join(dep_file.library, name, ".{}_{}".format(name, dep_file.extension()))

    def get_stamp_library(self, lib):
        return lib + shell.makefile_slash_char() + "." + lib

    def _makefile_touch_stamp_file(self):
        self.write("\t\t@" + shell.mkdir_command() + " $(dir $@)")
        self.writeln(" && " + shell.touch_command()  + " $@\n")

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

    def _makefile_sim_compile_file(self, srcfile):
        if isinstance(srcfile, VHDLFile):
            key = 'vhdl'
        elif isinstance(srcfile, VerilogFile):
            key = 'vlog'
        else:
            return None
        cmd = self.SIMULATOR_CONTROLS.get(key)
        if cmd is None:
            return None
        return cmd.format(work=srcfile.library)

    def _makefile_sim_dep_files(self):
        """Print dummy targets to handle file dependencies"""
        for file_aux in self.fileset.sort():
            cmd = self._makefile_sim_compile_file(file_aux)
            if cmd is not None:
                self._makefile_sim_file_rule(file_aux)
                self.writeln("\t\t" + cmd)
                self._makefile_touch_stamp_file()
                self.writeln()

    def get_all_libs(self):
        """Return a sorted list of all the libraries name"""
        return sorted(set(f.library for f in self.fileset))

    def _makefile_sim_libs_variables(self, libs):
        """Create variables for libraries name"""
        self.writeln('LIBS := ' + ' '.join(libs))
        self.writeln('LIB_IND := ' + ' '.join([self.get_stamp_library(lib) for lib in libs]))
        self.writeln()

    def _makefile_sim_command(self):
        """Generic method to write the simulation Makefile user commands"""
        self.writeln("# USER SIM COMMANDS")
        self.writeln("sim_pre_cmd:")
        self.writeln("\t\t" + self.manifest_dict.get("sim_pre_cmd", ''))
        self.writeln("sim_post_cmd:")
        self.writeln("\t\t" + self.manifest_dict.get("sim_post_cmd", ''))
        self.writeln()

    def _makefile_sim_clean(self):
        """Generic method to write the simulation Makefile user clean target"""
        self.makefile_clean()
        self.makefile_mrproper()

    def _makefile_sim_phony(self):
        """Print simulation PHONY target list to the Makefile"""
        self.writeln(
            ".PHONY: mrproper clean sim_pre_cmd sim_post_cmd simulation")
