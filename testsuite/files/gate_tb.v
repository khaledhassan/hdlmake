module gate_tb;
  reg i, o;
  gate dut(.i(i), .o(o));
  initial begin
    i <= 0;
    # 1;
    $stop;
  end
endmodule
