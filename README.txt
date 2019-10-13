To install and use the assembler:

1)  First install Python (version 3) from the website python.org. Make sure that the installer
    updates your Path environment variable so that it will include the folder where python is 
    installed.

2)  The Assembler consists of a top-level script named sbasm.py, and a subfolder named Assembler
    that contains the main Assembler.py code. Install the sbasm.py file and the Assembler subfolder
    into a folder of your choice on your computer.

3)  On your computer make a new environment variable called PYTHONPATH (in Windows 10 you can 
    edit environment variables by using 

    Control Panel | User Accounts | Change my environment variables).

    Python uses the value of this environment variable to locate user-libraries. Set the PYTHONPATH
    environment variable to the full path of the Assembler subfolder. This setting allows the 
    python code in sbasm.py to import the code in the Assembler subfolder.

    For example, assume that the Python script sbasm.py is stored in the folder C:\Python_scripts.
    This means that the Assembler itself, which is made up of the two files Assembler.py and 
    ErrorCodes.py, is stored in the folder called C:\Python_scripts\Assembler.

    Then, you would set PYTHONPATH to: PYTHONPATH = C:\Python_scripts\Assembler

    Finally, you need to add the path C:\Python_scripts to your Path environment variable. This
    setting will allow your operating system to find the sbasm.py script whenever you wish to run 
    the assembler.

    This completes the installation process!

    Now, in a Command prompt window you can navigate to a folder that has your assembly-language
    code, such as file.s, and then assemble it by typing

   sbasm.py file.s file.mif

    By default, the Windows OS associates any file *.py with the python executable program.
    Thus, Windows will automatically execute the command "python sbasm.py file.s file.mif". 
    Windows uses your Path environment variable to find sbasm.py and the Python program uses 
    the PYTHONPATH environment variable to find Assembler.py.

*****************************************************************************************
Notes
-----

1) Assembly Language File Format

    The input file line numbers start indexing at line number 1 (for error messages). Blank 
    lines are ignored.

    // is used for comments, the assembler will ignore everything afer the //
    
    Supported instructions are:

    mv rX, rY      rX <- rY
    mv rX, #D      rX <- 0000000DDDDDDDDD
    mvt rX, #D     rX <- DDDDDDDD00000000
    add rX, rY     rX <- rX + rY
    add rX, #D     rX <- rX + 0000000DDDDDDDDD
    sub rX, rY     rX <- rX - rY
    sub rX, #D     rX <- rX - 0000000DDDDDDDDD
    ld rX, [rY]    rX <- contents of memory at address rY
    st rX, [rY]    contents of memory at address rY <- rX
    and rX, rY     rX <- rX & rY
    and rX, #D     rX <- rX & 0000000DDDDDDDDD
    b{cond} #D     pc <- 0000000DDDDDDDDD iff cond == True

   rX and rY can be registers r0, r1, ..., r7. Register r7 can also be called pc

2)  Running the program:
    The program expects 2 arguments in particular order:
        The input file name (the file with the assembly code written).
        The output file name (the file where the MIF is produced).
    
    Example:
        sbasm.py input_file.s output_file.mif
        sbasm.py input_file.s                        // produces output file a.mif

4)  Bitwidth

    The Assembler supports a bit widths of 16

    The Assembler supports different memory depths. The default is 256 words, but can 
    be changed by including in your assembly-language program the line

    DEPTH = x   (only integer multiples of 2 supported)

    Each machine code instruction by the Assembler has the format:
    
    15              0
     III0XXX000000YYY
     or
     III1XXXDDDDDDDDD

    Where III specifies the instruction, XXX is rX, YYY is rY, and DDDDDDDDD is
    #D. For mvt the immediate is 0DDDDDDDD. For b{cond} XXX is the condition

5)  Instruction Encoding
    mv:        III = 000 M
    mvt:       III = 001 1
    add:       III = 010 M
    sub:       III = 011 M
    ld:        III = 100 0
    st:        III = 101 0
    and:       III = 110 M
    b{cond}:   III = 111 1, where cond are none (000), eq (001), ne (010), cc (011), cs (100)

    M = 0 when using rY, 1 when using immediate data #D
    
6) Labels and Assembler Directives

    Any line of assembly-language code can include a label, which can use the 
    characters a-z, A-Z, 0-9, _, or $. As example of a label being used is:

    MAIN:     mv     r0, #0                // initialize counter
                ...
                ...
              b       #MAIN

    The Assembler supports two directives: .define and .word.

    The .define directive is used to associate a symbolic name with a constant.
    For example, if your assembly-language code includes the line

    .define STACK 256            // bottom of memory

    Then your program could use this symbolic name STACK in an instruction such as

    mv     r6, #STACK            // stack pointer

    The default number base is 10, as used for STACK above. Other examples are

    .define SW_ADDRESS 0x3000         // hexadecimal
    .define HEX_ADDRESS 0x2000        // hexadecimal
    .define LED_ADDRESS 0x1000        // hexadecimal
    .define PATTERN 0b00111111        // binary

    The .word directive is used to place data into memory, normally at the end of an 
    assembly-language source-code file. For example, if your assembly-language code 
    includes the lines

    DATA:   .word 0b00111111            // '0'
            .word 0b00000110            // '1'

    Then these data words (extended to 16 bits) will appear in the resulting .MIF file.

