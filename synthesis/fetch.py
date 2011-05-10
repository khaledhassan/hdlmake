#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import msg as p
import global_mod
import path

def fetch_from_svn(url, revision = None, fetchto = None):
    if fetchto == None:
        fetchto = global_mod.fetchto

    if not os.path.exists(fetchto):
        os.mkdir(fetchto)

    cur_dir = os.getcwd()
    os.chdir(fetchto)
    basename = path.url_basename(url)

    cmd = "svn checkout {0} " + basename
    if revision:
        cmd = cmd.format(url + '@' + revision)
    else:
        cmd = cmd.format(url)

    p.vprint(cmd)
    os.system(cmd)
    os.chdir(cur_dir)

def fetch_from_git(url, revision = None, fetchto = None):
    if fetchto == None:
        fetchto = global_mod.fetchto

    basename = path.url_basename(url)
    if basename.endswith(".git"):
        basename = basename[:-4] #remove trailing .git

    if not os.path.exists(fetchto):
        if not global_mod.fetch:
            return None;
        os.mkdir(fetchto)

    if os.path.exists(fetchto+"/"+basename):
        if global_mod.options.fetch:
            update_only = True;
            do_fetch = True;
        else:
            return True;
    else:
        if(global_mod.options.fetch):
            update_only = False;
            do_fetch = True;
        else:
            return None

    rval = True
    if do_fetch:

        cur_dir = os.getcwd()
        os.chdir(fetchto)

        if update_only:
            fdir = fetchto+"/"+basename;
            os.chdir(fdir);
            cmd = "git pull"
            p.vprint(cmd);
            if os.system(cmd) != 0:
                rval = False
            os.chdir(fetchto)

        else:  		
            cmd = "git clone " + url
            p.vprint(cmd);
            if os.system(cmd) != 0:
                rval = False
	    

        if revision and rval:
            os.chdir(basename)
            if os.system("git checkout " + revision) != 0:
                rval = False
            
        os.chdir(cur_dir)

    return rval

def parse_repo_url(url) :
    """
    Check if link to a repo seems to be correct
    """
    import re
    url_pat = re.compile("[ \t]*([^ \t]+)[ \t]*(@[ \t]*(.+))?[ \t]*")
    url_match = re.match(url_pat, url)

    if url_match == None:
        p.echo("Not a correct repo url: {0}. Skipping".format(url))
    if url_match.group(3) != None: #there is a revision given 
        ret = (url_match.group(1), url_match.group(3))
    else:
        ret = url_match.group(1)
    return ret


