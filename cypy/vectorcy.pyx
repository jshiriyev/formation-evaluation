cpdef starsplit(string_list,default=1.0):
    """It returns star splitted list repeating post-star pre-star times."""

    float_list = []

    cdef str string
    cdef str multch
    cdef str valch

    cdef float value

    cdef int multpl
    cdef int index

    for string in string_list:

        if "*" in string:

            if string.endswith("*"):
                multch = string.rstrip("*")
                multpl,value = int(multch),default
            else:
                multch,valch = string.split("*",maxsplit=1)
                multpl,value = int(multch),float(valch)

            for index in range(multpl):
                float_list.append(value)

        else:

            value = float(string)
            float_list.append(value)

    return float_list