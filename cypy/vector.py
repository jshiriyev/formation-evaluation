import numpy as np

def remove_thousand_separator(string):
    """It returns float after removing thousand separator (either comma or full stop)
    from string and setting decimal separator as full stop."""

    if string.count(".")>1 and string.count(",")>1:
        logging.warning(f"String contains more than one comma and dot, {string}")
        return string

    if string.count(",")>1 and string.count(".")<=1:
        string = string.replace(",","")
    elif string.count(".")>1 and string.count(",")<=1:
        string = string.replace(".","")

    if string.count(".")==1 and string.count(",")==1:
        if string.index(".")>string.index(","):
            string = string.replace(",","")
        else:
            string = string.replace(".","")
            string = string.replace(",",".")
        try:
            return float(string)
        except ValueError:
            string = string.replace(" ","")
            return float(string)
    elif string.count(".")==1:
        try:
            return float(string)
        except ValueError:
            string = string.replace(" ","")
            return float(string)
    elif string.count(",")==1:
        string = string.replace(",",".")
        try:
            return float(string)
        except ValueError:
            string = string.replace(" ","")
            return float(string)
    else:
        try:
            return float(string)
        except ValueError:
            string = string.replace(" ","")
            return float(string)

def starsplit(string_list,default=1.0):
    """It returns star splitted list repeating post-star pre-star times."""

    float_list = []

    for string in string_list:

        if "*" in string:

            if string.endswith("*"):
                mult = string.rstrip("*")
                mult,val = int(mult),default
            else:
                mult,val = string.split("*",maxsplit=1)
                mult,val = int(mult),float(val)

            for i in range(mult):
                float_list.append(val)

        else:
            
            float_list.append(float(string))

    return float_list

def starsplit_numpy(array):
    """It returns star splitted array repeating post-star pre-star times."""

    ints = np.ones(array.shape,dtype=int)

    flts = np.empty(array.shape,dtype=float)

    # array = np.char.split(array,sep="*",maxsplit=1)

    # for i,pylist in enumerate(array):

    #     if len(pylist)==1:
    #         flts[i] = float(pylist[0])
    #     else:
    #         ints[i],flts[i] = int(pylist[0]),float(pylist[1])
    for i,string in enumerate(array):

        row = string.split("*",maxsplit=1)

        if len(row)==1:
            flts[i] = float(row[0])
        else:
            ints[i],flts[i] = int(row[0]),float(row[1])

    return np.repeat(flts,ints)

def starsplit_npvect_(string):
    """It returns integer and floating number in star multiplied string."""
    
    row = string.split("*",maxsplit=1)

    if len(row)==1:
        return 1,float(row[0])
    else:
        return int(row[0]),float(row[1])

starsplit_npvect = np.vectorize(starsplit_npvect_,signature='()->(),()')