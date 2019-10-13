
class ErrorCodes(object):
    """
    Static class for error codes.
    """
    
    # Error code objects.
    NO_ERROR           = 0
    BAD_INSTR          = 1
    BAD_REG            = 2
    BAD_IMMED          = 3
    BIG_IMMED          = 4
    BIG_DEFINE         = 5
    DEFINE_REDEF       = 6
    IMMED_LABEL_NF     = 7
    DEPTH_ERROR        = 8
    BAD_DATA           = 9
    DEPTH_DEFINE       = 10
    BIG_BRANCH         = 11
    UNKNOWN            = 12        # Always the last error
    
    
    @staticmethod
    def get_error_message(error_code, line, depth, instruction_count):
        """
        Converts the given error code and info into a string message.
        Args:
            error_code: int [NO_ERROR, UNKNOWN]
            line: The line number the error is on
            depth: The depth of the max MIF file
            instruction_count: The current instruction count
        Returns:
            A detailed string for the error.
        """
        error_code = min(error_code, ErrorCodes.UNKNOWN)
        line_str = str(line)
        
        return {
            ErrorCodes.NO_ERROR       : '',
            ErrorCodes.BAD_INSTR      : 'ERROR: line ' + line_str + ': unknown instruction',
            ErrorCodes.BAD_REG        : 'ERROR: line ' + line_str + ': unknown register',
            ErrorCodes.BAD_IMMED      : 'ERROR: line ' + line_str + 
                ': the immediate value for mvt should be 0 in the eight least-significant bits',
            ErrorCodes.BIG_IMMED      : 'ERROR: line ' + line_str + 
                ': the immediate value is too large',
            ErrorCodes.BIG_DEFINE     : 'ERROR: line ' + line_str + ': define value too large',
            ErrorCodes.DEFINE_REDEF   : 'ERROR: line ' + line_str + ': define is being redefined',
            ErrorCodes.IMMED_LABEL_NF : 'ERROR: line ' + line_str + 
                ': undeclared identifier (label or define), or value error',
            ErrorCodes.DEPTH_ERROR    : 'ERROR: Memory depth must be an integer multiple of 2',
            ErrorCodes.BAD_DATA       : 'ERROR: line ' + line_str + ': missing or bad data',
            ErrorCodes.DEPTH_DEFINE   : 'ERROR: line ' + line_str + 
                ': symbol DEPTH is reserved, it cannot be redefined',
            ErrorCodes.BIG_BRANCH     : 'ERROR: line ' + line_str + 
                ': the branch target is too large',
            ErrorCodes.UNKNOWN        : 'ERROR: UNKNOWN'
        }[error_code]
