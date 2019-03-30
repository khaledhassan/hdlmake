//-----------------------------------------------------
// Design      : Simple 8-bit verilog counter
// Author      : Javier D. Garcia-Lasheras
//-----------------------------------------------------

module counter  (
    clock,
    clear,
    count,
    Q
);

//--------- Cycles per second -------------------------
    parameter cycles_per_second = 12000000;

//--------- Output Ports ------------------------------
    output [7:0] Q;

//--------- Input Ports -------------------------------
    input clock, clear, count;

//--------- Internal Variables ------------------------
    reg [23:0] divider;
    reg [7:0] Q;

//--------- Code Starts Here --------------------------

    always @(posedge clock) begin
       if (clear)
         begin
           Q <= 0;
           divider <= 0;
         end
       else
         begin
           if (count)
             begin
               if (divider == cycles_per_second)
                 begin
                   divider <= 0;
                   Q <= Q + 1;
                 end
               else
                 begin
                   divider <= divider + 1;
                   Q <= Q;
                 end
             end
         end
    end


endmodule 
