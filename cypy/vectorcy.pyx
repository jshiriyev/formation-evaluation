import numpy

cimport numpy
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef list starsplit(string_arr, float default=1.0):
    """It returns star splitted list repeating post-star pre-star times."""

    cdef str string

    cdef str str_multiplier
    cdef str str_value

    cdef int multiplier

    cdef float value

    cdef list float_array = []

    for string in string_arr:

        if "*" in string:

            str_multiplier,str_value = string.split("*",maxsplit=1)

            multiplier = int(str_multiplier)

            if string.endswith("*"):
                value = default
            else:
                value = float(str_value)

            for _ in range(multiplier):
                float_array.append(value)

        else:

            value = float(string)

            float_array.append(value)

    return float_array