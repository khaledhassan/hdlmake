action = "synthesis"
fetchto = '.'

syn_device = "xc6slx45t"
syn_grade = "-3"
syn_package = "fgg484"

syn_top = "gate"
syn_project = "gate.xise"

syn_tool = "vivado"
syn_properties = [['prop1', 'val1' 'obj'],
                  ["prop2", "is", "too", "long"],
                  ["prop3 options", "obj"],
                  ["prop4 err", "obj"],
                  ["steps.synth_design", "2"],
                  ["steps.impl", "3"]]

files = [ "../files/gate.vhdl" ]
