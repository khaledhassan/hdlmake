library ieee;
use ieee.std_logic_1164.all;

library testlib;
context testlib.testlib_context;

entity test_top is
  
  port (
    int_out : out integer);

end entity test_top;

architecture behav of test_top is

begin  -- architecture behav

  int_out <= C_TEST_INT;

end architecture behav;
