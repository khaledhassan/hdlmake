target = "microsemi"
syn_tool = "liberosoc"
action = "synthesis"
language = "verilog"

syn_family = "IGLOO2"
syn_device = "M2GL060"
syn_grade = "-1"
syn_package = "484 FBGA"
syn_top = "igloo2_top"
syn_project = "demo"

modules = {
  "local" : [ "../../../top/igloo2/verilog" ],
}
