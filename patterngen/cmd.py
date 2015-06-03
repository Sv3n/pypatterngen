#!/usr/bin/env python3.4
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

from enum import IntEnum, unique

from .memspec import Spec


@unique
class CmdTp(IntEnum):
    """Note: The order should correspond to the column order in memconstraints.py"""
    ACT = 0
    PRE = 1
    RD = 2
    WR = 3
    REF = 4
    NOP = 5

    def __str__(self):
        return shortCmdNames[self.name]

shortCmdNames = dict(zip(CmdTp.__members__.keys(), ['A', 'P', 'R', 'W', 'E', 'N']))


class Cmd(object):
    def __init__(self, cmdType, bank, cycle, autoPrechargeFlag=False):
        if not isinstance(cmdType, CmdTp):
            raise TypeError
        self.cmdType = cmdType
        self.bank = bank
        self.cycle = cycle
        self.autoPrechargeFlag = autoPrechargeFlag
        self.memspec = Spec

    def __repr__(self):
        return "{tp}{bank}".format(tp=str(self.cmdType), bank=self.bank)

    @property
    def bankGroup(self):
        """ Getter for a bankGroup property. Used by memconstraints. """
        return self.bank % Spec.numBankGroups

    @property
    def type(self):
        """ Getter for a type property. Used by memconstraints. """
        return self.cmdType
