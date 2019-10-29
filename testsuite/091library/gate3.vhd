library sublib;

entity gate3 is
  port (i : in bit;
        o : out bit);
end gate3;

architecture behav of gate3 is
begin
  inst: entity sublib.gate 
    port map (i, o);
end behav;
