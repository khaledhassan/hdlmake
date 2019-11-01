entity top is
  port (s : bit);
end top;

architecture rtl of top is
begin
  inst: entity work.sub
    port map(s => s);
end rtl;
