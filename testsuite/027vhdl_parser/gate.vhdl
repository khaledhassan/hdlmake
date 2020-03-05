library ieee;
use work.pkg.all;
use ieee.unsigned.all;

entity gate is
end;

architecture arch of gate is
   signal s : unsigned (3 downto 0);
   type rec is record
      a : natural;
   end record;
   component comp is
     port (a : in bit);
   end component;
   function f return natural is
   begin
     return 1;
   end f;
begin
   assert false report msg;
   inst1: entity work.ent1 port map (s);
   inst2: comp port map (s);
   inst3: component comp port map (s);
   inst4: entity work.ent1(arch) port map (s);
end arch;
