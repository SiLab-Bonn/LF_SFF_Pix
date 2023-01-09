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

`include "silbusb.sv"

`define ADC_SPI_BASE_ADD 16'h0000
`define ADC_SPI_START `ADC_SPI_BASE_ADD+1
`define ADC_SPI_CLKDIV `ADC_SPI_BASE_ADD+2
`define ADC_SPI_DATA_OUT `ADC_SPI_BASE_ADD+8
`define ADC_SPI_DATA_IN `ADC_SPI_BASE_ADD+10

`define ADC_RX_BASE_ADD 16'h0030
`define ADC_RX_RESET `ADC_RX_BASE_ADD+0
`define ADC_RX_START `ADC_RX_BASE_ADD+1

`define FIFO_BASE_ADD 16'h0020
`define FIFO_BASE_SIZE `FIFO_BASE_ADD+1

`define SEQ_GEN_BASE_ADD 16'h1000
`define SEQ_GEN_START `SEQ_GEN_BASE_ADD+1
`define SEQ_GEN_CLKDIV `SEQ_GEN_BASE_ADD+2
`define SEQ_GEN_SIZE1 `SEQ_GEN_BASE_ADD+3
`define SEQ_GEN_SIZE0 `SEQ_GEN_BASE_ADD+4
`define SEQ_GEN_REPEAT `SEQ_GEN_BASE_ADD+7
`define SEQ_GEN_REP_START1 `SEQ_GEN_BASE_ADD+8
`define SEQ_GEN_REP_START0 `SEQ_GEN_BASE_ADD+9
`define SEQ_GEN_DATA_OUT `SEQ_GEN_BASE_ADD+16

module tb;

    // Inputs
    reg FCLK_IN;
    wire FE_RX;
    
    // Outputs
    wire [15:0] DEBUG_D;
    wire LED1;
    wire LED2;
    wire LED3;
    wire LED4;
    wire LED5;
    wire [19:0] SRAM_A;
    wire SRAM_BHE_B;
    wire SRAM_BLE_B;
    wire SRAM_CE1_B;
    wire SRAM_OE_B;
    wire SRAM_WE_B;

    // Bidirs
    wire [15:0] SRAM_IO;

    wire ADC_CSN, ADC_SCLK, ADC_SPI;
    reg ADC_SD0;
    
    wire ADC_ENC_P, ADC_ENC_N;
    logic ADC_DATA;
    
    SiLibUSB sidev(FCLK_IN);
    
    // Instantiate the Unit Under Test (UUT)
    xtb01 uut (
        .FCLK_IN(FCLK_IN), 
        
        .BUS_DATA(sidev.DATA), 
        .ADD(sidev.ADD), 
        .RD_B(sidev.RD_B), 
        .WR_B(sidev.WR_B), 
        .FD(sidev.FD), 
        .FREAD(sidev.FREAD), 
        .FSTROBE(sidev.FSTROBE), 
        .FMODE(sidev.FMODE),
        
        .DEBUG_D(DEBUG_D), 
        .LED1(LED1), 
        .LED2(LED2), 
        .LED3(LED3), 
        .LED4(LED4), 
        .LED5(LED5), 
        
        .SRAM_A(SRAM_A), 
        .SRAM_IO(SRAM_IO), 
        .SRAM_BHE_B(SRAM_BHE_B), 
        .SRAM_BLE_B(SRAM_BLE_B), 
        .SRAM_CE1_B(SRAM_CE1_B), 
        .SRAM_OE_B(SRAM_OE_B), 
        .SRAM_WE_B(SRAM_WE_B),
        
        .ADC_CSN(ADC_CSN),
        .ADC_SCLK(ADC_SCLK),
        .ADC_SDI(ADC_SPI),
        .ADC_SD0(ADC_SD0),
        
        .ADC_ENC_P(ADC_ENC_P),
        .ADC_ENC_N(ADC_ENC_N),
    
        .ADC_FCO_P(ADC_ENC_P),
        .ADC_FCO_N(ADC_ENC_N),
        
        .ADC_OUT_P({4{ADC_DATA}}),
        .ADC_OUT_N({4{!ADC_DATA}})
        
    );
   

    /// SRAM
    reg [15:0] sram [1048576-1:0];
    always@(posedge SRAM_WE_B)
        sram[SRAM_A] <= SRAM_IO;
    
    assign SRAM_IO = !SRAM_OE_B ? sram[SRAM_A] : 16'hzzzz;
    
    //// SPI
    always@(negedge ADC_SCLK or posedge ADC_CSN)
        if(ADC_CSN)
            ADC_SD0 <= 1;
        else
            ADC_SD0 <= !ADC_SD0;
            
    
    logic [13:0] cnt; 
    initial cnt = 0;
    always@(posedge ADC_ENC_P)
        cnt <= cnt +1;
    
    initial ADC_DATA = 0;
    always@(negedge uut.ADC_CLK)
        ADC_DATA <= !ADC_DATA;
    
    initial begin
            FCLK_IN = 0;
            forever
                #(20.833/2) FCLK_IN =!FCLK_IN;
    end
    
    reg [15:0]  data ;
    integer sram_fifo_size;
    integer bytes_to_read;
    bit [31:0] sram_data;
    
    initial begin
        repeat (300) @(posedge FCLK_IN);
        
        /*
        //TEST ADC_SPI
        sidev.WriteExternal( `ADC_SPI_BASE_ADD,  0); 
        repeat (20) @(posedge FCLK_IN);
        sidev.WriteExternal( `ADC_SPI_DATA_OUT,  8'h80); 
        sidev.WriteExternal( `ADC_SPI_DATA_OUT+1,  8'hff);
        
        sidev.WriteExternal( `ADC_SPI_START,  0); 
        
        repeat (1000) @(posedge FCLK_IN);
        sidev.ReadExternal( `ADC_SPI_DATA_IN, data[15:8]);
        sidev.ReadExternal( `ADC_SPI_DATA_IN+1, data[7:0]);
        $display (" Data from ADCSPI %h",  data ); 
        
        //sidev.FastBlockRead(data[7:0]);
        
        
        #400us
        sram_fifo_size = 0;
        sidev.ReadExternal( `FIFO_BASE_SIZE,  sram_fifo_size[23:16]); 
        sidev.ReadExternal( `FIFO_BASE_SIZE+1,  sram_fifo_size[15:8]);
        sidev.ReadExternal( `FIFO_BASE_SIZE+2,  sram_fifo_size[7:0]);
        $display (" SRAM FIFO Size %d",  sram_fifo_size ); 
        bytes_to_read = sram_fifo_size *2; // sram data bus is 16bit = 2 bytes 
        
        //Read with fast usb always 4 bytes
        for(int i=0;i<bytes_to_read/4;i++) begin
            sidev.FastBlockRead(sram_data[31:24]);
            sidev.FastBlockRead(sram_data[23:16]); 
            sidev.FastBlockRead(sram_data[15:8]);
            sidev.FastBlockRead(sram_data[7:0]);
            $display (" SRAM DATA [%d]: %h",  i, sram_data ); 
        end
        */
        
        // SEQ_GEN 
        
        sidev.WriteExternal( `SEQ_GEN_BASE_ADD,  0); 
        repeat (20) @(posedge FCLK_IN);
        
        /*
      
        sidev.WriteExternal( `SEQ_GEN_CLKDIV,  8); 
        sidev.WriteExternal( `SEQ_GEN_REPEAT,  2); 
        
        sidev.WriteExternal( `SEQ_GEN_SIZE1,  0 );
        sidev.WriteExternal( `SEQ_GEN_SIZE0, 16 );
        
        sidev.WriteExternal( `SEQ_GEN_REP_START1,  0 );
        sidev.WriteExternal( `SEQ_GEN_REP_START0,  1 );
        
        for(int i=0;i<34;i++)
            sidev.WriteExternal( `SEQ_GEN_DATA_OUT+i,  i+1 ); 

        sidev.WriteExternal( `SEQ_GEN_START, 0);
        */
        
        sidev.WriteExternal( `SEQ_GEN_CLKDIV,  8); 
        sidev.WriteExternal( `SEQ_GEN_SIZE1,  0 );
        sidev.WriteExternal( `SEQ_GEN_SIZE0, 128 );
        sidev.WriteExternal( `SEQ_GEN_DATA_OUT+1,  8'h01 ); 
        sidev.WriteExternal( `SEQ_GEN_START, 0);
        
        repeat (200) @(posedge FCLK_IN);
        
        sidev.WriteExternal( `ADC_RX_BASE_ADD+1, 0);
        
        
    end

endmodule

