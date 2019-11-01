# HDLmake testsuite
# Just run 'pytest' in this directory.

import hdlmake.main
from hdlmake.manifest_parser.configparser import ConfigParser
import os
import os.path
import pytest
import shutil

class Config(object):
    def __init__(self, path=None, my_os='unx', fakebin="linux_fakebin"):
        self.path = path
        self.prev_env_path = os.environ['PATH']
        self.prev_check_windows_commands = hdlmake.util.shell.check_windows_commands
        self.prev_check_windows_tools = hdlmake.util.shell.check_windows_tools
        assert my_os in ('unx', 'windows', 'cygwin')
        self.check_windows_commands = my_os == 'windows'
        self.check_windows_tools = my_os in ('windows', 'cygwin')
        self.fakebin = fakebin

    def __enter__(self):
        os.environ['PATH'] = ("../" + self.fakebin + ":"
            + os.path.abspath(self.fakebin) + ':'
            + self.prev_env_path)
        if self.path is not None:
            os.chdir(self.path)
        hdlmake.util.shell.check_windows_tools = (lambda : self.check_windows_tools)
        hdlmake.util.shell.check_windows_commands = (lambda : self.check_windows_commands)

    def __exit__(self, *_):
        if self.path is not None:
            os.chdir("..")
        os.environ['PATH'] = self.prev_env_path
        hdlmake.util.shell.check_windows_tools = self.prev_check_windows_tools
        hdlmake.util.shell.check_windows_commands = self.prev_check_windows_commands

def compare_makefile():
    ref = open('Makefile.ref', 'r').read()
    out = open('Makefile', 'r').read()
    # shutil.move('Makefile', 'Makefile.ref')  # To regenerate
    assert out == ref
    os.remove('Makefile')

def compare_makefile_filter(start):
    ref = open('Makefile.ref', 'r').readlines()
    out = open('Makefile', 'r').readlines()
    out = [l for l in out if not l.startswith(start)]
    assert out == ref
    os.remove('Makefile')

def compare_makefile_xilinx():
    # HDLmake make the path absolute.  Remove this line.
    compare_makefile_filter("XILINX_INI_PATH")

def run_compare(**kwargs):
    with Config(**kwargs) as _:
        hdlmake.main.hdlmake([])
        compare_makefile()

def run(args, **kwargs):
    with Config(**kwargs) as _:
        hdlmake.main.hdlmake(args)

def test_ise():
    run_compare(path="001ise")

def test_ise_windows():
    run_compare(path="071ise_windows", my_os='windows')

def test_ise_cygwin():
    run_compare(path="082ise_cygwin", my_os='cygwin')

def test_makefile_002():
    run_compare(path="002msim")

def test_makefile_003():
    run_compare(path="003msim")

def test_makefile_004():
    run_compare(path="004msim")

def test_filename_opt():
    run(['-f', 'my.mk'], path="062filename_opt")
    os.remove("062filename_opt/my.mk")

def test_fetch():
    run(['fetch'], path="001ise")

def test_clean():
    run(['clean'], path="001ise")

def test_list_mods_none():
    run(['list-mods'], path="001ise")

def test_list_files():
    run(['list-files'], path="001ise")

def test_circular_dep_096():
    run(['list-files'], path="096circular_dep")

def test_noact():
    with Config(path="005noact") as _:
        hdlmake.main.hdlmake(['manifest-help'])
        hdlmake.main.hdlmake(['list-files'])
        hdlmake.main.hdlmake(['list-mods', '--with-files'])

def test_ahdl():
    run_compare(path="006ahdl", my_os='windows')

def test_diamond():
    run_compare(path="007diamond")

def test_ghdl():
    run_compare(path="008ghdl")

def test_icestorm():
    with Config(path="009icestorm") as _:
        hdlmake.main.hdlmake([])
        compare_makefile_filter("TOOL_PATH")

def test_isim_010():
    with Config(path="010isim") as _:
        hdlmake.main.hdlmake([])
        compare_makefile_xilinx()

def test_isim_windows_060():
    with Config(path="060isim_windows",
                my_os='windows', fakebin="windows_fakebin") as _:
        hdlmake.main.hdlmake([])
        compare_makefile_xilinx()

def test_icarus_012():
    run_compare(path="012icarus")

def test_icarus_include_083():
    run_compare(path="083icarus_include")

def test_libero():
    run_compare(path="013libero")

def test_planahead():
    run_compare(path="014planahead")

def test_quartus():
    run_compare(path="015quartus")

def test_quartus016():
    run_compare(path="016quartus_nofam")

def test_quartus033():
    run_compare(path="033quartus")

def test_quartus034():
    run([], path="034quartus_prop")

def test_quartus035():
    with pytest.raises(SystemExit) as _:
        run([], path="035quartus_err")
    print(os.getcwd())
    os.remove('035quartus_err/Makefile')

def test_quartus036():
    with pytest.raises(SystemExit) as _:
        run([], path="036quartus_err")
    os.remove('036quartus_err/Makefile')

def test_quartus037():
    with pytest.raises(SystemExit) as _:
        run([], path="037quartus_err")
    os.remove('037quartus_err/Makefile')

def test_quartus038():
    with pytest.raises(SystemExit) as _:
        run([], path="038quartus_err")
    os.remove('038quartus_err/Makefile')

def test_quartus039():
    with pytest.raises(SystemExit) as _:
        run([], path="039quartus_err")
    #os.remove('039quartus_err/Makefile')

def test_riviera():
    run_compare(path="017riviera")

def test_vivado():
    run_compare(path="018vivado")

def test_vivado_props():
    run_compare(path="054vivado_props")

def test_vivado_sim():
    run_compare(path="019vsim")

def test_git_fetch():
    with Config(path="020git_fetch") as _:
        hdlmake.main.hdlmake(['list-files'])
        hdlmake.main.hdlmake(['fetch'])
        hdlmake.main.hdlmake(['list-mods'])
        shutil.rmtree('ipcores.old', ignore_errors=True)
        shutil.move('ipcores', 'ipcores.old')

def test_git_fetch_branch():
    with Config(path="055git_fetch_branch") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_rev():
    with Config(path="056git_fetch_rev") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_url():
    with Config(path="073git_fetch_url") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_url2():
    with Config(path="074git_fetch_url") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_git_fetch_err():
    with pytest.raises(SystemExit) as _:
        run(['fetch'], path="075err_git")
    shutil.rmtree('ipcores', ignore_errors=True)

def test_svn_fetch_err():
    with pytest.raises(SystemExit) as _:
        run(['--full-error', 'fetch'], path="094err_svn")
    shutil.rmtree('094err_svn/ipcores', ignore_errors=True)

def test_svn_fetch():
    with Config(path="021svn_fetch") as _:
        hdlmake.main.hdlmake(['list-mods'])
        hdlmake.main.hdlmake(['fetch'])
        hdlmake.main.hdlmake(['list-mods', '--with-files'])
        shutil.rmtree('ipcores')

def test_svn_fetch_rev():
    with Config(path="072svn_fetch_rev") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_gitsm_fetch():
    with Config(path="022gitsm_fetch") as _:
        hdlmake.main.hdlmake(['fetch'])
        hdlmake.main.hdlmake(['list-mods'])
        hdlmake.main.hdlmake(['clean'])
        shutil.rmtree('ipcores')

def test_git_fetch_cmds():
    with Config(path="065fetch_pre_post") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_sub_fetch():
    with Config(path="095sub_fetch") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_err_fetch():
    with pytest.raises(SystemExit) as _:
        run([], path="065fetch_pre_post")
        assert False

def test_xci():
    run_compare(path="023xci")

def test_vlog_parser():
    run_compare(path="024vlog_parser")

def test_vlog_parser025():
    run_compare(path="025vlog_parser")

def test_gitsm_fetch026():
    with Config(path="026gitsm_fetch") as _:
        hdlmake.main.hdlmake(['fetch'])
        shutil.rmtree('ipcores')

def test_vhdl_parser():
    run_compare(path="027vhdl_parser")

def test_manifest_print():
    run([], path="028manifest_print")
    os.remove('028manifest_print/Makefile')

def test_manifest_quit():
    with pytest.raises(SystemExit) as _:
        run([], path="029manifest_quit")
        assert False

def test_manifest_syntax():
    with pytest.raises(SystemExit) as _:
        run([], path="030manifest_syntax")
        assert False

def test_manifest_except():
    with pytest.raises(SystemExit) as _:
        run([], path="031manifest_except")
        assert False

def test_manifest_nameerr_098():
    with pytest.raises(SystemExit) as _:
        run([], path="098manifest_nameerr")
        assert False

def test_manifest_vars():
    run([], path="032manifest_vars")

def test_srcfiles():
    run_compare(path="040srcfiles")

def test_no_syn_tool():
    with pytest.raises(SystemExit) as _:
        run([], path="041err_syn")
        assert False

def test_no_files():
    run([], path="042nofiles")

def test_no_bin_061():
    with Config(path="061err_nobin", fakebin="no_fakebin") as _:
        hdlmake.main.hdlmake([])
        compare_makefile_xilinx()

def test_local043():
    run_compare(path="043local_fetch")

def test_files_dir():
    # Not sure we want to keep this feature: allow to specify a directory
    # as a file (will be replaced by all the files in the directory)
    run_compare(path="044files_dir")

def test_incl_makefile():
    run_compare(path="045incl_makefile")

def test_incl_makefiles():
    run_compare(path="046incl_makefiles")

def test_abs_local():
    with pytest.raises(SystemExit) as _:
        run([], path="047err_abs_local")
        assert False

def test_two_manifest():
    d = "048err_two_manifest"
    # Create manifest.py dynamically so that you can clone the
    # repo on windows/macosx
    shutil.copy(d + "/Manifest.py", d + "/manifest.py")
    with pytest.raises(SystemExit) as _:
        run([], path=d)

def test_no_manifest():
    with pytest.raises(SystemExit) as _:
        run([], path="049err_no_manifest")

def test_configparser_bad_descr():
    # More like a unittest
    with pytest.raises(ValueError) as _:
        _ = ConfigParser(description=1)

def test_configparser_dup_option():
    p = ConfigParser()
    p.add_option("a", type={})
    with pytest.raises(ValueError) as _:
        p.add_option("a", type=0)

def test_configparser_bad_option():
    p = ConfigParser()
    with pytest.raises(ValueError) as _:
        p.add_option("a", type=0, unknown=True)

def test_configparser_key():
    p = ConfigParser()
    p.add_option("a", type={})
    p.add_allowed_key("a", key="k")
    with pytest.raises(ValueError) as _:
        p.add_allowed_key("a", key=1)

def test_configparser_bad_type():
    # More like a unittest
    p = ConfigParser()
    with pytest.raises(RuntimeError) as _:
        p.add_type("a", type_new=[])

def test_configparser_unexpected_key():
    # More like a unittest
    p = ConfigParser()
    with pytest.raises(RuntimeError) as _:
        p.add_allowed_key("a", key="k1")
    p.add_option("a", type=[])
    with pytest.raises(RuntimeError) as _:
        p.add_allowed_key("a", key="k")

def test_err_manifest_type():
    with pytest.raises(SystemExit) as _:
        run([], path="050err_manifest_type")

def test_err_manifest_key():
    with pytest.raises(SystemExit) as _:
        run([], path="051err_manifest_key")

def test_svlog_parser():
    run_compare(path="052svlog_parser")

def test_err_vlog_include():
    with pytest.raises(SystemExit) as _:
        run([], path="077err_vlg_include")

def test_err_vlog_define():
    with pytest.raises(SystemExit) as _:
        run([], path="078err_vlg_define")

def test_err_vlog_no_macro():
    run_compare(path="079err_vlg_macro")

def test_err_vlog_recursion():
    with pytest.raises(SystemExit) as _:
        run([], path="080err_vlg_recursion")

def test_vlog_ifdef_elsif_else_081():
    run_compare(path="081vlog_ifdef_elsif_else")

def test_dep_level():
    run(['list-files'], path="053vlog_dep_level")
    run(['list-files', '--delimiter', ','], path="053vlog_dep_level")
    run(['list-files', '--reverse'], path="053vlog_dep_level")
    run(['list-files', '--top', 'level2'], path="053vlog_dep_level")

def test_modelsim_windows():
    assert hdlmake.util.shell.check_windows_tools() is False
    run_compare(path="057msim_windows", my_os='windows')

def test_nosim_tool():
    with pytest.raises(SystemExit) as _:
        run([], path="063err_nosim_tool")

def test_err_action():
    with pytest.raises(SystemExit) as _:
        run([], path="064err_action")

def test_err_loglevel():
    with pytest.raises(SystemExit) as _:
        run(['--log', 'unknown', 'makefile'], path="002msim")

def test_err_noaction():
    run(['--log', 'warning'], path="002msim")

def test_all_files():
    run(['-a', 'makefile'], path="002msim")

def test_err_sim_top():
    with pytest.raises(SystemExit) as _:
        run([], path="066err_sim_top")

def test_err_syn_dev():
    with pytest.raises(SystemExit) as _:
        run([], path="067err_syndev")
        assert False

def test_err_syn_grade():
    with pytest.raises(SystemExit) as _:
        run([], path="068err_syngrade")
        assert False

def test_err_syn_package():
    with pytest.raises(SystemExit) as _:
        run([], path="069err_synpackage")
        assert False

def test_err_syn_top():
    run_compare(path="070err_syntop")

def test_extra_modules():
    run_compare(path="076extra_modules")

def test_err_syntool():
    with pytest.raises(SystemExit) as _:
        run([], path="084bad_syn")
        assert False

def test_err_simtool():
    with pytest.raises(SystemExit) as _:
        run([], path="085bad_sim")
        assert False

def test_err_ise_no_family():
    with pytest.raises(SystemExit) as _:
        run([], path="086ise_no_family")
        assert False

def test_many_modules():
    run_compare(path="087many_modules")

def test_file_abs():
    run_compare(path="088bad_file_abs")

def test_err_missing_file():
    with pytest.raises(SystemExit) as _:
        run([], path="089missing_file")
        assert False

def test_err_missing_module():
    with pytest.raises(SystemExit) as _:
        run([], path="090missing_module")
        assert False

def test_library():
    run_compare(path="091library")

def test_err_filetype():
    with pytest.raises(SystemExit) as _:
        run([], path="092bad_filetype")
        assert False

def test_multi_sat():
    run_compare(path="093multi_sat")

def test_sys_package_097():
    with Config(path="097sys_package") as _:
        hdlmake.main.hdlmake([])
        compare_makefile_xilinx()

@pytest.mark.xfail
def test_xfail():
    """This is a self-consistency test: the test is known to fail"""
    run_compare(path="011xfail")
