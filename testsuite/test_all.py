# HDLmake testsuite
# Just run 'pytest' in this directory.

import hdlmake.__main__
import os
import os.path
import pytest
import shutil

class Config(object):
    def __init__(self, path=None, check_windows=False):
        self.path = path
        self.prev_env_path = os.environ['PATH']
        self.prev_check_windows = hdlmake.util.shell.check_windows
        self.check_windows = check_windows
    
    def __enter__(self):
        os.environ['PATH'] = ("../linux_fakebin:"
            + os.path.abspath('linux_fakebin') + ':'
            + self.prev_env_path)
        if self.path is not None:
            os.chdir(self.path)
        hdlmake.util.shell.check_windows = (lambda : self.check_windows)

    def __exit__(self, *_):
        if self.path is not None:
            os.chdir("..")
        os.environ['PATH'] = self.prev_env_path
        hdlmake.util.shell.check_windows = self.prev_check_windows

def compare_makefile():
    ref = open('Makefile.ref', 'r').read()
    out = open('Makefile', 'r').read()
    assert out == ref
    os.remove('Makefile')


def run_compare(**kwargs):
    with Config(**kwargs) as _:
        hdlmake.__main__.hdlmake([])
        compare_makefile()

def test_makefile_001():
    run_compare(path="001ise")

def test_makefile_002():
    run_compare(path="002msim")

def test_makefile_003():
    run_compare(path="003msim")
    
def test_makefile_004():
    run_compare(path="004msim")
    
def test_fetch():
    with Config(path="001ise") as _:
        hdlmake.__main__.hdlmake(['fetch'])

def test_clean():
    with Config(path="001ise") as _:
        hdlmake.__main__.hdlmake(['clean'])

def test_list_mods():
    with Config(path="001ise") as _:
        hdlmake.__main__.hdlmake(['list-mods'])

def test_list_files():
    with Config(path="001ise") as _:
        hdlmake.__main__.hdlmake(['list-files'])

def test_noact():
    with Config(path="005noact") as _:
        hdlmake.__main__.hdlmake(['manifest-help'])
        hdlmake.__main__.hdlmake(['list-files'])

def test_ahdl():
    run_compare(path="006ahdl", check_windows=True)

def test_diamond():
    run_compare(path="007diamond")

def test_ghdl():
    run_compare(path="008ghdl")

def test_icestorm():
    run_compare(path="009icestorm")

def test_isim():
    with Config(path="010isim") as _:
        hdlmake.__main__.hdlmake([])
        ref = open('Makefile.ref', 'r').readlines()
        out = open('Makefile', 'r').readlines()
        # HDLmake make the path absolute.  Remove this line.
        out = [l for l in out if not l.startswith("XILINX_INI_PATH")]
        assert out == ref
        os.remove('Makefile')

def test_icarus():
    run_compare(path="012icarus")

def test_libero():
    run_compare(path="013libero")

def test_planahead():
    run_compare(path="014planahead")

def test_quartus():
    run_compare(path="015quartus")

def test_quartus016():
    run_compare(path="016quartus_nofam")

def test_riviera():
    run_compare(path="017riviera")

def test_vivado():
    run_compare(path="018vivado")

def test_vivado_sim():
    run_compare(path="019vsim")

def test_git_fetch():
    with Config(path="020git_fetch") as _:
        hdlmake.__main__.hdlmake(['fetch'])
        shutil.rmtree('ipcores.old', ignore_errors=True)
        shutil.move('ipcores', 'ipcores.old')

def test_svn_fetch():
    with Config(path="021svn_fetch") as _:
        hdlmake.__main__.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_gitsm_fetch():
    with Config(path="022gitsm_fetch") as _:
        hdlmake.__main__.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

@pytest.mark.xfail
def test_xfail():
    """This is a self-consistency test: the test is known to fail"""
    run_compare(path="011xfail")
