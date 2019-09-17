`define DEF_A

module gate;
  // My comment
`ifdef DEF_A
mod_a mod_a ();
`elsif DEF_B
mod_b mod_b ();
`else
mod_c mod_c ();
`endif
endmodule
