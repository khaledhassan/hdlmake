#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
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

"""This is the entry point for HDLMake working in command line app mode"""

from __future__ import print_function
from __future__ import absolute_import
import argparse
import sys
import logging
from hdlmake.util import shell
from hdlmake.util.termcolor import colored

from .manifest_parser.variables import ManifestParser
from .action.core import ActionCore
from ._version import __version__


def hdlmake(args):
    """This is the main function, where HDLMake starts.
    Here, we make the next processes:
        -- parse command
        -- check and set the environment
        -- prepare the global module containing the heavy common stuff
    """

    # Options
    parser = _get_parser()
    options = _get_options(args, parser)

    try:
        set_logging_level(options)

        # Create a ModulePool object, this will become our workspace
        action = ActionCore(options)
        action.load_top_module()
        action.run()

        # Execute the appropriated action for the freshly created modules pool
        _action_runner(action)
    except Exception as e:
        import traceback
        logging.error(e)
        if options.full_error:
            logging.error("Trace:")
            traceback.print_exc()
        quit(2)


def _action_runner(modules_pool):
    """Funtion that decodes and executed the action selected by the user"""
    options = modules_pool.options
    if options.command == "manifest-help":
        ManifestParser().print_help()
    elif options.command == "makefile":
        modules_pool.makefile()
    elif options.command == "fetch":
        modules_pool.fetch()
    elif options.command == "clean":
        modules_pool.clean()
    elif options.command == "list-mods":
        modules_pool.list_modules()
    elif options.command == "list-files":
        modules_pool.list_files()
    elif options.command == "tree":
        modules_pool.generate_tree()
    elif options.command is None:
        logging.info("No command selected")


def _get_parser():
    """This is the parser function, where options and commands are defined.
    Here, we make the next processes:
    """
    description = ("A tool designed to help FPGA designers to manage "
                 + "and share their HDL code by automatically finding file "
                 + "dependencies, writing synthesis & simulation Makefiles, "
                 + "and fetching IP-Core libraries from remote repositories.")
    parser = argparse.ArgumentParser("hdlmake", description=description)
    subparsers = parser.add_subparsers(title="commands", dest="command")
    makefile = subparsers.add_parser(
        "makefile",
        help="write the Makefile (default action for hdlmake)")
    makefile.add_argument(
        "-f", "--filename",
        help="name for the Makefile file to be created",
        default=None,
        dest="filename")
    subparsers.add_parser(
        "fetch",
        help="fetch and/or update all of the remote modules")
    subparsers.add_parser(
        "clean",
        help="clean all of the already fetched remote modules")
    listmod = subparsers.add_parser(
        "list-mods",
        help="list all modules together with their files")
    listmod.add_argument(
        "--with-files",
        help="list modules together with their files",
        default=False,
        action="store_true",
        dest="withfiles")
    listmod.add_argument(
        "--terse",
        help="do not print comments",
        default=False,
        action="store_true",
        dest="terse")
    listfiles = subparsers.add_parser(
        "list-files",
        help="list all of the files in the design hierarchy")
    listfiles.add_argument(
        "--delimiter",
        help="set delimitier for the list of files",
        dest="delimiter",
        default=None)
    listfiles.add_argument(
        "--reverse",
        help="reverse the order for the list of files",
        dest="reverse",
        default=False,
        action="store_true")
    listfiles.add_argument(
        "--top",
        help="print only those files required to build 'top'",
        dest="top",
        default=None)
    tree = subparsers.add_parser(
        "tree",
        help="generate a module hierarchy tree graph")
    tree.add_argument(
        "--with-files",
        help="add files to the module hierarchy tree",
        default=False,
        action="store_true",
        dest="withfiles")
    tree.add_argument(
        "--mode",
        dest="mode",
        default="mods",
        help="set the working mode for the tree generator: "
             "(mods, dfs, bfs)")
    subparsers.add_parser(
        "manifest-help",
        help="print manifest file variables description")
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        help="print the version of this program",
        version=parser.prog +
        " " +
        __version__)
    parser.add_argument(
        '-a',
        '--all',
        action='store_true',
        dest="all_files",
        help="use all the listed files, do not solve the fileset")
    parser.add_argument(
        "--log",
        dest="log",
        default="info",
        help="logging level: debug, info, warning, error, critical")
    parser.add_argument(
        "--logfile",
        help="path to the optional log file",
        default=None,
        dest="logfile")
    parser.add_argument(
        "-p", "--prefix",
        dest="prefix_code",
        default="",
        help="Python code executed before every Manifest.py")
    parser.add_argument(
        "-s", "--suffix",
        dest="suffix_code",
        default="",
        help="Python code executed after every Manifest.py")
    parser.add_argument(
        "--full-error",
        default=False,
        action="store_true",
        dest="full_error",
        help="display full error log with traceback")
    return parser

def set_logging_level(options):
    """Set the log level and config (A.K.A. log verbosity)"""
    numeric_level = getattr(logging, options.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise Exception('Invalid log level: %s' % options.log)

    if not shell.check_windows() and options.logfile == None:
        logging.basicConfig(
            format=colored(
                "%(levelname)s",
                "yellow") + colored(
                "\t%(filename)s:%(lineno)d: %(funcName)s()\t",
                "blue") + "%(message)s",
            level=numeric_level)
    else:
        logging.basicConfig(
            format="%(levelname)s" +
                   "\t%(filename)s:%(lineno)d: %(funcName)s()\t" +
                   "%(message)s",
            level=numeric_level,
            filename=options.logfile)
    logging.debug(str(options))


def _get_options(args, parser):
    """Function that decodes and set the provided command user options"""
    options = None
    if len(args) == 0:
        options = parser.parse_args(['makefile'])
    elif len(args) == 2 and (
             args[0] == '-f' or args[0] == '--filename'):
        options = parser.parse_args(['makefile'] + args)
    else:
        options = parser.parse_args(args)
    return options


def main():
    """Entry point used by the executable"""
    hdlmake(sys.argv[1:])
