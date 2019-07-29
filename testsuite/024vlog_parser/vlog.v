`include "macros.v"

module gate;
  // My comment
`ifdef MYWIRE
  `MYWIRE(w);
`endif
`ifndef MYWIRE
  wire w2;
`elsif ALL
  /* nothing.  */
`else
  wire \
  w3;
`endif
  wire a, b, c;
  xor a1(a,b,c);
endmodule

`pragma protect begin_protected
`pragma none
`pragma protect end_protected
