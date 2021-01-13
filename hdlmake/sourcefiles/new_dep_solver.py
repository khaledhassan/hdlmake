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

    def parse(self, dep_file):
        """Base dummy interface method for the HDL parse execution"""
        pass


def solve(fileset, syslibs, standard_libs=None):
    """Function that Parses and Solves the provided HDL fileset. Note
       that it doesn't return a new fileset, but modifies the original one"""
    from .sourcefileset import SourceFileSet
    from .dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)

    # Consider only source files with dependencies
    fset = fileset.filter(DepFile)

    # Parse source files
    # TODO: explain why some files are not parsed.
    logging.debug("PARSE BEGIN: Here, we will parse all the files in the "
                  "fileset: no parsing should be done beyond this point")
    for investigated_file in fset:
        logging.debug("PARSING FILE: %s", investigated_file)
        investigated_file.parser.parse(investigated_file)
    logging.debug("PARSE END: now the parsing is done")

    # Dependencies provided by system libraries.
    system_rels = []
    for e in syslibs:
        f = all_system_libs.get(e)
        if f is None:
            raise Exception("system library '{}' is unknown".format(e))
        system_rels.extend(f())

    logging.debug("SOLVE BEGIN")
    not_satisfied = 0
    for investigated_file in fset:
        # logging.info("INVESTIGATED FILE: %s" % investigated_file)
        for rel in investigated_file.requires:
            # logging.info("- relation: %s" % rel)
            # Only analyze USE relations, we are looking for dependencies
            satisfied_by = set()
            for dep_file in fset:
                if dep_file.satisfies(rel):
                    if dep_file is not investigated_file:
                        # A file cannot depends on itself.
                        investigated_file.depends_on.add(dep_file)
                    satisfied_by.add(dep_file)
            if len(satisfied_by) == 1:
                # Perfect!
                continue
            if len(satisfied_by) > 1:
                logging.warning(
                    "Relation %s satisfied by multiple (%d) files:\n %s",
                    str(rel),
                    len(satisfied_by),
                    '\n '.join([file_aux.path for
                               file_aux in list(satisfied_by)]))
                continue
            # So we are handling an unsatisfied dependency.
            assert(len(satisfied_by) == 0)

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
    dependable = [f for f in fileset if isinstance(f, DepFile)]
    non_dependable = [f for f in fileset if not isinstance(f, DepFile)]
    dependable.sort(key=lambda f: f.path.lower())
    # Not necessary, but will tend to group files more nicely
    # in the output.
    dependable.sort(key=DepFile.get_dep_level)
    return non_dependable + dependable


def make_dependency_set(fileset, top_level_entity, extra_modules=None):
    """Create the set of all files required to build the named
     top_level_entity."""
    from ..sourcefiles.sourcefileset import SourceFileSet
    from ..sourcefiles.dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)
    fset = fileset.filter(DepFile)

    def _check_entity(test_file, entity_name):
        """ Check if :param test_file: provides the entity pointed by :param entity_name:"""
        if entity_name == None:
            return False
        entity_rel = DepRelation(entity_name, "work", DepRelation.MODULE)
        for rel in test_file.provides:
            if rel == entity_rel:
                return True
        return False

    top_file = None
    extra_files = []
    for chk_file in fset:
        if _check_entity(chk_file, top_level_entity):
            top_file = chk_file
        if extra_modules is not None:
            for entity_aux in extra_modules:
                if _check_entity(chk_file, entity_aux):
                    extra_files.append(chk_file)
    if top_file is None:
        if top_level_entity is None:
            logging.critical(
                    'Could not find a top level file because the top '
                    'module is undefined. Continuing with the full file set.')
        else:
            logging.critical(
                    'Could not find a top level file that provides the '
                    '"%s" top module. Continuing with the full file set.',
                     top_level_entity)
        return fileset
    # Collect only the files that the top level entity is dependant on, by
    # walking the dependancy tree.
    dep_file_set = set()
    file_set = set([top_file] + extra_files)
    while len(file_set) > 0:
        chk_file = file_set.pop()
        dep_file_set.add(chk_file)
        file_set.update(chk_file.depends_on - dep_file_set)
    hierarchy_drivers = [top_level_entity]
    if extra_modules is not None:
        hierarchy_drivers += extra_modules
    logging.info("Found %d files as dependancies of %s.",
                 len(dep_file_set), ", ".join(hierarchy_drivers))
    return dep_file_set
