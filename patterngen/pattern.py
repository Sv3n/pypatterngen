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

from enum import Enum, unique
from .cmd import Cmd, CmdTp


@unique
class PatternTp(Enum):
    # Enum that represent different commands
    RD = 0
    WR = 1
    REF = 2
    RTW = 3
    WTR = 4

    @classmethod
    def fromCmdTp(cls, val):
        """Convenience function that converts a command type into a pattern type"""
        if isinstance(val, CmdTp):
            if val == CmdTp.RD:
                return cls(PatternTp.RD)
            elif val == CmdTp.WR:
                return cls(PatternTp.WR)
            else:
                raise ValueError
        else:
            raise TypeError


class Pattern(object):
    """Container class for a pattern, with some convenience functions"""
    def __init__(self, myType, rawPattern):
        self.myType = myType
        self.commands = rawPattern.commands
        # Command list with precharges made explicit
        self.commandsPre = rawPattern.commandsPre
        self.length = rawPattern.length

    def __len__(self):
        return self.length

    def __repr__(self):
        s = []
        for cmd in self:
            s.append(str(cmd))
        cmds = '-'.join(s)
        return 'length: {len}\nCommands: {cmds}\n'.format(len=len(self), cmds=cmds)

    def __getitem__(self, key):
        """Returns commands for keys in the range [0 ... len-1]"""
        if not isinstance(key, int):
            raise TypeError
        if key >= len(self):
            raise IndexError
        for cmd in self.commands:
            if cmd.cycle == key:
                return cmd
        else:
            return Cmd(CmdTp.NOP, 0, 0)


if __name__ == '__main__':
    a = Pattern(PatternTp.RD, (10, False, []))
    print(a[0])
