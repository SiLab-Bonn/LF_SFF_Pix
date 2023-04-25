/**
 * ------------------------------------------------------------
 * Copyright (c) All rights reserved 
 * SiLab , Physics Institute of Bonn University , All Right 
 * ------------------------------------------------------------
 */
module LF_SFF_MIO(
    
    input wire FCLK_IN, // 48MHz
    
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
    input  ADC_SD0,

    output ADC_ENC_P,
    output ADC_ENC_N,
    input  ADC_DCO_P,
    input  ADC_DCO_N,
    input  ADC_FCO_P,
    input  ADC_FCO_N,

    input [3:0] ADC_OUT_P,
    input [3:0] ADC_OUT_N,
     
    // Triggers
    input wire [2:0] LEMO_RX,
    output wire [2:0] TX, // TX[0] == RJ45 trigger clock output, TX[1] == RJ45 busy output
    input wire RJ45_RESET,
    input wire RJ45_TRIGGER,
     
    // I2C
    inout SDA,
    inout SCL,

    //debug
	output wire LED1,
    output wire LED2,
    output wire LED3,
    output wire LED4,
    output wire LED5,

    output wire SEL0,
    output wire SEL1,
    output wire SEL2,
    output wire SEL3,
    output wire RESET
);


// assignments for SCC_HVCMOS2FE-I4B_V1.0 and SCC_HVCMOS2FE-I4B_V1.1
// CCPD

// Assignments
wire BUS_RST;
(* KEEP = "{TRUE}" *)
wire BUS_CLK;
(* KEEP = "{TRUE}" *)
wire CLK_40;
wire DATA_CLK;
wire RX_CLK;
wire RX_CLK2X;
wire CLK_LOCKED;
wire ADC_ENC;
wire ADC_SEL;
wire SPI_CLK;
wire ADC_CLK;
wire GPIO_RESET;

// ------- RESET/CLOCK  ------- //
reset_gen ireset_gen(.CLK(BUS_CLK), .RST(BUS_RST));

clk_gen i_clkgen(
	 .CLKIN(FCLK_IN),   
	 .BUS_CLK(BUS_CLK),   // 48 MHz
	 .ADC_ENC(ADC_ENC),   // 10 MHz
	 .ADC_CLK(ADC_CLK),   // 160 MHz
	 .SPI_CLK(SPI_CLK),   //   3 MHz
	 .LOCKED()
);

// -------  MODULE ADREESSES  ------- //
localparam FIFO_BASEADDR = 16'h8100;
localparam FIFO_HIGHADDR = 16'h8200-1;

localparam GPIO_RX_BASEADDR = 16'h8800;
localparam GPIO_RX_HIGHADDR = 16'h883F;

//ADC
localparam ADC_SPI_BASEADDR = 16'h8840;                 // 0x8840
localparam ADC_SPI_HIGHADDR = ADC_SPI_BASEADDR + 47;    // 0x886f

localparam ADC_RX_CH0_BASEADDR = 16'h8280;   
localparam ADC_RX_CH0_HIGHADDR = ADC_RX_CH0_BASEADDR + 31; // 
localparam ADC_RX_CH1_BASEADDR = 16'h82A0; 
localparam ADC_RX_CH1_HIGHADDR = ADC_RX_CH1_BASEADDR + 31; // 
localparam ADC_RX_CH2_BASEADDR = 16'h82C0;
localparam ADC_RX_CH2_HIGHADDR = ADC_RX_CH2_BASEADDR + 31; //
localparam ADC_RX_CH3_BASEADDR = 16'h82E0; 
localparam ADC_RX_CH3_HIGHADDR = ADC_RX_CH3_BASEADDR + 31; //

localparam GPIO_TH_BASEADDR = 16'h8890;
localparam GPIO_TH_HIGHADDR = 16'h88bf;

localparam GPIO_BASEADDR = 16'h0000;
localparam GPIO_HIGHADDR = 16'h000f;

localparam SEQ_GEN_BASEADDR = 16'h1000;                     // 0x1000
localparam SEQ_GEN_HIGHADDR = SEQ_GEN_BASEADDR + 15 + 16384;// 0x500f

// -------  BUS SYGNALING  ------- //
wire [15:0] BUS_ADD;
wire BUS_RD, BUS_WR;
fx2_to_bus i_fx2_to_bus (
    .ADD(ADD),
    .RD_B(RD_B),
    .WR_B(WR_B),

    .BUS_CLK(BUS_CLK),
    .BUS_ADD(BUS_ADD),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR)
);

// -------  USER MODULES  ------- //
wire FIFO_NOT_EMPTY; // raised, when SRAM FIFO is not empty
wire FIFO_FULL, FIFO_NEAR_FULL; // raised, when SRAM FIFO is full / near full
wire FIFO_READ_ERROR; // raised, when attempting to read from SRAM FIFO when it is empty

// ADC
wire ADC_EN;

spi 
#( 
	.BASEADDR(ADC_SPI_BASEADDR), 
	.HIGHADDR(ADC_SPI_HIGHADDR), 
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
	 
	 .EXT_START(1'b0),

	 .SCLK(ADC_SCLK),
   .SDI(ADC_SDI),
   .SDO(ADC_SD0),
   .SEN(ADC_EN),
   .SLD()
);

assign ADC_CSN = !ADC_EN;
wire [13:0] ADC_IN [3:0];
wire ADC_DCO, ADC_FCO;
gpac_adc_iobuf i_gpac_adc_iobuf
(
	.ADC_CLK(ADC_CLK),
	  
	.ADC_DCO_P(ADC_DCO_P), .ADC_DCO_N(ADC_DCO_N),
	.ADC_DCO(ADC_DCO),

	.ADC_FCO_P(ADC_FCO_P), .ADC_FCO_N(ADC_FCO_N),
	.ADC_FCO(ADC_FCO),

	.ADC_ENC(ADC_ENC), 
	.ADC_ENC_P(ADC_ENC_P), .ADC_ENC_N(ADC_ENC_N),

	.ADC_IN_P(ADC_OUT_P), .ADC_IN_N(ADC_OUT_N),
	
	.ADC_IN0(ADC_IN[0]), 
	.ADC_IN1(ADC_IN[1]), 
	.ADC_IN2(ADC_IN[2]), 
	.ADC_IN3(ADC_IN[3])
);


wire [31:0] FIFO_DATA_ADC [3:0];
wire [3:0]  FIFO_EMPTY_ADC;
wire [3:0]  FIFO_READ_ADC;
wire [3:0]  ADC_ERROR;
wire ADC_TRIGGER;
wire [3:0] ADC_SYNC;

genvar i;
generate
for (i = 0; i < 4; i = i + 1) begin: adc_gen
	gpac_adc_rx 
	#(
		.BASEADDR(ADC_RX_CH0_BASEADDR+32*i), 
		.HIGHADDR(ADC_RX_CH0_HIGHADDR+32*i),
		.ADC_ID(i), 
		.HEADER_ID(1'b1) 
	) i_gpac_adc_rx
	(
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
			
		.FIFO_READ(FIFO_READ_ADC[i]),
		.FIFO_EMPTY(FIFO_EMPTY_ADC[i]),
		.FIFO_DATA(FIFO_DATA_ADC[i]),

		.LOST_ERROR(ADC_ERROR[i])
	);
  end
	endgenerate
        
// Arbiter
wire ARB_READY_OUT, ARB_WRITE_OUT;
wire [31:0] ARB_DATA_OUT;
rrp_arbiter 
#( 
    .WIDTH(4)
) i_rrp_arbiter
(
    .RST(BUS_RST),
    .CLK(BUS_CLK),

    .WRITE_REQ({~FIFO_EMPTY_ADC[3],~FIFO_EMPTY_ADC[2],~FIFO_EMPTY_ADC[1],
                ~FIFO_EMPTY_ADC[0]}),
    .HOLD_REQ(4'b0),
    .DATA_IN({FIFO_DATA_ADC[3],FIFO_DATA_ADC[2],FIFO_DATA_ADC[1],FIFO_DATA_ADC[0]}),
    .READ_GRANT(FIFO_READ_ADC),

    .READY_OUT(ARB_READY_OUT),
    .WRITE_OUT(ARB_WRITE_OUT),
    .DATA_OUT(ARB_DATA_OUT)
);

// SRAM
wire USB_READ;
assign USB_READ = FREAD & FSTROBE;

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

    .FIFO_NOT_EMPTY(FIFO_NOT_EMPTY),
    .FIFO_FULL(FIFO_FULL),
    .FIFO_NEAR_FULL(FIFO_NEAR_FULL),
    .FIFO_READ_ERROR(FIFO_READ_ERROR)
);

wire [15:0] SEQ_OUT;
seq_gen 
#( 
    .BASEADDR(SEQ_GEN_BASEADDR), 
    .HIGHADDR(SEQ_GEN_HIGHADDR), 
    .MEM_BYTES(16384), 
    .OUT_BITS(16) 
) i_seq_gen
(
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR), 

    .SEQ_CLK(ADC_ENC),
    .SEQ_OUT(SEQ_OUT)
);
wire [1:0] GPIO_NOT_USED;
gpio #(
    .BASEADDR(GPIO_BASEADDR),
    .HIGHADDR(GPIO_HIGHADDR),

    .IO_WIDTH(5),
    .IO_DIRECTION(5'h1f) // 3 MSBs are input the rest output
) i_gpio (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    .IO({LED5, SEL2, SEL1, SEL0, GPIO_RESET}) //,FPGA_BUTTON, GPIO_NOT_USED, LED5, LED4, LED3, LED2, LED1
);
assign RESET = (SEQ_OUT[0] == 1'b1) ? SEQ_OUT[0] : GPIO_RESET;
assign GPIO_NOT_USED = {LED2, LED1};
assign LED1 = SEL0;
assign LED2 = SEL1;
assign LED3 = SEL2;
assign LED4 = RESET;
assign TX[0] = SEQ_OUT[0];
assign TX[1] = SEQ_OUT[1];
assign TX[2] = SEQ_OUT[3];

endmodule
