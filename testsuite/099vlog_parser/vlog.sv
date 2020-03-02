module gate1(input a);
endmodule

module gate(input a);
endmodule

module gate2(input a);
   gate1 g(a);
endmodule
