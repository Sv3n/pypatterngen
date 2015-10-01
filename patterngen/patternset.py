#!/usr/bin/env python3
"""
Copyright (c) 2015, Eindhoven University of Technology

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of this project nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 Authors: Sven Goossens
"""

from .pattern import PatternTp
from .memspec import Spec


class PatternSet(dict):
    """A collection of patterns"""
    def __init__(self, bi, bc, bgi, *args):
        self.BI = bi
        self.BC = bc
        self.BGI = bgi
        super().__init__(*args)

    @property
    def AG(self):
        """Returns the access granularity of the patterns in bytes"""
        return Spec.spec.BL * Spec.spec.width / 8 * self.BI * self.BC

    def worstCaseBandwidth(self):
        """
        Worst-case back-end bandwidth of the pattern set.
        Based on Akesson2010RTCSA, or the Springer book
        ("Memory Controllers for Real-Time Embedded Systems")
        """
        e_ref = 1 - (float(self.tref) / Spec.spec.REFI)

        f = Spec.spec.clkMhz
        trwInterleaved = self.tw + self.tr + self.twtr + self.trtw
        return e_ref * float(self.AG) * min(1.0 / self.tw,
                                            1.0 / self.tr,
                                            2.0 / trwInterleaved) * f

    def __setitem__(self, key, value):
        """Act like a dict for keys that are pattern types (PatternTp)."""
        if not isinstance(key, PatternTp):
            raise TypeError
        return super().__setitem__(key, value)

    @property
    def tw(self):
        """Write pattern length"""
        return len(self[PatternTp.WR])

    @property
    def tr(self):
        """Read pattern length"""
        return len(self[PatternTp.RD])

    @property
    def twtr(self):
        """Write-to-read switching pattern length"""
        return len(self[PatternTp.WTR])

    @property
    def trtw(self):
        """Read-to-write switching pattern length"""
        return len(self[PatternTp.RTW])

    @property
    def tref(self):
        """Refresh pattern length"""
        return len(self[PatternTp.REF])
