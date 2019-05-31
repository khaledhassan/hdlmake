entity mod1 is
  port (i : bit;
        o : out bit);
end mod1;

architecture arch of mod1 is
begin
  o <= i;
end arch;
