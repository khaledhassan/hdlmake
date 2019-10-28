"""This provides the stuff related with the HDLMake module,
from files to required submodules"""

from __future__ import absolute_import
import logging
from ..fetch.git import Git
from ..util import path as path_mod
import six
import os

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


class ModuleContent(object):

    """Class providing the HDLMake module content"""

    def __init__(self):
        # Manifest Files Properties
        self.files = None
        # Manifest Modules Properties
        self.modules = {'local': [], 'git': [], 'gitsm': [], 'svn': []}
        self.incl_makefiles = []
        self.library = "work"
        self.pool = None
        self.top_manifest = None
        self.manifest_dict = {}
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

    def process_manifest(self):
        """Process the content section of the manifest_dict"""
        logging.debug("Process manifest at: " + os.path.dirname(self.path))
        self._process_manifest_universal()
        self._process_manifest_files()
        self._process_manifest_modules()
        self._process_manifest_makefiles()
        self._process_git_submodules()

    def _process_manifest_universal(self):
        """Method processing the universal manifest directives;
           set library (inherited if not set) and action"""
        # Libraries
        if "library" in self.manifest_dict:
            self.library = self.manifest_dict["library"]
        elif self.parent:
            self.library = self.parent.library

    def _create_file_list_from_paths(self, paths):
        """
        Build a Source File Set containing the files indicated by the
        provided list of paths
        """
        from ..sourcefiles.srcfile import create_source_file, SourceFileSet
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
        from ..sourcefiles.srcfile import SourceFileSet
        # HDL files provided by the module
        if "files" not in self.manifest_dict:
            self.files = SourceFileSet()
            logging.debug("No files in the manifest at %s", self.path or '?')
        else:
            self.manifest_dict["files"] = path_mod.flatten_list(
                self.manifest_dict["files"])
            logging.debug("Files in %s: %s to library %s" ,
                          self.path,
                          str(self.manifest_dict["files"]),
                          self.library)
            paths = self._make_list_of_paths(self.manifest_dict["files"])
            self.files = self._create_file_list_from_paths(paths=paths)

    def fetchto(self):
        """Get the fetchto folder for the module"""
        return os.path.dirname(self.path)

    def _get_fetchto(self):
        """Calculate the fetchto folder"""
        if ("fetchto" in self.manifest_dict and
                self.manifest_dict["fetchto"] is not None):
            fetchto = path_mod.rel2abs(self.manifest_dict["fetchto"],
                                       self.path)
        else:
            fetchto = self.fetchto()
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
                mods.append(self.pool.new_module(
                    parent=self, url=path, source=m, fetchto=fetchto))
            self.modules[m] = mods

    def _process_git_submodules(self):
        """Get the submodules if found in the Manifest path"""
        if not self.source == 'gitsm':
            return
        git_submodule_dict = Git.get_git_submodules(self)
        git_toplevel = Git.get_git_toplevel(self)
        for submodule_key in git_submodule_dict.keys():
            url = git_submodule_dict[submodule_key]["url"]
            path = git_submodule_dict[submodule_key]["path"]
            path = os.path.join(git_toplevel, path)
            fetchto = os.path.sep.join(path.split(os.path.sep)[:-1])
            self.modules['git'].append(self.pool.new_module(parent=self,
                                                            url=url,
                                                            fetchto=fetchto,
                                                            source='git'))

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

