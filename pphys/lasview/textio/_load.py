def loadlas(*args,**kwargs):
    """
    Returns an instance of pphys.LasFile. If a filepath is specified, the instance
    represents the file.
    
    Arguments:
        filepath {str} -- path to the given LAS file

    Keyword Arguments:
        homedir {str} -- path to the home (output) directory
        filedir {str} -- path to the file (input) directory
    
    Returns:
        pphys.LasFile -- an instance of pphys.LasFile filled with LAS file text.

    """

    if len(args)==1:
        filepath = args[0]
    elif len(args)>1:
        raise "The function does not take more than one positional argument."

    # It creates an empty pphys.LasFile instance.
    nullfile = LasFile(filepath=filepath,**kwargs)

    # It reads LAS file and returns pphys.LasFile instance.
    fullfile = LasWorm(nullfile).lasfile

    return fullfile

def loadtxt(filepath,**kwargs):
    """
    Returns an instance of textio.TxtFile for the given filepath.
    
    Arguments:
        filepath {str} -- path to the given txt file

    Keyword Arguments:
        homedir {str} -- path to the home (output) directory
        filedir {str} -- path to the file (input) directory
    
    Returns:
        textio.TxtFile -- an instance of textio.TxtFile filled with LAS file text.

    """

    # It creates an empty textio.TxtFile instance.
    nullfile = TxtFile(filepath=filepath)

    # It reads text file and returns textio.txtfile instance.
    return TxtWorm(nullfile,**kwargs).txtfile