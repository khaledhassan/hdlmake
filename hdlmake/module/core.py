"""Provides the core functionality for the HDLMake module"""

from __future__ import absolute_import
import os
import sys
import logging

from ..util import path as path_mod


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


class ModuleConfig(object):

    """This class containt the base properties and methods that
    need to be initialized for a proper behavior"""

    def __init__(self):
        self.source = None
        self.parent = None
        self.url = None
        self.branch = None
        self.revision = None
        self.path = None
        self.isfetched = False

    def init_config(self, module_args):
        """This initializes the module configuration.
        The function is executed by Module constructor"""
        self.parent = module_args.parent
        url = module_args.url
        self.source = module_args.source
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
