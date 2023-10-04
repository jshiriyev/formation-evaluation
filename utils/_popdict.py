# DO NOT TOUCH POPDICT, IT'S WORKING PERFECTLY FINE!

def popdict(pydict:dict,key:str,default=None):
    """Returns the value of pydict[key]. If the key is not
    in the dictionary, default value will be returned
    """
    try:
        return pydict.pop(key)
    except KeyError:
        return default

if __name__ == "__main__":

    a = {}

    a["name"] = "John"
    a["job"] = "Businessman"

    print(f"{a = }")

    b = popdict(a,"name")

    print(f"{a = }, {b = }")

    c = popdict(a,"age")

    print(f"{a = }, {c = }, {type(c) = }")

    d = popdict(a,"location","London")

    print(f"{a = }, {d = }")