module gatesv_tb;
  reg i, o;
  wire o2;
  gate dut(.i(i), .o(o));
  gate2 dut(.i(i), .o(o2));
  initial begin
    i <= 0;
    # 1;
    $stop;
  end
endmodule
