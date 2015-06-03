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


class memconstraintsLut(object):
    """
    The self.c member contains a LUT describing the command-to-command
    constraints of the memory in question. It's a 4D dictionary.

    The first 2 dimensions are indexed by 's' and 'd', which stands for 'same'
    and 'different'. The last two dimentions are indexed by the command types.

    1. The first index indicates that the commands go to the same or to different
    bank groups.
    2. The second index indicates the same or a different bank.
    3. The third index is the first command of the command pair, using the enum
    from the Cmd class.
    4. The fourth index is the second command of the command pair, using the enum
    from the Cmd class.

    Example:
        self.c['s']['d'][CmdTp.ACT][CmdTp.ACT] returns the number of cycles between
        two activate commands to the same bankgroup but a different bank (RRD generally).

    Using the constraintVal function is generally better than directly using
    the LUT.
    """

    def __init__(self, spec):
        self.c = None
        if spec.memory_type == 'DDR4':
            self.c = self.DDR4(spec)
        elif spec.memory_type == 'DDR3':
            self.c = self.DDR3(spec)
        elif spec.memory_type == 'DDR2':
            self.c = self.DDR2(spec)
        elif spec.memory_type == 'LPDDR':
            self.c = self.LPDDR(spec)
        elif spec.memory_type == 'LPDDR2':
            self.c = self.LPDDR2(spec)
        elif spec.memory_type == 'LPDDR3':
            self.c = self.LPDDR3(spec)
        else:
            raise Exception('Memory type %s not implemented.' % spec.memory_type)

    def sameBank(self, c0, c1):
        """Returns 's' when the two commands are directed to the same bank."""
        if c0.bank == c1.bank:
            return 's'
        return 'd'

    def sameBankGroup(self, c0, c1):
        """Returns 's' when the two commands are directed to the same bank group."""
        if c0.bankGroup == c1.bankGroup:
            return 's'
        return 'd'

    def constraintVal(self, c0, c1):
        """Returns the minimum number of cycles between the two input commands."""
        sb = self.sameBank(c0, c1)
        sbg = self.sameBankGroup(c0, c1)
        return self.c[sbg][sb][c0.type][c1.type]

    def DDR2(self, t):
        c = {}
        c['s'] = {}
        c['d'] = {}

        # BG    B        ACT         PRE                               RD                                       WR                          REF
        c['s']['s'] = [
                        (t.RC  ,   t.RAS                          ,   t.RCD                               ,   t.RCD                    ,   0    ),  # ACT
                        (t.RP  ,   0                              ,   0                                   ,   0                        ,   t.RP ),  # PRE
                        (0     ,   t.AL + t.B - 2 + max(t.RTP,2)  ,   t.B                                 ,   t.B + t.RTW              ,   0    ),  # RD
                        (0     ,   t.WL + t.B + t.WR              ,   t.CL - 1 + t.B + t.WTR              ,   t.B                      ,   0    ),  # WR
                        (t.RFC ,   0                              ,   0                                   ,   0                        ,   0    ),  # REF
        ]
        # BG    B       ACT         PRE                   RD                                   WR                           REF
        c['s']['d'] = [
                        (t.RRD ,   0                              ,   1                                   ,   1                        ,   0    ),  # ACT
                        (0     ,   0                              ,   0                                   ,   0                        ,   t.RP ),  # PRE
                        (0     ,   0                              ,   t.B                                 ,   t.B + t.RTW              ,   0    ),  # RD
                        (0     ,   0                              ,   t.CL - 1 + t.B + t.WTR              ,   t.B                      ,   0    ),  # WR
                        (t.RFC ,   0                              ,   0                                   ,   0                        ,   0    ),  # REF
        ]
        c['d']['d'] = None
        return c

    def DDR3(self, t):
        c = {}
        c['s'] = {}
        c['d'] = {}

        # BG    B        ACT         PRE                   RD                                       WR                          REF
        c['s']['s'] = [
                        (t.RC  ,   t.RAS              ,   t.RCD                               ,   t.RCD                    ,   0    ),  # ACT
                        (t.RP  ,   0                  ,   0                                   ,   0                        ,   t.RP ),  # PRE
                        (0     ,   t.AL+ max(t.RTP,4) ,   t.B                                 ,   t.B + t.RL - t.WL + 2    ,   0    ),  # RD
                        (0     ,   t.WL+ t.B + t.WR   ,   t.B + max(0, t.WL - t.AL + t.WTR  ) ,   t.B                      ,   0    ),  # WR
                        (t.RFC ,   0                  ,   0                                   ,   0                        ,   0    ),  # REF
        ]
        # BG    B       ACT         PRE                   RD                                   WR                           REF
        c['s']['d'] = [
                        (t.RRD    ,   0               ,   1                                   ,   1                        ,   0    ),    # ACT
                        (0        ,   0               ,   0                                   ,   0                        ,   t.RP ),    # PRE
                        (1        ,   0               ,   t.B                                 ,   t.B + t.RL - t.WL + 2    ,   0    ),    # RD
                        (1        ,   0               ,   t.B + max(0, t.WL - t.AL + t.WTR)   ,   t.B                      ,   0    ),    # WR
                        (t.RFC    ,   0               ,   0                                   ,   0                        ,   0    ),    # REF
        ]
        c['d']['d'] = None
        return c

    def DDR4(self, t):
        c = {}
        c['s'] = {}
        c['d'] = {}

        # BG    B        ACT         PRE                   RD                                       WR                          REF
        c['s']['s'] = [
                        (t.RC  ,   t.RAS              ,   t.RCD                               ,   t.RCD                    ,   0    ),  # ACT
                        (t.RP  ,   0                  ,   0                                   ,   0                        ,   t.RP ),  # PRE
                        (0     ,   t.AL+ t.RTP        ,   t.CCD_L                             ,   t.B + t.RL - t.WL + t.PA ,   0    ),  # RD
                        (0     ,   t.WL+ t.B + t.WR   ,   t.B + max(0, t.WL - t.AL + t.WTR_L) ,   t.CCD_L                  ,   0    ),  # WR
                        (t.RFC ,   0                  ,   0                                   ,   0                        ,   0    ),  # REF
        ]
        # BG    B       ACT         PRE                   RD                                   WR                           REF
        c['s']['d'] = [
                        (t.RRD_L  ,   0            ,   1                                   ,   1                        ,   0    ),    # ACT
                        (0        ,   0            ,   0                                   ,   0                        ,   t.RP ),    # PRE
                        (1        ,   0            ,   t.CCD_L                             ,   t.B + t.RL - t.WL + t.PA ,   0    ),    # RD
                        (1        ,   0            ,   t.B + max(0, t.WL - t.AL + t.WTR_L) ,   t.CCD_L                  ,   0    ),    # WR
                        (t.RFC    ,   0            ,   0                                   ,   0                        ,   0    ),    # REF
        ]
        # BG    B       ACT         PRE                  RD                             WR                  REF
        c['d']['d'] = [
                        (t.RRD_S  ,   0            ,   1                                   ,   1                        ,   0    ),    # ACT
                        (0        ,   0            ,   0                                   ,   0                        ,   t.RP ),    # PRE
                        (1        ,   0            ,   t.CCD_S                             ,   t.B + t.RL - t.WL + t.PA ,   0    ),    # RD
                        (1        ,   0            ,   t.B + max(0, t.WL - t.AL + t.WTR_S) ,   t.CCD_S                  ,   0    ),    # WR
                        (t.RFC    ,   0            ,   0                                   ,   0                        ,   0    ),    # REF
        ]
        return c

    def LPDDR(self, t):
        c = {}
        c['s'] = {}
        c['d'] = {}

        # BG    B        ACT         PRE                      RD                              WR                          REF
        c['s']['s'] = [
                        (t.RC  ,   t.RAS                 ,   t.RCD                      ,   t.RCD                    ,   0    ),  # ACT
                        (t.RP  ,   0                     ,   0                          ,   0                        ,   t.RP ),  # PRE
                        (0     ,   t.B                   ,   t.B                        ,   t.CL + t.B               ,   0    ),  # RD
                        (0     ,   t.DQSS + t.B + t.WR   ,   t.DQSS + t.B + t.WTR       ,   t.B                      ,   0    ),  # WR
                        (t.RFC ,   0                     ,   0                          ,   0                        ,   0    ),  # REF
        ]
        # BG    B       ACT         PRE                      RD                                 WR                    REF
        c['s']['d'] = [
                        (t.RRD ,   0                     ,   1                          ,   1                        ,   0    ),  # ACT
                        (0     ,   0                     ,   0                          ,   0                        ,   t.RP ),  # PRE
                        (1     ,   0                     ,   t.B                        ,   t.CL + t.B               ,   0    ),  # RD
                        (1     ,   0                     ,   t.DQSS + t.B + t.WTR       ,   t.B                      ,   0    ),  # WR
                        (t.RFC ,   0                     ,   0                          ,   0                        ,   0    ),  # REF
        ]
        c['d']['d'] = None
        return c

    def LPDDRX(self, t, D):
        """ Shared table for LPDDR2 and LPDDR3 """
        c = {}
        c['s'] = {}
        c['d'] = {}

        # BG    B        ACT         PRE                   RD                                       WR                          REF
        c['s']['s'] = [
                        (t.RC  ,   t.RAS                 ,   t.RCD                      ,   t.RCD                           ,   0    ),  # ACT
                        (t.RP  ,   0                     ,   0                          ,   0                               ,   t.RP ),  # PRE
                        (0     ,   t.B + max(0, t.RTP-D) ,   t.B                        ,   t.B + t.RL - t.WL + t.DQSCK + 1 ,   0    ),  # RD
                        (0     ,   t.WL+ t.B + t.WR + 1  ,   t.B + t.WL + t.WTR + 1     ,   t.B                             ,   0    ),  # WR
                        (t.RFC ,   0                     ,   0                          ,   0                               ,   0    ),  # REF
        ]
        # BG    B       ACT         PRE                   RD                                   WR                           REF
        c['s']['d'] = [
                        (t.RRD ,   0                     ,   1                           ,   1                               ,   0    ),  # ACT
                        (0     ,   0                     ,   0                           ,   0                               ,   t.RP ),  # PRE
                        (1     ,   0                     ,   t.B                         ,   t.B + t.RL - t.WL + t.DQSCK + 1 ,   0    ),  # RD
                        (1     ,   0                     ,   t.B + t.WL + t.WTR + 1      ,   t.B                             ,   0    ),  # WR
                        (t.RFC ,   0                     ,   0                           ,   0                               ,   0    ),  # REF
        ]
        c['d']['d'] = None
        return c

    def LPDDR3(self, t):
        return self.LPDDRX(t, D = 4)

    def LPDDR2(self, t):
        """ Assuming we are using LPDDR2 S4 devices, D = 2. For S2 devices D should be 1 """
        return self.LPDDRX(t, D = 2)
