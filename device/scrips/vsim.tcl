
vlib work
set XILINX   $env(XILINX)

#vmap unisims_ver $XILINX/verilog/questasim/10.1c/lin64/unisims_ver
#vmap simprims_ver $XILINX/verilog/questasim/10.1c/lin64/simprims_ver
 
vlog $XILINX/verilog/src/glbl.v

vlog -lint ../../../../basil/trunk/device/modules/utils/*.v
vlog -lint ../../../../basil/trunk/device/modules/spi/*.v
vlog -lint ../../../../basil/trunk/device/modules/gpac_adc_rx/*.v
vlog -lint ../../../../basil/trunk/device/modules/sram_fifo/*.v

vlog -lint ../../../../basil/trunk/device/modules/rrp_arbiter/*.v +incdir+../../../../basil/trunk/device/modules/rrp_arbiter

vlog -lint ../../../../basil/trunk/device/modules/seq_gen/*.v +incdir+../../../../basil/trunk/device/modules/seq_gen
vlog -lint ../../../../basil/trunk/device/modules/seq_gen/seq_gen_blk_mem_16x8196.v
#vlog -lint ../../../../basil/trunk/device/modules/seq_gen/seq_gen_blk_mem_8x2048.v

vlog -lint ../src/*.v +incdir+../../../../basil/trunk/device/
vlog ../tb/tb.sv +incdir+../../../../basil/trunk/device/modules/tb

proc vsim_top {} {
    vsim -novopt -t 1ps -L unisims_ver -L simprims_ver work.tb glbl
}

proc wave_top {} {
    
    add wave -group tb sim:/tb/*
    add wave -group uut sim:/tb/uut/*
    add wave -group clk_gen sim:/tb/uut/i_clkgen/*
    add wave -group spi sim:/tb/uut/i_spi_adc/i_spi_adc_core/*
    add wave -group gpac_adc_rx sim:/tb/uut/adc_gen\[0\]/i_gpac_adc_rx/i_gpac_adc_core/*
    #add wave -group gpac_adc_rx_fifo sim:/tb/uut/igpac_adc_rx_0/cdc_syncfifo_i/*
    add wave -group out_fifo sim:/tb/uut/i_out_fifo/i_out_fifo_core/*
    add wave -group seq_gen sim:/tb/uut/i_seq_gen/i_seq_gen_core/*
    add wave -group rrp_arbiter sim:/tb/uut/irrp_arbiter/*
    
}
