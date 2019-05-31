entity gate is
  port (o : out bit;
        i : in bit);
end gate;

architecture behav of gate is
begin
  o <= not i;
end behav;
