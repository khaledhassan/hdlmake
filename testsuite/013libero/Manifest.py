action = "synthesis"

syn_tool="libero"
syn_device="anfpga"
syn_grade="3"
syn_package="ff"
syn_project="gate"

top_module = "gate"

# Not reliable.
#files = [ "../files/gate.vhdl", "syn.sdc", "comp.pdc" ]

files = [ "../files/gate.vhdl", "syn.sdc" ]
