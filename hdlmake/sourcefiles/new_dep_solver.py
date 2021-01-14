#!/usr/bin/python
#
# Copyright (c) 2013, 2014 CERN
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

"""This package provides the functions and classes to parse and solve
 HDLMake filesets"""

from __future__ import print_function
from __future__ import absolute_import
import logging

from ..sourcefiles.dep_file import DepFile
from .systemlibs import all_system_libs


class DepParser(object):

    """Base Class for the different HDL parsers (VHDL and Verilog)"""

    def parse(self, dep_file, alldeps):
        """Base dummy interface method for the HDL parse execution"""
        pass

    
class AllRelations(object):
    def __init__(self):
        # Dict of Rel to itself.
        # FIXME: is there a better way to do this ?
        self.rels = {}

    def add_require(self, file, rel):
        """Called by a parsed when :param file: requires :param rel:"""
        if rel in file.requires:
            # Already present
            assert rel in self.rels
            return
        # Get the existing relation or insert the new one
        rel = self.rels.setdefault(rel, rel)
        # Update the graph
        file.requires.add(rel)
        rel.required_by.add(file)

    def add_provide(self, file, rel):
        """Called by a parsed when :param file: provides :param rel:"""
        if rel in file.provides:
            # Alreay present
            assert rel in self.rels
        # Get the existing relation or insert the new one
        rel = self.rels.setdefault(rel, rel)
        # Update the graph
        file.provides.add(rel)
        rel.provided_by.add(file)

    def find_provider(self, rel):
        return self.rels.get(rel)


def parse_source_files(graph, fileset):
    """Parse source files to extract the graph dependencies"""
    from .sourcefileset import SourceFileSet
    assert isinstance(fileset, SourceFileSet)

    # Parse source files
    logging.debug("PARSE SOURCE BEGIN: Here, we parse all the files in the "
                  "fileset: no manifest parsing should be done beyond this point")
    for investigated_file in fileset:
        assert isinstance(investigated_file, DepFile)
        logging.debug("PARSING SOURCE FILE: %s", investigated_file)
        investigated_file.parser.parse(investigated_file, graph)
        if logging.root.level >= logging.DEBUG:
            for r in investigated_file.provides:
                logging.debug("PROVIDE %s", r)
            for r in investigated_file.requires:
                logging.debug("REQUIRE %s", r)
    logging.debug("PARSE SOURCE END: now the parsing is done")

    # Compute file dependencies
    for investigated_file in fileset:
        for rel in investigated_file.requires:
            for dep_file in rel.provided_by:
                if dep_file is not investigated_file:
                    # A file cannot depends on itself.
                    investigated_file.depends_on.add(dep_file)


def check_graph(graph, fileset, syslibs, standard_libs=None):
    """Check that each dependency of :param fileset: can be solved once or by
       a module from :param syslibs: or :param standard_libs:"""
    from .dep_file import DepRelation
    # Dependencies provided by system libraries.
    system_rels = []
    for e in syslibs:
        f = all_system_libs.get(e)
        if f is None:
            raise Exception("system library '{}' is unknown".format(e))
        rels = f()
        system_rels.extend(rels)

    logging.debug("SOLVE BEGIN")
    not_satisfied = 0
    done = set()
    for investigated_file in fileset:
        # logging.info("INVESTIGATED FILE: %s" % investigated_file)
        for rel in investigated_file.requires:
            if rel in done:
                # Already handled.  Avoid to warn several times
                continue
            done.add(rel)
            lst = list(rel.provided_by)
            if len(lst) > 1:
                logging.warning(
                    "Relation %s satisfied by multiple (%d) files:\n %s",
                    str(rel),
                    len(lst),
                    '\n '.join([file_aux.path for file_aux in lst]))
                continue
            if len(lst) == 1:
                # Perfect!
                continue

            # So we are handling an unsatisfied dependency.
            assert(len(lst) == 0)

            # Maybe provided by system libraries
            found = False
            for r in system_rels:
                if r.satisfies(rel):
                    found = True
                    break
            if found:
                continue

            # if relation is a USE PACKAGE, check against
            # the standard libs provided by the tool HDL compiler
            required_lib = rel.lib_name
            if (standard_libs is not None
                 and rel.rel_type is DepRelation.PACKAGE
                 and required_lib in standard_libs):
                logging.debug("Not satisfied relation %s in %s will "
                              "be covered by the target compiler "
                              "standard libs.",
                              str(rel), investigated_file.name)
                continue
            logging.warning("File '%s' depends on %s, but the latter was not found in any source file",
                            investigated_file.name, str(rel))
            not_satisfied += 1
    logging.debug("SOLVE END")
    if not_satisfied != 0:
        logging.warning(
            "Dependencies solved, but %d relations were not satisfied",
            not_satisfied)
    else:
        logging.info(
            "Dependencies solved, all of the relations were satisfied!")


def make_dependency_sorted_list(fileset):
    """Sort files in order of dependency.
    Files with no dependencies first.
    All files that another depends on will be earlier in the list."""
    fset = list(fileset)
    fset.sort(key=lambda f: f.path.lower())
    # Not necessary, but will tend to group files more nicely
    # in the output.
    fset.sort(key=DepFile.get_dep_level)
    return fset


def make_dependency_set(graph, fileset, top_level_entity, extra_modules=None):
    """Create the set of all files required to build the named
     top_level_entity."""
    from ..sourcefiles.sourcefileset import SourceFileSet
    from ..sourcefiles.dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)

    # Find top file
    rel = DepRelation(top_level_entity, "work", DepRelation.MODULE)
    rel = graph.find_provider(rel)
    if rel is None:
        logging.critical(
            'Could not find a top level file that provides the '
            '"%s" top module. Continuing with the full file set.',
            top_level_entity)
        return fileset
    top_file = list(rel.provided_by)
    # TODO: warn if multiple providers ?

    # Add extra modules
    extra_files = []
    if extra_modules is not None:
        for name in extra_modules:
            rel = DepRelation(name, "work", DepRelation.MODULE)
            rel = graph.find_provider(rel)
            if rel is None:
                logging.critical(
                    'Could not find a extra module %s (ignored)', name)
            else:
                extra_files.extend(list(rel.provided_by))

    # Collect only the files that the top level entity is dependant on, by
    # walking the dependancy tree.
    dep_file_set = SourceFileSet()
    file_set = set(top_file + extra_files)
    while len(file_set) > 0:
        chk_file = file_set.pop()
        if chk_file not in dep_file_set:
            dep_file_set.add(chk_file)
            for f in chk_file.depends_on:
                file_set.add(f)

    hierarchy_drivers = [top_level_entity]
    if extra_modules is not None:
        hierarchy_drivers += extra_modules
    logging.info("Found %d files as dependancies of %s.",
                 len(dep_file_set), ", ".join(hierarchy_drivers))
    return dep_file_set
