#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2016 CERN
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

"""
This python module is the one in charge to support the HDLMake modules
It includes the base Module class, that inherits several action
specific parent modules providing specific methods and attributes.

"""

from __future__ import print_function
from __future__ import absolute_import
import os
import logging

from ..util import path as path_mod
from ..util import shell
from ..manifest_parser.manifestparser import ManifestParser
from .content import ModuleContent, ModuleArgs
import six


class Module(ModuleContent):

    """
    This is the class providing the HDLMake module, the basic element
    providing the modular behavior allowing for structured designs.
    """

    def __init__(self, module_args, pool):
        """Calculate and initialize the origin attributes: path, source..."""
        assert module_args.url is not None
        assert module_args.source is not None
        self.manifest_dict = {}
        super(Module, self).__init__()
        self.init_config(module_args)
        self.pool = pool
        self.top_manifest = pool.get_top_manifest()
        self.module_args = module_args

    def __str__(self):
        return self.module_args.url

    def submodules(self):
        """Get a list with all the submodules this module instance requires"""
        return self.modules['local'] + self.modules['git'] \
            + self.modules['gitsm'] + self.modules['svn']

    def remove_dir_from_disk(self):
        """Delete the module dir if it is already fetched and available"""
        assert self.isfetched
        logging.debug("Removing " + self.path)
        command_tmp = shell.rmdir_command() + " " + self.path
        shell.run(command_tmp)

    def _search_for_manifest(self):
        """Look for manifest in the given folder and create a Manifest object
        """
        logging.debug("Looking for manifest in " + self.path)
        dir_files = os.listdir(self.path)
        if "manifest.py" in dir_files and "Manifest.py" in dir_files:
            raise Exception(
                "Both manifest.py and Manifest.py" +
                "found in the module directory: %s",
                self.path)
        for filename in dir_files:
            if filename == "manifest.py" or filename == "Manifest.py":
                if not os.path.isdir(filename):
                    logging.debug("Found manifest for module %s: %s",
                                  self.path, filename)
                    return os.path.join(self.path, filename)
        raise Exception("No manifest found in path: {}".format(self.path))

    def parse_manifest(self):
        """
        Create a dictionary from the module Manifest.py and assign it
        to the manifest_dict property.
        In order to do this, it creates a ManifestParser object and
        feeds it with:
        - the arbitrary code from pool's top_module options
            (it assumes a top_module exists before any parsing!)
        - the Manifest.py (if exists)
        - the extra_context:
          - If this is the root module (has not parent),
              use an empty extra_context in the parser
          - If this is a submodule (has a parent),
              inherit the extra_context as:
            - the full manifest_dict from the top_module...
            - ...but deleting some key fields that needs to be respected.
        """

        if self.manifest_dict or self.isfetched is False:
            return
        assert self.path is not None

        filename = self._search_for_manifest()
        logging.debug("Parse manifest in: %s", filename)

        logging.debug("""
***********************************************************
PARSE START: %s
***********************************************************""", self.path)

        manifest_parser = ManifestParser()

        manifest_parser.add_prefix_code(self.pool.options.prefix_code)
        manifest_parser.add_suffix_code(self.pool.options.suffix_code)

        # Parse and extract variables from it.
        if self.parent is None:
            extra_context = {}
        else:
            extra_context = dict(self.top_manifest.manifest_dict)
        extra_context["__manifest"] = self.path

        # The parse method is where most of the parser action takes place!
        try:
            self.manifest_dict = manifest_parser.parse(config_file=filename, extra_context=extra_context)
        except NameError as name_error:
            raise Exception(
                "Error while parsing {0}:\n{1}: {2}.".format(
                    self.path, type(name_error), name_error))

        # Process the parsed manifest_dict to assign the module properties
        self.process_manifest()

        # Recurse: parse every detected submodule
        for submod in self.submodules():
            submod.parse_manifest()

        logging.debug("""
***********************************************************
PARSE END: %s
***********************************************************

                      """, self.path)
