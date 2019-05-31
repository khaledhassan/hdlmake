action = "simulation"

sim_tool="modelsim"

top_module = "gate"
fetchto = "ipcores"

files = [ "../files/gate.vhdl" ]
modules = { "svn" : "http://test.org:tester/module1" }
