To use this project you are requiered to:
1. Clone this [fork of basil](https://github.com/dschuechter/basil) that supports spartan 3 FPGAs (e.g. in the parent directory next to the [LF_SFF_Pix](https://github.com/SiLab-Bonn/LF_SFF_Pix) repository)
2. Open the ise project and manually link the firmware dependencies to the cloned repository by right clicking on the :question: objects and "Add Source..."
3. You might have to change the relative file path ```include "../../../git/basil/basil/firmware/modules/includes/log2func.v"``` in multiple files to your relative file path (ISE will let you know which files are affected)
4. Select the the top module (LF_SFF_MIO) and synthesize it by pressing :arrow_forward:
5. The output files can be found in ```work/work/```

Modify the firmware to your needs. The fork of basil is required, because some newly introduced features of [basil](https://github.com/SiLab-Bonn/basil) are not compatible with the old spartan3 on the MultiIO Board 1.04. For this setup specifically was the hardware revision HK 02/2011 used.

This MultiIO board utilizes the functionality of the GAPC Rev1.0a board from 07/2013 and the LF SFF AC/DC Rev.1.0 board of which you can find the source files in [this repository](https://github.com/SiLab-Bonn/LF_SFF_Pix/tree/main/pcb).
