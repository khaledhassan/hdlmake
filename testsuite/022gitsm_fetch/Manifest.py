action = "simulation"

sim_tool="modelsim"

top_module = "gate"
fetchto = "ipcores"

files = [ "../files/gate.vhdl" ]
modules = { "gitsm" : "git@test.org:tester/module1.git" }
