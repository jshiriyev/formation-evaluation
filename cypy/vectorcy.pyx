import numpy

cimport numpy
cimport cython

from libc.stdlib cimport malloc, free
from libc.string cimport strcmp
from cpython.string cimport PyString_AsString

numpy.import_array()

# ctypedef numpy.str DTYPE_t
# ctypedef numpy.int_t DTYPEINT
ctypedef numpy.float_t DTYPE_f

cdef char ** to_cstring_array(list_str):
    cdef char **ret = <char **>malloc(len(list_str) * sizeof(char *))
    for i in xrange(len(list_str)):
        ret[i] = PyString_AsString(list_str[i])
    return ret

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef numpy.ndarray[DTYPE_f,ndim=1] starsplit(string_arr, float default=1.0):
    """It returns star splitted list repeating post-star pre-star times."""

    cdef int arr_size = len(string_arr)

    cdef char **c_str_arr = to_cstring_array(string_arr)

    cdef numpy.ndarray multp_arr = numpy.ones(
        arr_size,dtype=numpy.int32)

    cdef numpy.ndarray float_arr = numpy.full(
        arr_size,default,dtype=numpy.float64)

    # cdef str string

    cdef str multch
    cdef str valch

    cdef int index

    for index in range(arr_size):

    # for index,string in enumerate(string_arr):

        if "*" in c_str_arr[index]:

            multch,valch = c_str_arr[index].split("*",maxsplit=1)

            multp_arr[index] = int(multch)

            if not c_str_arr[index].endswith("*"):
                float_arr[index] = float(valch)

            # for index in range(multpl):
            #     float_list.append(value)

        else:

            float_arr[index] = float(c_str_arr[index])

    return numpy.repeat(float_arr,multp_arr)