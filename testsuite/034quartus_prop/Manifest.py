action = "synthesis"
language = "vhdl"

syn_family  = "Arria V"
syn_device  = "5agxmb1g4f"
syn_grade   = "c4"
syn_package = "40"

syn_top = "gate"
syn_project = "gate_prj"

syn_tool = "quartus"
include_dirs=['.']
syn_properties=[{'what': 'vwaht', 
                 'name': 'vname', 'from': 'vfrom', 'value': 'vval',
                 'tag': 'vtag',
                'to': 'vto', 'section_id': 'vsid'}]

files = [ "../files/gate.vhdl" ]
