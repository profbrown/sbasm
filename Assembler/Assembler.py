import os
import sys
import re

from ErrorCodes import *


class Assembler(object):
    """
    Assembler class.
    """
    
    # Define regular expressions patterns that can be used to parse lines of assembly code
    # REGEX to match a single line comment
    COMMENT_REGEX = re.compile('//.*$')
    
    # REGEX string to match trailing space and a comment
    TRAIL_SPACE_COMMENT = '\s*(//.*)?$'
    
    # REGEX to match the DEPTH definition
    DEPTH_DEF_REGEX = re.compile('DEPTH\s+(\d+)' + TRAIL_SPACE_COMMENT)
    
    # REGEX to match a define (.define) statement
    DEFINE_REGEX = re.compile('\.define\s+([a-zA-Z_$][a-zA-Z_$0-9]*)\s+((0|0b|0x)?\w+)' + 
        TRAIL_SPACE_COMMENT)
    
    # REGEX string to match a label only
    LABEL_REGEX_STR = '([a-zA-Z_$][a-zA-Z_$0-9]*):'
    
    # REGEX to match a label with trailing comment (no trailing instruction)
    LABEL_REGEX = re.compile(LABEL_REGEX_STR + TRAIL_SPACE_COMMENT)
    
    # REGEX to match instructions. Includes an optional preceeding label and trailing comment
    # type 1 is an instruction with Op2 = register
    INSTR_TYPE1_REGEX = re.compile('(' + LABEL_REGEX_STR + ')?\s*' + 
        '(mv|add|sub|ld|st|and)\s+(r[0-7]|pc),\s*\[*(r[0-7]|pc)\]*' + TRAIL_SPACE_COMMENT)
    # type 2 is an instruction with Op2 = #Data
    INSTR_TYPE2_REGEX = re.compile('(' + LABEL_REGEX_STR + ')?\s*' + 
        '(mv|mvt|add|sub|and)\s+(r[0-7]|pc),\s*#*(((0|0b|0x)?\w+)|[a-zA-Z_$][a-zA-Z_$0-9]*)+' +
        TRAIL_SPACE_COMMENT)
    # type 3 is a branch instruction
    INSTR_TYPE3_REGEX = re.compile('(' + LABEL_REGEX_STR + ')?\s*' + 
        '(b(eq|ne|cc|cs)?)\s+#*(((0|0b|0x)?\w+)|[a-zA-Z_$][a-zA-Z_$0-9]*)+' + 
        TRAIL_SPACE_COMMENT)
    # error check for an instruction that is not ld|st but Op2 = [rY]
    INSTR_TYPE1_CHK_REGEX = re.compile('(' + LABEL_REGEX_STR + ')?\s*' + 
        '(mv|add|sub|and)\s+(r[0-7]|pc),\s*\[(r[0-7]|pc)\]' + TRAIL_SPACE_COMMENT)

    # REGEX to match .word directive. Includes an optional preceeding label and a 
    # trailing comment
    WORD_DIR_REGEX = re.compile('(' + LABEL_REGEX_STR + ')?\s*' + '(.word)\s+((0|0b|0x)?\w+)' + 
        TRAIL_SPACE_COMMENT)
    
    # Max integers 
    MAX_INT_16U = 65535     # maximum size of an integer (16 bits)
    MAX_INT_IMM = 0x1FF     # maximum size of immediate data
    
    # Maps instruction strings to integer values
    # Used for forming machine code words
    INSTR_STR_TO_VAL = {'mv': 0, 'mvt': 1, 'add': 2, 'sub': 3, 'ld': 4, 'st': 5, 'and': 6, 
        'b': 7, 'beq':7, 'bne':7, 'bcc':7, 'bcs':7}
    
    # Maps register strings to integer values. Both r7 and pc are register 7
        # Used for forming machine code words
    REG_STR_TO_VAL = {'r0': 0, 'r1': 1, 'r2': 2, 'r3': 3, 'r4': 4, 'r5': 5, 'r6': 6, 
        'r7': 7, 'pc': 7}
    
    # Maps condition strings for branches to integer values
        # Used for forming machine code words
    COND_STR_TO_VAL = {'': 0, 'eq': 1, 'ne': 2, 'cc': 3, 'cs': 4}
    
    # Maps integers (indices of this list) to instruction strings
        # Used for printing comments at the end of a line of machine code
    INSTR_VAL_TO_STR = ['mv  ', 'mvt ', 'add ', 'sub ', 'ld  ', 'st  ', 'and', 'b', 
        'beq', 'bne', 'bcc', 'bcs']
    
    # Maps integers (indices of this list) to register strings
        # Used for printing comments at the end of a line of machine code
    REG_VAL_TO_STR = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7']
    
    # Maps integers (indices of this list) to condition strings
        # Used for printing comments at the end of a line of machine code
    COND_VAL_TO_STR = ['  ', 'eq', 'ne', 'cc', 'cs', '', '', '']
    
    def __init__(self, in_filename, out_filename):
        """
        Initializes the assembler.
        Args:
            in_filename: The input filename.
            out_filename: The output filname.
        """
        # Store the input filename
        self.in_filename = in_filename
        
        # Store the outputfilename, default to a.mif
        if out_filename is None:
            out_filename = 'a.mif'
        self.out_filename = out_filename
        
        # The lines of the input file will be stored here
        self.lines = []
        
        # Stores the assembled machine instructions
        self.machine_instructions = []
        
        # Indicates whether a word of machine code is an instruction or data. 
        # A value of 0 indicates data
        self.is_inst = []
        
        # Maps labels and defines to (line) numbers
        self.symbol_def_to_num = {}
        
        # Width bits (only 16 is currently supported)
        self.width_bits = 16
        
        # Depth - should correspond to the total number of words in memory
        self.depth_words = 256
        
        # Tracks current line number of the input file
        self.line = 0
        
        # Tracks the current instruction number being assembled
        self.curr_instr_num = -1
        
        # Validate input and output filenames
        if not in_filename.strip() or not os.path.isfile(in_filename):
            print('Input file: ' + in_filename + ' is invalid')
            sys.exit()
        elif not out_filename.strip():
            print('Output file: ' + out_filename + ' is invalid')
            sys.exit()
        else:
            in_file = open(in_filename, 'r')
            self.lines = in_file.read().splitlines()


    def assemble(self):
        """
        Assembles the input file into the output file.
        """
        # validate and parse the in and out filenames.
        self.__validate_out_filename()
        width = 0
        depth = 0
        line = 0
        
        # Preprocess by finding the labels
        error = self.__find_labels()
            
        if error is not ErrorCodes.NO_ERROR:
            # Error in preprocess.
            print(ErrorCodes.get_error_message(error, self.line, self.depth_words, 
                self.curr_instr_num))
        else:
            # Parse the lines of the input file
            error = self.__parse_lines()

            if error is not ErrorCodes.NO_ERROR:
                # Error in processing
                print(ErrorCodes.get_error_message(error, self.line, self.depth_words, 
                    self.curr_instr_num))
            else:
                # Output the MIF file
                self.__output_file()
    
    
    def __find_labels(self):
        """
        Preprocessing - finds all labels and defines
        Returns:
            int: ErrorCodes.BAD_INFILE on error, ErrorCodes.NO_ERROR otherwise
        """
        # Reset the current line and instruction number
        self.line = 1
        self.curr_instr_num = -1
        
        for line in self.lines:
            line = line.strip()
            match = None
            
            # Skip empty lines and comments.
            if line != "" and line != "\n" and not self.__is_comment(line):
                # Check matches of REGEXs
                if self.DEPTH_DEF_REGEX.match(line):
                    # Line matches DEPTH line, get the value
                    match = self.DEPTH_DEF_REGEX.match(line)
                    depth = int(match.group(1), 0)
                    
                    # Depth must be a power of 2
                    if depth % 2 != 0:
                        return ErrorCodes.DEPTH_ERROR
                    else:
                        self.depth_words = depth
                elif self.DEFINE_REGEX.match(line):
                    # Line is a define statement
                    match = self.DEFINE_REGEX.match(line)
                    
                    # Get the symbol and the number
                    symbol = match.group(1)
                    num = int(match.group(2), 0)
                    
                    if symbol == 'DEPTH':
                        return ErrorCodes.DEPTH_DEFINE
                    elif symbol in self.symbol_def_to_num:
                        return ErrorCodes.DEFINE_REDEF
                    elif self.__is_number_too_large(num):
                        return ErrorCodes.BIG_DEFINE
                    else:
                        # Add the mapping to the symbol -> value mapping
                        self.symbol_def_to_num[symbol] = num
                elif self.LABEL_REGEX.match(line):
                    # Line is only a label
                    match = self.LABEL_REGEX.match(line)
                    label = match.group(1)
                    
                    if label == 'DEPTH':
                        return ErrorCodes.DEPTH_DEFINE
                    elif label in self.symbol_def_to_num:
                        return ErrorCodes.DEFINE_REDEF
                    else:
                        # Add the mapping to the label -> value mapping
                        self.symbol_def_to_num[label] = self.curr_instr_num + 1
                else:
                    # the rest of the types are parsed in the same way
                    if self.INSTR_TYPE1_REGEX.match(line):
                        # Line is an instruction of type 1 (no immediate data)
                        match = self.INSTR_TYPE1_REGEX.match(line)
                    elif self.INSTR_TYPE2_REGEX.match(line):
                        # Line is an instruction of type 2 (#immediate)
                        match = self.INSTR_TYPE2_REGEX.match(line)
                    elif self.INSTR_TYPE3_REGEX.match(line):
                        # Line is an instruction of type 3 (branch)
                        match = self.INSTR_TYPE3_REGEX.match(line)
                    elif self.WORD_DIR_REGEX.match(line):
                        # Line is a .word directive
                        match = self.WORD_DIR_REGEX.match(line)

                    # Grab the possible label
                    label = match.group(2)
            
                    if label == 'DEPTH':
                        return ErrorCodes.DEPTH_DEFINE
                    elif label in self.symbol_def_to_num:
                        return ErrorCodes.DEFINE_REDEF
                    elif label is not None:
                        # Label was defined, add it to the mapping
                        self.symbol_def_to_num[label] = self.curr_instr_num + 1
        
                    # Increment instruction number
                    self.curr_instr_num += 1
                if match is None:
                    # Line matches nothing, which is bad
                    print("Error: can't parse assembly code on line " + str(self.line))
                    
            # Keep track of line number for error reporting
            self.line += 1
        #ENDFOR
            
        return ErrorCodes.NO_ERROR
        
        
    def __parse_lines(self):
        """
        Processing. Parses the lines of the input file.
        Returns:
            int: ErrorCodes.BAD_INFILE on error, ErrorCodes.NO_ERROR otherwise.
        """
        self.line = 1
        self.curr_instr_num = -1
        
        for line in self.lines:
            line = line.strip()
            match = None
            
            # Skip empty lines and comments.
            if line != "" and line != "\n" and not self.__is_comment(line):
                # Only need to parse instructions and .word directives
                if self.INSTR_TYPE1_REGEX.match(line):
                    # Type 1 instruction.
                    (error, sub_mif) = self.__parse_type1_instruction(line)
                    
                    if error == ErrorCodes.NO_ERROR:
                        # Increment instruction number.
                        self.curr_instr_num += 1
                        # Add assembled machine code to the machine instructions
                        self.machine_instructions.extend(sub_mif)
                        self.is_inst.extend([True])
                    else:
                        return error
                elif self.INSTR_TYPE2_REGEX.match(line):
                    (error, sub_mif) = self.__parse_type2_instruction(line)
                    
                    if error == ErrorCodes.NO_ERROR:
                        # Increment instruction number.
                        self.curr_instr_num += 1
                        # Add assembled machine code to the machine instructions
                        self.machine_instructions.extend(sub_mif)
                        self.is_inst.extend([True])
                    else:
                        return error
                elif self.INSTR_TYPE3_REGEX.match(line):
                    (error, sub_mif) = self.__parse_type3_instruction(line)
                    
                    if error == ErrorCodes.NO_ERROR:
                        # Increment instruction number.
                        self.curr_instr_num += 1
                        # Add assembled machine code to the machine instructions
                        self.machine_instructions.extend(sub_mif)
                        self.is_inst.extend([True])
                    else:
                        return error
                elif self.WORD_DIR_REGEX.match(line):
                    # .word directive
                    (error, sub_mif) = self.__parse_word_dir(line)
                    
                    if error == ErrorCodes.NO_ERROR:
                        # Increment instruction number.
                        self.curr_instr_num += 1
                        # Add assembled machine code to the machine instructions
                        self.machine_instructions.extend(sub_mif)
                        # put False into is_inst array to indicate data item
                        self.is_inst.extend([False])
                    else:
                        return error
            
            # Move to the next line.
            self.line += 1
        #ENDFOR
        
        return ErrorCodes.NO_ERROR
        
        
    def __output_file(self):
        """
        Outputs the machine instructions to the output mif file.
        """
        # Open file for writing, should already be verified.
        out_file = open(self.out_filename, 'w')
        
        ####################################################
        ## MIF Data.
        out_file.write('WIDTH = ' + str(self.width_bits) + ';\n')
        out_file.write('DEPTH = ' + str(self.depth_words) + ';\n')
        out_file.write('ADDRESS_RADIX = HEX;\n')
        out_file.write('DATA_RADIX = HEX;\n\n')
        out_file.write('CONTENT\nBEGIN\n')
        
        ########################
        ## Instructions.
        instruction_num = 0
        instruction_format_str = '%0' + str(self.width_bits/4) + 'x'
        i = 0
        
        while i < len(self.machine_instructions):
            # Get the current instruction.
            instruction = self.machine_instructions[i]
            write_comment = self.is_inst[i]
            
            # Format the instruction number and the instruction itself (HEX).
            instruction_num_str = '%x' % i
            instruction_str = instruction_format_str % (instruction)
            
            # Move to the next instruction.
            i += 1
            
            # Write to the output file, format - <inst #>    : <inst>;    % inst comment.
            if write_comment:
                # Convert the current instruction into a comment.
                comment_str = self.__instruction_to_comment(instruction)
                out_file.write(instruction_num_str + '\t\t: ' + instruction_str + ';\t\t% ' + 
                    comment_str + '\n')
            else:
                out_file.write(instruction_num_str + '\t\t: ' + instruction_str + ';\t\t% ' + 
                'data %\n')
            
        #ENDWHILE
        ########################
        
        out_file.write('END;\n')
        ####################################################

    
    def __validate_out_filename(self):
        """
        Validates the output filename. Appends a '.mif' extension if it is missing.
        """
        if not self.out_filename.endswith('.mif'):
            self.out_filename += '.mif'
            
            
    def __is_comment(self, line):
        """
        Determines if a line is a comment.
        Returns:
            Boolean: True if the line is a comment, False otherwise.
        """
        return self.COMMENT_REGEX.match(line)
        
    
    def __parse_type1_instruction(self, line):
        """
        Parses a type 1 instruction (no immediate data)
        Args:
            line: The line from the input file which matched the INSTR_TYPE1_REGEX.
        Returns:
            int: ErrorCodes.NO_ERROR on success, some error code on failure.
            [int]: An array of MIF instructions which is the assembled machine code.
        """
        # error check to see if instruction uses [rY] but is not ld or st
        if self.INSTR_TYPE1_CHK_REGEX.match(line):
            return ErrorCodes.BAD_INSTR, []
        match = self.INSTR_TYPE1_REGEX.match(line)
        
        # Grab the instruction and registers from the REGEX.
        instr = self.INSTR_STR_TO_VAL.get(match.group(3))
        ra = self.REG_STR_TO_VAL.get(match.group(4))
        rb = self.REG_STR_TO_VAL.get(match.group(5))
        
        if instr is None:
            return ErrorCodes.BAD_INSTR, []
        elif ra is None:
            return ErrorCodes.BAD_REG, []
        elif rb is None:
            return ErrorCodes.BAD_REG, []
        else:
            # Create the instruction and return it.
            mif_instr = self.__make_type1_instruction(instr, ra, rb)
            return ErrorCodes.NO_ERROR, [mif_instr]


    def __parse_type2_instruction(self, line):
        """
        Parses a type 2 instruction (#immediate operand).
        Args:
            line: The line from the input file which matched the INSTR_TYPE2_REGEX.
        Returns:
            int: ErrorCodes.NO_ERROR on success, some error code on failure.
            [int]: An array of MIF instructions which is the assembled machine code.
        """
        match = self.INSTR_TYPE2_REGEX.match(line)
        # Grab the instruction, register and immediate value from the REGEX.
        instr = self.INSTR_STR_TO_VAL.get(match.group(3))
        ra = self.REG_STR_TO_VAL.get(match.group(4))
        imm_str = match.group(5)
        imm = None
        try:
            imm = int(imm_str, 0)
        except ValueError:
            # see if the immediate is a valid symbolic name
            imm = self.symbol_def_to_num.get(imm_str)
            if imm is None:
                return ErrorCodes.IMMED_LABEL_NF, []
        
        # error check the value of the immediate constant
        if self.INSTR_VAL_TO_STR[instr] != 'mvt ':
            if self.__is_number_too_large_imm(imm):
                return ErrorCodes.BIG_IMMED, []
        else:
            if self.__is_number_bad_imm(imm):
                return ErrorCodes.BAD_IMMED, []

        if instr is None:
            return ErrorCodes.BAD_INSTR, []
        elif ra is None:
            return ErrorCodes.BAD_REG, []
        else:
            mif_instr = self.__make_type2_instruction(instr, ra, imm)
            return ErrorCodes.NO_ERROR, [mif_instr]
    
    def __parse_type3_instruction(self, line):
        """
        Parses a type 3 instruction (branch).
        Args:
            line: The line from the input file which matched the INSTR_TYPE3_REGEX.
        Returns:
            int: ErrorCodes.NO_ERROR on success, some error code on failure.
            [int]: An array of MIF instructions which is the assembled machine code.
        """
        match = self.INSTR_TYPE3_REGEX.match(line)
        
        # Grab the instruction, condition and branch address from the REGEX
        instr = self.INSTR_STR_TO_VAL.get(match.group(3))
        cond = match.group(4)
        if cond is not None:
            cond = self.COND_STR_TO_VAL.get(match.group(4))
        else:
            cond = self.COND_STR_TO_VAL.get('')
        address = match.group(5)
        imm = None
        try:
            imm = int(address, 0)
        except ValueError:
            # see if the immediate is a valid symbolic name
            imm = self.symbol_def_to_num.get(address)
            if imm is None:
                return ErrorCodes.IMMED_LABEL_NF, []
        
        # error check the value of the immediate constant (#Label)
        if imm >= self.depth_words:
            return ErrorCodes.BIG_BRANCH, []

        if instr is None:
            return ErrorCodes.BAD_INSTR, []
        # Create the instruction and return it with the immediate value.
        mif_instr = self.__make_type3_instruction(instr, cond, imm)
        return ErrorCodes.NO_ERROR, [mif_instr]
    
    
    def __make_type1_instruction(self, instr, ra, rb):
        """
        Converts an instruction to machine code.
        Args:
            instr: the instruction int.
            ra: The first regsiter int.
            rb: The second register int.
        Returns:
            int: The machine code for the instruction.
        """
        return rb | (ra << 9) | (instr << 13)
        
    def __make_type2_instruction(self, instr, ra, imm):
        """
        Converts an instruction to machine code.
        Args:
            instr: the instruction int.
            ra: The first regsiter int.
            imm: The immediate data
        Returns:
            int: The machine code for the instruction.
        """
        if not self.INSTR_VAL_TO_STR[instr] == 'mvt ':
            return (imm & 0x1FF) | (ra << 9) | (1 << 12) | (instr << 13)
        else:
            return (imm >> 8) | (ra << 9) | (1 << 12) | (instr << 13)
    
    def __make_type3_instruction(self, instr, cond, imm):
        """
        Converts an instruction to machine code.
        Args:
            instr: the instruction int. for branch
            cond: The branch condition int.
            imm: The immediate data
        Returns:
            int: The machine code for the instruction.
        """
        return (imm & 0x1FF) | (cond << 9) | (1 << 12) | (instr << 13)
    
    def __parse_word_dir(self, line):
        """
        Parses a .word directive 
        Args:
            line: The line from the input file which matched the WORD_DIR_REGEX.
        Returns:
            int: ErrorCodes.NO_ERROR on success, some error code on failure.
            [int]: An array of MIF instructions which is the assembled machine code.
        """
        match = self.WORD_DIR_REGEX.match(line)
        data_str = match.group(4)
        
        # Grab the instruction and registers from the REGEX.
        try:
            data = int(data_str, 0)
        except ValueError:
            return ErrorCodes.BAD_DATA, []
        
        return ErrorCodes.NO_ERROR, [data]
    
    
    def __is_number_too_large(self, num):
        """
        Determines is a number is too large for the architecture.
        Args:
            num: The number to check.
        Returns:
            Boolean: True if the number is too large.
        """
        return num > self.MAX_INT_16U

    def __is_number_too_large_imm(self, num):
        """
        Determines is a number is too large for the architecture.
        Args:
            num: The number to check.
        Returns:
            Boolean: True if the number is too large.
        """
        return num > self.MAX_INT_IMM


    def __is_number_bad_imm(self, num):
        """
        Determines is a number is inappropriate for the mvt instruction
        Args:
            num: The number to check.
        Returns:
            Boolean: True if the number is too large.
        """
        return (num & 0xFF) != 0


    def __instruction_to_comment(self, instr):
        """
        Converts an instruction to a comment.
        Args:
            instr: The current instruction.
        Returns:
            str: The string form of the instruction.
        """
        # Parse out the instruction and first and second registers.
        rb = instr & 0x0007
        ra = (instr >> 9) & 0x0007
        imm = (instr >> 12) & 0x0001
        i = (instr >> 13) & 0x0007
        # Parse out the condition for a branch
        cond = (instr >> 9) & 0x0007
        
        # Create the comment for branch instructions
        if i == self.INSTR_STR_TO_VAL['b']:
            comment = self.INSTR_VAL_TO_STR[i] + self.COND_VAL_TO_STR[cond] + '  '
        else:
            comment = self.INSTR_VAL_TO_STR[i] + ' ' + self.REG_VAL_TO_STR[ra] + ', '
        
        # Append the immediate value if used
        if imm == 1:
            if self.INSTR_VAL_TO_STR[i] != 'mvt ':
                comment += '#0x%04x' % (instr & 0x1FF)
            else:
                comment += '#0x%04x' % ((instr & 0x1FF) << 8)
        else:
            if self.INSTR_VAL_TO_STR[i] == 'ld  ' or self.INSTR_VAL_TO_STR[i] == 'st  ':
                comment += '[' + self.REG_VAL_TO_STR[rb] + ']'
            else:
                comment += self.REG_VAL_TO_STR[rb]
            
        comment += ' %'
        return comment
        
        
