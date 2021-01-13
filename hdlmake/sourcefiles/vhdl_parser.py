#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2015 CERN
# Author:
#     Tomasz Wlostowski (tomasz.wlostowski@cern.ch)
#     Adrian Fiergolski (Adrian.Fiergolski@cern.ch)
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

"""Module providing the VHDL parser capabilities"""

from __future__ import absolute_import
import logging
import re

from .new_dep_solver import DepParser


class VHDLParser(DepParser):

    """Class providing the container for VHDL parser instances"""

    def parse(self, dep_file, graph):
        """Parse the provided VHDL file and add the detected relations to it"""
        from .dep_file import DepRelation

        def _preprocess(vhdl_file):
            """Preprocess the supplied VHDL file instance"""
            buf = open(vhdl_file.path, "r").read()
            logging.debug(
                "preprocess file %s (of length %d) in library %s",
                vhdl_file.path, len(buf), vhdl_file.library)
            # Remove the comments and strings from the VHDL code
            pattern = re.compile('--.*?$|".?"', re.DOTALL | re.MULTILINE)
            return re.sub(pattern, "", buf)

        buf = _preprocess(dep_file)
        # use packages
        use_pattern = re.compile(
            r"^\s*use\s+(\w+)\s*\.\s*(\w+)",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_use(text):
            """Function to be applied by re.sub to every match of the
            use_pattern in the VHDL code -- group() returns positive matches
            as indexed plain strings. It adds the found USE relations to the
            file"""
            lib_name = text.group(1).lower()
            pkg_name = text.group(2).lower()
            if pkg_name == "all":
                # Forget 'use work.all'
                return "";
            if lib_name == "work":
                # Work is an alias for the current library
                lib_name = dep_file.library
            logging.debug("use package %s.%s", lib_name, pkg_name)
            graph.add_require(
                dep_file, DepRelation(pkg_name, lib_name, DepRelation.PACKAGE))
            return "<hdlmake use_pattern %s.%s>" % (lib_name, pkg_name)
        buf = re.sub(use_pattern, do_use, buf)

        use_context_pattern = re.compile(
            r"^\s*context\s+(\w+)\s*\.\s*(\w+)\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_use_context(text):
            """Function to be applied by re.sub to every match of the
            context_pattern in the VHDL code -- group() returns positive matches
            as indexed plain strings. It adds the found CONTEXT relations to the
            file"""
            lib_name = text.group(1).lower()
            pkg_name = text.group(2).lower()
            if lib_name == "work":
                # Work is an alias for the current library
                lib_name = dep_file.library
            logging.debug("use package %s.%s", lib_name, pkg_name)
            graph.add_require(
                dep_file, DepRelation(pkg_name, lib_name, DepRelation.CONTEXT))
            return "<hdlmake use_pattern %s.%s>" % (lib_name, pkg_name)
        buf = re.sub(use_context_pattern, do_use_context, buf)

        context_declaration_pattern = re.compile(
            r"^\s*context\s+(?P<name>\w+)\s+is\s+"
              r".*?"
            r"end\s*(context\s*)?(?P=name)?\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)
        def do_context_declaration(text):
            """Function to be applied by re.sub to every match of the
            context_declaration_pattern in the VHDL code -- group() returns
            positive matches as indexed plain strings. It adds the found PROVIDE
            relations to the file

            """
            ctx_name = text.group(1)
            logging.debug("found entity %s.%s", dep_file.library, ctx_name)
            graph.add_provide(
                dep_file,
                DepRelation(ctx_name, dep_file.library, DepRelation.CONTEXT))
            return "<hdlmake entity_pattern %s.%s>" % (dep_file.library, ctx_name)
        buf = re.sub(context_declaration_pattern, do_context_declaration, buf)

        # new entity
        entity_pattern = re.compile(
            r"^\s*entity\s+(?P<name>\w+)\s+is\s+"
              r".*?"
            r"end\s*(entity\s*)?(?P=name)?\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)
        def do_entity(text):
            """Function to be applied by re.sub to every match of the
            entity_pattern in the VHDL code -- group() returns positive matches
            as indexed plain strings. It adds the found PROVIDE relations
            to the file"""
            ent_name = text.group(1)
            logging.debug("found entity %s.%s", dep_file.library, ent_name)
            graph.add_provide(
                dep_file,
                DepRelation(ent_name, dep_file.library, DepRelation.ENTITY))
            return "<hdlmake entity_pattern %s.%s>" % (dep_file.library, ent_name)

        buf = re.sub(entity_pattern, do_entity, buf)

        # new architecture
        architecture_split_pattern = re.compile(
            r"^\s*architecture\s+(?P<name>\w+)\s+of\s+(\w+)\s+is",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_architecture(text):
            """Function to be applied by re.sub to every match of the
            architecture_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It adds the found PROVIDE
            relations to the file"""
            arch_name = text.group(1)
            ent_name = text.group(2)
            logging.debug("found architecture %s of entity %s.%s",
                          arch_name, dep_file.library, ent_name)
            graph.add_provide(
                dep_file,
                DepRelation(ent_name, dep_file.library, DepRelation.ARCHITECTURE))
            # The architecture depends on the entity.
            graph.add_require(
                dep_file,
                DepRelation(ent_name, dep_file.library, DepRelation.ENTITY))

            return "<hdlmake architecture %s.%s>" % (dep_file.library,
                                                     text.group(2))
        buf = re.sub(architecture_split_pattern, do_architecture, buf)

        # new package
        package_pattern = re.compile(
            r"^\s*package\s+(\w+)\s+is",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_package(text):
            """Function to be applied by re.sub to every match of the
            package_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It adds the found PROVIDE
            relations to the file"""
            pkg_name = text.group(1)
            logging.debug("found package %s.%s", dep_file.library, pkg_name)
            graph.add_provide(
                dep_file,
                DepRelation(pkg_name, dep_file.library, DepRelation.PACKAGE))
            return "<hdlmake package %s.%s>" % (dep_file.library, pkg_name)
        buf = re.sub(package_pattern, do_package, buf)

        # component declaration
        component_pattern = re.compile(
            r"^\s*component\s+(\w+).*?end\s+component.*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_component(text):
            """Function to be applied by re.sub to every match of the
            component_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add any relation
            to the file"""
            logging.debug("found component declaration %s", text.group(1))
            return "<hdlmake component %s>" % text.group(1)

        buf = re.sub(component_pattern, do_component, buf)

        # Signal declaration
        signal_pattern = re.compile(
            r"^\s*signal\s+(\w+).*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_signal(text):
            """Function to be applied by re.sub to every match of the
            signal_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add any relation
            to the file"""
            logging.debug("found signal declaration %s", text.group(1))
            return "<hdlmake signal %s>" % text.group(1)

        buf = re.sub(signal_pattern, do_signal, buf)

        # Constant declaration
        constant_pattern = re.compile(
            r"^\s*constant\s+(\w+).*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_constant(text):
            """Function to be applied by re.sub to every match of the
            constant_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add any relation
            to the file"""
            logging.debug("found constant declaration %s", text.group(1))
            return "<hdlmake constant %s>" % text.group(1)

        buf = re.sub(constant_pattern, do_constant, buf)


        # record declaration
        record_pattern = re.compile(
            r"^\s*type\s+(\w+)\s+is\s+record.*?end\s+record.*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_record(text):
            """Function to be applied by re.sub to every match of the
            record_pattern in the VHDL code -- group() returns positive matches
            as indexed plain strings. It doesn't add any relation to the
            file"""
            logging.debug("found record declaration %s", text.group(1))
            return "<hdlmake record %s>" % text.group(1)

        buf = re.sub(record_pattern, do_record, buf)

        # function declaration
        function_pattern = re.compile(
            r"^\s*function\s+(?P<name>\w+)"
            r".*?" # gobble arguments if any.
            r"return\s+\w+"
            r"(\s+is.*?end\s+function.*?)?" # gobble body if any.
            r"\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_function(text):
            """Function to be applied by re.sub to every match of the
            funtion_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It doesn't add the relations
            to the file"""
            logging.debug("found function declaration %s", text.group(1))
            return "<hdlmake function %s>" % text.group(1)

        buf = re.sub(function_pattern, do_function, buf)

        # component instantiation
        instance_component_pattern = re.compile(
            r"^\s*(?P<LABEL>\w+)\s*:"
            r"\s*(?:component\s+)?(?P<COMPONENT>\w+)\s*"
            r"(?:port|generic)\s+map.*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_instance_component(text):
            """Function to be applied by re.sub to every match of the
            instance_component_pattern in the VHDL code"""
            logging.debug("found component instantiation %s %s", text.group(1), text.group(2))
            comp_name = text.group("COMPONENT")
            graph.add_require(
                dep_file,
                DepRelation(comp_name, dep_file.library, DepRelation.ENTITY))
            return "<hdlmake component instance %s as %s>" % (comp_name, text.group("LABEL"))
        buf = re.sub(instance_component_pattern, do_instance_component, buf)

        # direct instantiations
        direct_instance_pattern = re.compile(
            r"^\s*(?P<LABEL>\w+)\s*:"
            r"\s*entity\s+((?P<LIB>\w+)\.)?(?P<ENTITY>\w+)"
            r"\s*(?:\(\s*(?P<ARCH>\w+)\s*\)\s*)?"
            r"(?:port|generic)\s+map.*?;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_direct_instance(text):
            """Function to be applied by re.sub to every match of the
            direct_instance_pattern in the VHDL code"""
            logging.debug("-> instantiates %s.%s(%s) as %s",
                          text.group("LIB"), text.group("ENTITY"), text.group("ARCH"), text.group("LABEL"))
            lib_name = text.group("LIB")
            if not lib_name or lib_name == "work":
                lib_name = dep_file.library
            ent_name = text.group("ENTITY")
            graph.add_require(
                dep_file,
                DepRelation(ent_name, lib_name, DepRelation.ENTITY))
            return "<hdlmake direct instance %s|%s|%s>" % (text.group("LABEL"), lib_name, ent_name)
        buf = re.sub(direct_instance_pattern, do_direct_instance, buf)

        # libraries
        library_pattern = re.compile(
            r"^\s*library\s*(\w+)\s*;",
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

        def do_library(text):
            """Function to be applied by re.sub to every match of the
            library_pattern in the VHDL code -- group() returns positive
            matches as indexed plain strings. It adds the used libraries
            to the file's 'library' property"""
            logging.debug("use library %s", text.group(1))
            return "<hdlmake library %s>" % text.group(1)
        buf = re.sub(library_pattern, do_library, buf)
        # logging.debug("\n" + buf) # print modified buffer.

