module gate3_tb;
  reg i, o;
  gate3 dut(.i(i), .o(o));
  initial begin
    i <= 0;
    # 1;
    $stop;
  end
endmodule
