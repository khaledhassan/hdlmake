`include "macros.v"

module gate;
  // My comment
`ifdef MYWIRE
  `MYWIRE(w);
`endif
endmodule
