entity sub is
  port (s: bit);
end sub;

architecture rtl of sub is
begin
  inst: entity work.top
    port map(s => s);
end rtl;
