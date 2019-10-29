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
from ..fetch import git
from ..manifest_parser.manifestparser import ManifestParser
import six


class ModuleArgs(object):
    """This class is just a container for the main Module args"""

    def __init__(self):
        self.parent = None
        self.url = None
        self.source = 'local'
        self.fetchto = None

    def set_args(self, parent, url, source, fetchto):
        """Set the module arguments"""
        self.parent = parent
        self.url = url
        self.source = source or 'local'
        self.fetchto = fetchto


class Module(object):

    """
    This is the class providing the HDLMake module, the basic element
    providing the modular behavior allowing for structured designs.

    Note: a module is identified by its URL.
    """

    def __init__(self, module_args, action):
        """Calculate and initialize the origin attributes: path, source..."""
        assert module_args.url is not None
        assert module_args.source is not None
        self.manifest_dict = {}
        # Manifest Files Properties
        self.files = None
        # Manifest Modules Properties
        self.modules = {'local': [], 'git': [], 'gitsm': [], 'svn': []}
        self.incl_makefiles = []                # List of paths of makefile files to include.
        self.library = "work"
        self.action = None
        self.top_manifest = action.get_top_manifest()
        self.manifest_dict = {}
        self.source = module_args.source        # The fetcher (module, git, ...)
        self.parent = module_args.parent
        self.url = None
        self.branch = None
        self.revision = None
        self.path = None                        # Relative path to the module.
        self.isfetched = False                  # True if the module exists on the file system.
        self.init_config(module_args)
        self.action = action
        self.module_args = module_args

    def __str__(self):
        return self.module_args.url

    def init_config(self, module_args):
        """This initializes the module configuration.
        The function is executed by Module constructor"""
        url = module_args.url
        fetchto = module_args.fetchto

        if self.source == 'local':
            self.url, self.branch, self.revision = url, None, None

            if not os.path.exists(url):
                raise Exception(
                    "Path to the local module doesn't exist:\n" + url
                    + "\nThis module was instantiated in: " + str(self.parent))
            self.path = path_mod.relpath(url)
            self.isfetched = True
        else:
            # Split URL (extract basename, revision, branch...)
            if self.source == 'svn':
                self.url, self.revision = path_mod.svn_parse(url)
                basename = path_mod.svn_basename(self.url)
            else:
                self.url, self.branch, self.revision = path_mod.url_parse(url)
                basename =  path_mod.url_basename(self.url)
            self.path = path_mod.relpath(os.path.abspath(
                os.path.join(fetchto, basename)))

            # Check if the module dir exists and is not empty
            if os.path.exists(self.path) and os.listdir(self.path):
                self.isfetched = True
                logging.debug("Module %s (parent: %s) is fetched.",
                              url, self.parent.path)
            else:
                self.isfetched = False
                logging.debug("Module %s (parent: %s) is NOT fetched.",
                              url, self.parent.path)

    def process_manifest(self):
        """Process the content section of the manifest_dict"""
        logging.debug("Process manifest at: " + os.path.dirname(self.path))
        self._process_manifest_universal()
        self._process_manifest_files()
        self._process_manifest_modules()
        self._process_manifest_makefiles()

    def _process_manifest_universal(self):
        """Method processing the universal manifest directives;
           set library (inherited if not set)."""
        # Libraries
        if "library" in self.manifest_dict:
            self.library = self.manifest_dict["library"]
        elif self.parent:
            self.library = self.parent.library

    def _check_filepath(self, filepath):
        """Check the provided filepath against several conditions"""
        if filepath:
            if path_mod.is_abs_path(filepath):
                logging.warning(
                    "Specified path seems to be an absolute path: " +
                    filepath + "\nOmitting.")
                return False
            filepath = os.path.join(self.path, filepath)
            if not os.path.exists(filepath):
                raise Exception(
                    "Path specified in manifest {} doesn't exist: {}".format(
                    self.path, filepath))

            filepath = path_mod.rel2abs(filepath, self.path)
            if os.path.isdir(filepath):
                logging.warning(
                    "Path specified in manifest %s is a directory: %s",
                    self.path, filepath)
        return True

    def _make_list_of_paths(self, list_of_paths):
        """Get a list with only the valid absolute paths from the provided"""
        paths = []
        for filepath in list_of_paths:
            if self._check_filepath(filepath):
                paths.append(path_mod.rel2abs(filepath, self.path))
        return paths

    def _create_file_list_from_paths(self, paths):
        """
        Build a Source File Set containing the files indicated by the
        provided list of paths
        """
        from ..sourcefiles.srcfile import create_source_file
        from ..sourcefiles.sourcefileset import SourceFileSet
        srcs = SourceFileSet()
        # Check if this is the top module and grab the include_dirs
        if self.parent is None:
            include_dirs = self.manifest_dict.get('include_dirs', [])
        else:
            include_dirs = self.top_manifest.manifest_dict.get(
                'include_dirs', [])
        for path_aux in paths:
            if os.path.isdir(path_aux):
                # If a path is a dir, add all the files of that dir.
                dir_ = os.listdir(path_aux)
                for f_dir in dir_:
                    f_dir = os.path.join(self.path, path_aux, f_dir)
                    if not os.path.isdir(f_dir):
                        srcs.add(create_source_file(path=f_dir,
                                                    module=self,
                                                    library=self.library,
                                                    include_dirs=include_dirs))
            else:
                srcs.add(create_source_file(path=path_aux,
                                            module=self,
                                            library=self.library,
                                            include_dirs=include_dirs))
        return srcs

    def _process_manifest_files(self):
        """Process the files instantiated by the HDLMake module"""
        from ..sourcefiles.sourcefileset import SourceFileSet
        # HDL files provided by the module
        files = self.manifest_dict.get('files')
        if files is None:
            self.files = SourceFileSet()
            logging.debug("No files in the manifest at %s", self.path or '?')
        else:
            # Be sure it is a list.
            files = path_mod.flatten_list(files)
            self.manifest_dict["files"] = files
            logging.debug("Files in %s: %s to library %s" ,
                          self.path,
                          str(self.manifest_dict["files"]),
                          self.library)
            paths = self._make_list_of_paths(files)
            self.files = self._create_file_list_from_paths(paths=paths)

    def fetchto(self):
        """Get the fetchto folder for the module"""
        return os.path.dirname(self.path)

    def _get_fetchto(self):
        """Calculate the fetchto folder"""
        fetchto = self.manifest_dict.get('fetchto')
        if fetchto is None:
            fetchto = self.fetchto()
        else:
            fetchto = path_mod.rel2abs(fetchto, self.path)
        return fetchto

    def _process_manifest_modules(self):
        """Process the submodules required by the HDLMake module"""
        # Process required modules
        if "modules" not in self.manifest_dict:
            return
        fetchto = self._get_fetchto()
        for m in self.modules:
            if m not in self.manifest_dict["modules"]:
                continue
            paths = path_mod.flatten_list(self.manifest_dict["modules"][m])
            self.manifest_dict["modules"][m] = paths
            mods = []
            for path in paths:
                if m == 'local':
                    if path_mod.is_abs_path(path):
                        raise Exception("Found an absolute path (" + path +
                                        ") in a manifest(" + self.path + ")")
                    path = path_mod.rel2abs(path, self.path)
                mods.append(self.action.new_module(
                    parent=self, url=path, source=m, fetchto=fetchto))
            self.modules[m] = mods

    def _process_manifest_makefiles(self):
        """Get the extra makefiles defined in the HDLMake module"""
        # Included Makefiles
        included_makefiles_aux = []
        if "incl_makefiles" in self.manifest_dict:
            if isinstance(self.manifest_dict["incl_makefiles"],
                    six.string_types):
                included_makefiles_aux.append(
                    self.manifest_dict["incl_makefiles"])
            else:  # list
                included_makefiles_aux = self.manifest_dict["incl_makefiles"][:]
        makefiles_paths = self._make_list_of_paths(included_makefiles_aux)
        self.incl_makefiles.extend(makefiles_paths)

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
        - the arbitrary code from action's top_module options
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

        manifest_parser.add_prefix_code(self.action.options.prefix_code)
        manifest_parser.add_suffix_code(self.action.options.suffix_code)

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
