/**
 * ------------------------------------------------------------
 * Copyright (c) SILAB , Physics Institute of Bonn University 
 * ------------------------------------------------------------
 *
 * SVN revision information:
 *  $Rev:: 4                     $:
 *  $Author:: themperek          $: 
 *  $Date:: 2013-09-12 12:20:16 #$:
 */
 
`timescale 1ns / 1ps

module clk_gen(
    input CLKIN,
    output CLKINBUF,
    output CLKINBUF270,
    
    output ADC_ENC,
    output ADC_CLK,
    output SPI_CLK,
    output LOCKED
    );

    wire CLK2_FX_BUF;
    wire GND_BIT;
    assign GND_BIT = 0;
    wire CLKD5MHZ;
    wire CLKFX_BUF, CLKOUTFX, CLKDV, CLKDV_BUF;
    wire CLK0_BUF;
    wire CLKFX_40FB;
    
    assign ADC_ENC = CLKD5MHZ;
    assign ADC_CLK = CLK2_FX_BUF;
    wire CLK270_BUF;
    BUFG CLKFX_BUFG_INST (.I(CLKFX_BUF), .O(CLKOUTFX)); 
    BUFG CLKFB_BUFG_INST (.I(CLK0_BUF), .O(CLKINBUF));
    BUFG CLK90_BUFG_INST (.I(CLK270_BUF), .O(CLKINBUF270));
    BUFG CLKDV_BUFG_INST (.I(CLKDV), .O(CLKDV_BUF));
    assign SPI_CLK = CLKDV_BUF;
    //assign SPI_CLK = CLKINBUF;
   
    wire CLKFX_40;
   
   DCM #(
         .CLKDV_DIVIDE(4), // Divide by: 1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5
         // 7.0,7.5,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0 or 16.0
         .CLKFX_DIVIDE(6), // Can be any Integer from 1 to 32
         .CLKFX_MULTIPLY(5), // Can be any Integer from 2 to 32
         .CLKIN_DIVIDE_BY_2("FALSE"), // TRUE/FALSE to enable CLKIN divide by two feature
         .CLKIN_PERIOD(20.833), // Specify period of input clock
         .CLKOUT_PHASE_SHIFT("NONE"), // Specify phase shift of NONE, FIXED or VARIABLE
         .CLK_FEEDBACK("1X"), // Specify clock feedback of NONE, 1X or 2X
         .DESKEW_ADJUST("SYSTEM_SYNCHRONOUS"), // SOURCE_SYNCHRONOUS, SYSTEM_SYNCHRONOUS or
         // an Integer from 0 to 15
         .DFS_FREQUENCY_MODE("LOW"), // HIGH or LOW frequency mode for frequency synthesis
         .DLL_FREQUENCY_MODE("LOW"), // HIGH or LOW frequency mode for DLL
         .DUTY_CYCLE_CORRECTION("TRUE"), // Duty cycle correction, TRUE or FALSE
         .FACTORY_JF(16'hC080), // FACTORY JF values
         .PHASE_SHIFT(0), // Amount of fixed phase shift from -255 to 255
         .STARTUP_WAIT("TRUE") // Delay configuration DONE until DCM_SP LOCK, TRUE/FALSE
         ) DCM_BUS (
         .CLKFB(CLKINBUF), 
         .CLKIN(CLKIN), 
         .DSSEN(GND_BIT), 
         .PSCLK(GND_BIT), 
         .PSEN(GND_BIT), 
         .PSINCDEC(GND_BIT), 
         .RST(GND_BIT),
         .CLKDV(CLKDV),
         .CLKFX(CLKFX_40), 
         .CLKFX180(), 
         .CLK0(CLK0_BUF), 
         .CLK2X(), 
         .CLK2X180(), 
         .CLK90(), 
         .CLK180(), 
         .CLK270(CLK270_BUF), 
         .LOCKED(LOCKED), 
         .PSDONE(), 
         .STATUS());
  
   wire CLKOUT40, CLKDV_5;
   wire CLK2_0, CLK2_FX;
   BUFG CLKFX_2_BUFG_INST (.I(CLKFX_40), .O(CLKOUT40));
   BUFG CLKDV_2_BUFG_INST (.I(CLKDV_5), .O(CLKD5MHZ));
   BUFG CLKFB_2_BUFG_INST (.I(CLK2_0), .O(CLKFX_40FB));
   BUFG CLKFX2_2_BUFG_INST (.I(CLK2_FX), .O(CLK2_FX_BUF));
     
   DCM #(
         .CLKDV_DIVIDE(8.0), // Divide by: 1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5
         // 7.0,7.5,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0 or 16.0
         .CLKFX_DIVIDE(1), // Can be any Integer from 1 to 32
         .CLKFX_MULTIPLY(2), // Can be any Integer from 2 to 32
         .CLKIN_DIVIDE_BY_2("FALSE"), // TRUE/FALSE to enable CLKIN divide by two feature
         .CLKIN_PERIOD(25.0), // Specify period of input clock
         .CLKOUT_PHASE_SHIFT("NONE"), // Specify phase shift of NONE, FIXED or VARIABLE
         .CLK_FEEDBACK("1X"), // Specify clock feedback of NONE, 1X or 2X
         .DESKEW_ADJUST("SYSTEM_SYNCHRONOUS"), // SOURCE_SYNCHRONOUS, SYSTEM_SYNCHRONOUS or
         // an Integer from 0 to 15
         .DFS_FREQUENCY_MODE("LOW"), // HIGH or LOW frequency mode for frequency synthesis
         .DLL_FREQUENCY_MODE("LOW"), // HIGH or LOW frequency mode for DLL
         .DUTY_CYCLE_CORRECTION("TRUE"), // Duty cycle correction, TRUE or FALSE
         .FACTORY_JF(16'hC080), // FACTORY JF values
         .PHASE_SHIFT(0), // Amount of fixed phase shift from -255 to 255
         .STARTUP_WAIT("TRUE") // Delay configuration DONE until DCM_SP LOCK, TRUE/FALSE
     ) DCM_CMD (
         .DSSEN(GND_BIT), 
         .CLK0(CLK2_0), // 0 degree DCM_SP CLK output
         .CLK180(), // 180 degree DCM_SP CLK output
         .CLK270(), // 270 degree DCM_SP CLK output
         .CLK2X(), // 2X DCM_SP CLK output
         .CLK2X180(), // 2X, 180 degree DCM_SP CLK out
         .CLK90(), // 90 degree DCM_SP CLK output
         .CLKDV(CLKDV_5), // Divided DCM_SP CLK out (CLKDV_DIVIDE)
         .CLKFX(CLK2_FX), // DCM_SP CLK synthesis out (M/D)
         .CLKFX180(), // 180 degree CLK synthesis out
         .LOCKED(), // DCM_SP LOCK status output
         .PSDONE(), // Dynamic phase adjust done output
         .STATUS(), // 8-bit DCM_SP status bits output
         .CLKFB(CLKFX_40FB), // DCM_SP clock feedback
         .CLKIN(CLKOUT40), // Clock input (from IBUFG, BUFG or DCM_SP)
         .PSCLK(GND_BIT), // Dynamic phase adjust clock input
         .PSEN(GND_BIT), // Dynamic phase adjust enable input
         .PSINCDEC(GND_BIT), // Dynamic phase adjust increment/decrement
         .RST(GND_BIT)// // DCM_SP asynchronous reset input
     );

     
     
endmodule
