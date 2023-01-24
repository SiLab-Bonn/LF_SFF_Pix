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
 
`timescale 1ps / 1ps
 
//`default_nettype none

module LF_SFF_MIO (

    input wire FCLK_IN, 

    //full speed 
    inout wire [7:0] BUS_DATA,
    input wire [15:0] ADD,
    input wire RD_B,
    input wire WR_B,

    //high speed
    inout wire [7:0] FD,
    input wire FREAD,
    input wire FSTROBE,
    input wire FMODE,

    //debug
    output wire [15:0] DEBUG_D,
    output wire LED1,
    output wire LED2,
    output wire LED3,
    output wire LED4,
    output wire LED5,
    inout wire FPGA_BUTTON,

    inout SDA,
    inout SCL,

    output [2:0] TX,

    output wire SEL0,
    output wire SEL1,
    output wire SEL2,
    output wire SEL3,
    output wire RESET,

    //SRAM
    output wire [19:0] SRAM_A,
    inout wire [15:0] SRAM_IO,
    output wire SRAM_BHE_B,
    output wire SRAM_BLE_B,
    output wire SRAM_CE1_B,
    output wire SRAM_OE_B,
    output wire SRAM_WE_B,

    //FADC CONFIG
    output ADC_CSN,
    output ADC_SCLK,
    output ADC_SDI,
    input ADC_SD0,

    //FADC
    output ADC_ENC_P,
    output ADC_ENC_N,
    input ADC_DCO_P,
    input ADC_DCO_N,
    input ADC_FCO_P,
    input ADC_FCO_N,

    input [3:0] ADC_OUT_P,
    input [3:0] ADC_OUT_N,
    
    output CLK_ROW_25,
    output ROW_RESET_25,
    output CLK_COL_25,
    output CLK_ROW_50,
    output ROW_RESET_50,
    output ROW_SAMPLE1_50,
    output ROW_SAMPLE2_50,
    output CLK_COL_50,
    output RESET_ROW_START,
    output RESET_ROW_CNT,
    output RESET_COL_CNT,
    output RESET_COL_START_1,
    output RESET_COL_START_2,
    output CLK_COL_100,
    output CLK_ROW_100,
    output ROW_RESET_100
);   

    assign SDA = 1'bz;
    assign SCL = 1'bz;

    assign DEBUG_D = 16'ha5a5;

    wire BUS_CLK, BUS_CLK270;
    wire SPI_CLK;
    wire ADC_ENC;
    wire CLK_160_LOCKED;
    wire BUS_RST;

    assign TX[2:1] = 0;
    OFDDRRSE OFDDRRSE_ADC_ENC_BUF (
        .Q(TX[0]),      
        .C0(ADC_ENC), .C1(~ADC_ENC),  
        .CE(1'b1),    
        .D0(1'b1), .D1(1'b0),
        .R(1'b0), .S(1'b0)
    );

    reset_gen i_reset_gen(.CLK(BUS_CLK), .RST(BUS_RST));
    wire ADC_CLK;
    clk_gen i_clkgen(
         .CLKIN(FCLK_IN),
         .CLKINBUF(BUS_CLK),
         .CLKINBUF270(BUS_CLK270),
         .ADC_ENC(ADC_ENC),
         .ADC_CLK(ADC_CLK),
         .SPI_CLK(SPI_CLK),
         .LOCKED(CLK_160_LOCKED)
    );


    // -------  MODULE ADREESSES  ------- //
    localparam GPIO_BASEADDR = 16'h0000;
    localparam GPIO_HIGHADDR = 16'h000f;

    localparam SPI_ADC_BASEADDR = 16'h0010;                 // 0x0010
    localparam SPI_ADC_HIGHADDR = SPI_ADC_BASEADDR + 15;    // 0x001f
    
    localparam FIFO_BASEADDR = 16'h0020;                    // 0x0020
    localparam FIFO_HIGHADDR = FIFO_BASEADDR + 15;          // 0x002f

    localparam ADC_RX_CH0_BASEADDR = 16'h0030;                 // 0x0030
    localparam ADC_RX_CH0_HIGHADDR = ADC_RX_CH0_BASEADDR + 15; // 0x003f
    
    localparam ADC_RX_CH1_BASEADDR = ADC_RX_CH0_HIGHADDR + 1;  // 0x0040
    localparam ADC_RX_CH1_HIGHADDR = ADC_RX_CH1_BASEADDR + 15; // 0x004f
    
    localparam ADC_RX_CH2_BASEADDR = ADC_RX_CH1_HIGHADDR + 1;  // 0x0050
    localparam ADC_RX_CH2_HIGHADDR = ADC_RX_CH2_BASEADDR + 15; // 0x005f
    
    localparam ADC_RX_CH3_BASEADDR = ADC_RX_CH2_HIGHADDR + 1;  // 0x0060
    localparam ADC_RX_CH3_HIGHADDR = ADC_RX_CH3_BASEADDR + 15; // 0x006f
    
    //localparam SEQ_GEN_BASEADDR = 16'h1000;                     // 0x1000
    //localparam SEQ_GEN_HIGHADDR = SEQ_GEN_BASEADDR + 15 + 16384;// 0x500f
    

    // -------  BUS SYGNALING  ------- //
    wire [15:0] BUS_ADD;
    assign BUS_ADD = ADD - 16'h4000;
    wire BUS_RD, BUS_WR;
    assign BUS_RD = ~RD_B;
    assign BUS_WR = ~WR_B;
    
    
    // -------  USER MODULES  ------- //
    wire ADC_EN;
    spi 
    #( 
        .BASEADDR(SPI_ADC_BASEADDR), 
        .HIGHADDR(SPI_ADC_HIGHADDR), 
        .MEM_BYTES(2) 
    )  i_spi_adc
    (
        .BUS_CLK(BUS_CLK),
        .BUS_RST(BUS_RST),
        .BUS_ADD(BUS_ADD),
        .BUS_DATA(BUS_DATA),
        .BUS_RD(BUS_RD),
        .BUS_WR(BUS_WR),

        .SPI_CLK(SPI_CLK),

        .SCLK(ADC_SCLK),
        .SDI(ADC_SDI),
        .SDO(ADC_SD0),
        .SEN(ADC_EN),
        .SLD()
    );
    assign ADC_CSN = !ADC_EN;

    //wire [15:0] SEQ_OUT;
    //seq_gen 
    //#( 
    //    .BASEADDR(SEQ_GEN_BASEADDR), 
    //    .HIGHADDR(SEQ_GEN_HIGHADDR), 
    //    .MEM_BYTES(16384), 
    //    .OUT_BITS(16) 
    //) i_seq_gen
    //(
    //    .BUS_CLK(BUS_CLK),
    //    .BUS_RST(BUS_RST),
    //    .BUS_ADD(BUS_ADD),
    //    .BUS_DATA(BUS_DATA),
    //    .BUS_RD(BUS_RD),
    //    .BUS_WR(BUS_WR), 

    //    .SEQ_CLK(ADC_ENC),
    //    .SEQ_OUT(SEQ_OUT)
    //);

    wire [3:0] ADC_SYNC;
    //assign RESET_COL_START_1 = 0;
    //assign RESET_COL_START_2 = 0;
    //assign RESET_ROW_START = 0;
    
    //assign RESET_ROW_CNT = SEQ_OUT[0];
    //assign RESET_COL_CNT = SEQ_OUT[1];
    
    //assign ADC_SYNC[0] = SEQ_OUT[2];
    //assign ADC_SYNC[2] = SEQ_OUT[2];
    //assign CLK_ROW_50 = SEQ_OUT[3];
    //assign CLK_COL_50 = SEQ_OUT[4];
    //assign ROW_RESET_50 = SEQ_OUT[5];
    
    //assign ADC_SYNC[1] = SEQ_OUT[6];
    //assign CLK_ROW_25 = SEQ_OUT[7];
    //assign CLK_COL_25 = SEQ_OUT[8];
    //assign ROW_RESET_25 = SEQ_OUT[9];

    //assign ADC_SYNC[3] = SEQ_OUT[10];
    //assign CLK_ROW_100 = SEQ_OUT[11];
    //assign CLK_COL_100 = SEQ_OUT[12];
    //assign ROW_RESET_100 = SEQ_OUT[13];
    
    //assign ROW_SAMPLE1_50 = SEQ_OUT[14];
    //assign ROW_SAMPLE2_50 = SEQ_OUT[15];
    
    wire [3:0] ADC_IN;
    wire ADC_DCO, ADC_FCO;
    gpac_adc_iobuf i_gpac_adc_iobuf
    (
        .ADC_DCO_P(ADC_DCO_P), .ADC_DCO_N(ADC_DCO_N),
        .ADC_DCO(ADC_DCO),

        .ADC_FCO_P(ADC_FCO_P), .ADC_FCO_N(ADC_FCO_N),
        .ADC_FCO(ADC_FCO),

        .ADC_ENC(ADC_ENC), 
        .ADC_ENC_P(ADC_ENC_P), .ADC_ENC_N(ADC_ENC_N),

        .ADC_IN_P(ADC_OUT_P), .ADC_IN_N(ADC_OUT_N),
        .ADC_IN0(ADC_IN[0]),.ADC_IN1(ADC_IN[1]),.ADC_IN2(ADC_IN[2]),.ADC_IN3(ADC_IN[3])
    );

    wire [3:0] FIFO_EMPTY_ADC, FIFO_READ;
    wire [31:0] FIFO_DATA_ADC [3:0];
   
    wire [3:0] ADC_ERROR;
    //assign {LED2, LED3, LED4, LED5} = ADC_ERROR;
    
    genvar i;
    generate
      for (i = 0; i < 4; i = i + 1) begin: adc_gen
        gpac_adc_rx 
        #(
            .BASEADDR(ADC_RX_CH0_BASEADDR+16*i), 
            .HIGHADDR(ADC_RX_CH0_HIGHADDR+16*i),
            .ADC_ID(i), 
            .HEADER_ID(0) 
        ) i_gpac_adc_rx
        (
            /*.ADC_CLK(ADC_CLK),
            .ADC_DCO(ADC_DCO),
            .ADC_FCO(ADC_FCO),
            .ADC_IN(ADC_IN[i]),
            */
            .ADC_ENC(ADC_ENC),
            .ADC_IN(ADC_IN[i]),
            .ADC_SYNC(ADC_SYNC[i]),
            .ADC_TRIGGER(1'b0),

            .BUS_CLK(BUS_CLK),
            .BUS_RST(BUS_RST),
            .BUS_ADD(BUS_ADD),
            .BUS_DATA(BUS_DATA),
            .BUS_RD(BUS_RD),
            .BUS_WR(BUS_WR), 

            .FIFO_READ(FIFO_READ[i]),
            .FIFO_EMPTY(FIFO_EMPTY_ADC[i]),
            .FIFO_DATA(FIFO_DATA_ADC[i]),

            .LOST_ERROR(ADC_ERROR[i])
        ); 
      end
    endgenerate
    
    
    wire ARB_READY_OUT, ARB_WRITE_OUT;
    wire [31:0] ARB_DATA_OUT;
    rrp_arbiter 
    #( 
        .WIDTH(4)
        //.PRIORITY(0)
    ) i_rrp_arbiter
    (
        .RST(BUS_RST),
        .CLK(BUS_CLK),
    
        .WRITE_REQ(~FIFO_EMPTY_ADC),
        .HOLD_REQ(4'b0),
        .DATA_IN({FIFO_DATA_ADC[3],FIFO_DATA_ADC[2],FIFO_DATA_ADC[1],FIFO_DATA_ADC[0]}),
        .READ_GRANT(FIFO_READ),

        .READY_OUT(ARB_READY_OUT),
        .WRITE_OUT(ARB_WRITE_OUT),
        .DATA_OUT(ARB_DATA_OUT)
    );
    

    wire USB_READ;
    assign USB_READ = FREAD && FSTROBE;
    sram_fifo 
    #(
        .BASEADDR(FIFO_BASEADDR), 
        .HIGHADDR(FIFO_HIGHADDR)
    ) i_out_fifo (
        .BUS_CLK(BUS_CLK),
        .BUS_RST(BUS_RST),
        .BUS_ADD(BUS_ADD),
        .BUS_DATA(BUS_DATA),
        .BUS_RD(BUS_RD),
        .BUS_WR(BUS_WR), 

       // .BUS_CLK270(BUS_CLK270),
        
        .SRAM_A(SRAM_A),
        .SRAM_IO(SRAM_IO),
        .SRAM_BHE_B(SRAM_BHE_B),
        .SRAM_BLE_B(SRAM_BLE_B),
        .SRAM_CE1_B(SRAM_CE1_B),
        .SRAM_OE_B(SRAM_OE_B),
        .SRAM_WE_B(SRAM_WE_B),

        .USB_READ(USB_READ),
        .USB_DATA(FD),

        .FIFO_READ_NEXT_OUT(ARB_READY_OUT),
        .FIFO_EMPTY_IN(!ARB_WRITE_OUT),
        .FIFO_DATA(ARB_DATA_OUT),

        .FIFO_NOT_EMPTY(),
        .FIFO_READ_ERROR(),
        .FIFO_FULL()//,
        //.FIFO_NEAR_FULL(LED1)    
    ); 
    
    `ifdef SYNTHESIS_NOT
    wire [35:0] control_bus;
    chipscope_icon ichipscope_icon
    (
        .CONTROL0(control_bus)
    ); 

    chipscope_ila ichipscope_ila 
    (
        .CONTROL(control_bus),
        .CLK(ADC_CLK), 
        .TRIG0({adc_1_data, ADC_OUT1, ADC_ENC, adc_load, ADC_OUT1, ADC_FCO})//, ADC_SD0, ADC_SDI, ADC_SCLK, ADC_EN}) 

    ); 
    `endif
	 


	wire [1:0] GPIO_NOT_USED;
    gpio #(
        .BASEADDR(GPIO_BASEADDR),
        .HIGHADDR(GPIO_HIGHADDR),

        .IO_WIDTH(8),
        .IO_DIRECTION(8'h1f) // 3 MSBs are input the rest output
    ) i_gpio (
        .BUS_CLK(BUS_CLK),
        .BUS_RST(BUS_RST),
        .BUS_ADD(BUS_ADD),
        .BUS_DATA(BUS_DATA),
        .BUS_RD(BUS_RD),
        .BUS_WR(BUS_WR),
        .IO({SEL2, SEL1, SEL0, RESET, LED4, LED3, LED2, LED1}) //,FPGA_BUTTON, GPIO_NOT_USED, LED5, LED4, LED3, LED2, LED1
    );

    assign GPIO_NOT_USED = {LED2, LED1};

endmodule
