# -*- coding: utf-8 -*-
# Copyright (c) 2017 Richard Hull and contributors
# See LICENSE.rst for details.

import os
import sys
import time
import warnings
import ctypes.util


__all__ = ["deprecation", "monotonic"]


try:
    # only available since python 3.3
    monotonic = time.monotonic
except AttributeError:
    if sys.platform == 'darwin':  # OS X, iOS
        libc = ctypes.CDLL('/usr/lib/libc.dylib', use_errno=True)

        class mach_timebase_info_data_t(ctypes.Structure):
            """System timebase info. Defined in <mach/mach_time.h>."""
            _fields_ = (('numer', ctypes.c_uint32),
                        ('denom', ctypes.c_uint32))

        mach_absolute_time = libc.mach_absolute_time
        mach_absolute_time.restype = ctypes.c_uint64

        timebase = mach_timebase_info_data_t()
        libc.mach_timebase_info(ctypes.byref(timebase))
        ticks_per_second = timebase.numer / timebase.denom * 1.0e9

        def monotonic():
            """
            Monotonic clock that cannot go backward.
            """
            return mach_absolute_time() / ticks_per_second
    else:
        try:
            clock_gettime = ctypes.CDLL(ctypes.util.find_library('c'),
                                        use_errno=True).clock_gettime
        except AttributeError:
            clock_gettime = ctypes.CDLL(ctypes.util.find_library('rt'),
                                        use_errno=True).clock_gettime

        class timespec(ctypes.Structure):
            """
            Time specification, as described in clock_gettime(3).
            """
            _fields_ = (('tv_sec', ctypes.c_long),
                        ('tv_nsec', ctypes.c_long))

        def monotonic():
            """
            Monotonic clock that cannot go backward.
            """
            ts = timespec()
            if clock_gettime(1, ctypes.pointer(ts)):
                errno = ctypes.get_errno()
                raise OSError(errno, os.strerror(errno))
            return ts.tv_sec + ts.tv_nsec / 1.0e9


def deprecation(message):
    warnings.warn(message, DeprecationWarning, stacklevel=2)