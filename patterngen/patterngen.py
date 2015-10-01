#!/usr/bin/env python3
"""
Pattern generation functions.

The functions in this file have been written to match the algorithm in the
article, and hence sometimes use constructs that are not very pythonic.
"""

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

__all__ = ['patternGenBGI', 'refPattern', 'rtwPattern', 'wtrPattern', 'rtwPatternCop', 'wtrPatternCop']

from collections import namedtuple

from .cmd import CmdTp, Cmd
from .memspec import Spec
from .pattern import PatternTp

RawPattern = namedtuple('RawPattern', ['length', 'commandsPre', 'commands'])


def patternGenBGI(BI, BC, rdOrWr, useBsPbgi):
    """
    Generate a read or write memory pattern. Uses bank-scheduling or
    bank-scheduling with pairwise bank-group interleaving.

    Args:
    BI -- The number of banks interleaved (integer)
    BC -- The number of bursts per bank (integer)
    rdOrWr -- CmdTp.RD or CmdTp.WR (member of BaseCmd class)
    useBsPbgi -- When True, use bank-group interleaving (bool)
    """
    BGi = 2 if useBsPbgi and BI > 1 else 1
    P = []  # The pattern
    for bg in range(0, int(BI / BGi)):
        for burst in range(0, BC):
            for offset in range(0, BGi):
                bnk = bg * BGi + offset
                P = addActAndRw(bnk, rdOrWr, burst, P)
    PWPre = list(P)
    for bnk in range(0, BI):
        preCyc = earliest(Cmd(CmdTp.PRE, bnk, 0), P)
        PWPre.append(Cmd(CmdTp.PRE, bnk, preCyc))

    pattLen = makeRepeatable(P, PWPre)

    P = annotateAutoPre(P)
    P = sorted(P, key=lambda c: c.cycle)
    PWPre = sorted(PWPre, key=lambda c: c.cycle)

    return RawPattern(pattLen, PWPre, P)


def addActAndRw(bnk, rdOrWr, burst, P):
    rw = Cmd(rdOrWr, bnk, 0)
    rwCyc = earliest(rw, P)
    if burst == 0:
        """The first burst to a bank needs an act."""
        P, rwCyc = addAct(rw, rwCyc, P)
    return P + [Cmd(rdOrWr, bnk, rwCyc)]


def addAct(rw, rwCc, P):
    """Insert an ACT in the schedule, ALAP, but in time for the read or write command."""
    act = Cmd(CmdTp.ACT, rw.bank, 0)
    lb = earliest(act, P)
    lb = lb + remainingFawCyclesAt(lb, P)

    while True:
        """Create the list of free cycles s, starting at lb, up to the final
        cycle where we can place the act command."""
        s = [i for i in range(lb, rwCc - d(act, rw) + 1) if len([c for c in P if c.cycle == i]) == 0]
        if len(s) != 0:
            """There is an empty cycle. Select the largest one, and place the ACT"""
            P.append(Cmd(CmdTp.ACT, rw.bank, max(s)))
            return P, rwCc
        rwCc = rwCc + 1


def makeRepeatable(P, PWPre):
    """Add NOPs to PWPre until P can be repeated after it w/o violating constraints"""

    """First resolve simple cmd-to-cmd constraints"""
    plen = maxCmdCycle(P) + 1
    for cmd_b in P:
        plen = max(plen, earliest(cmd_b, PWPre) - cmd_b.cycle)

    """Resolve FAW constraints"""
    acts = [cmd.cycle for cmd in P if cmd.cmdType == CmdTp.ACT]
    while not fawSatisfiedAcross(plen, Spec.FAW, acts):
        plen += 1
    return plen


def earliest(cmd_b, P):
    """
    Returns the earliest cycle at which a command cmd_b may be scheduled, given
    the location of the commands in the (partial) pattern P.
    """
    return max([cmd_a.cycle + d(cmd_a, cmd_b) for cmd_a in P] + [0])


def d(in1, in2):
    """Returns the minimum number of cycles between the pair of input commands."""
    Inf = 100000  # A suitable abstraction of infinity
    minDist = Spec.lut.constraintVal(in1, in2)
    if minDist <= 1:
        minDist = -Inf
    return minDist


"""Helper functions:"""


def remainingFawCyclesAt(i, pattern):
    """The number of cycles required to move out of the current FAW window (may be 0)."""
    acts = [cmd.cycle for cmd in pattern if cmd.cmdType == CmdTp.ACT]
    if len(acts) >= 4:
        # (note: assumes acending ordering of acts by cycle)
        return max(0, Spec.FAW - (i - acts[-4]))
    return 0


def maxCmdCycle(pattern):
    """The last cycle in the pattern where there is an non-NOP command."""
    return max([cmd.cycle for cmd in pattern] + [0])


def actsInWindow(wrapAt, lb, ub, pattern, naw=4):
    nAct = 0
    for i in range(lb, ub):
        for act in pattern:
            if act == (i % wrapAt):
                nAct += 1
            if nAct > naw:
                return nAct

    return nAct


def fawSatisfiedAcross(pattLen, FAW, pattern, wrap=True):
    if FAW == 0 or pattLen == 0:
        return True

    if FAW < pattLen:
        # Need to check the FAW windows that span the
        # end of the pattern and the start of its next incarnation.
        lbRng = range(pattLen - FAW, pattLen + 1)
    else:
        # Faw >= pattLen. Check 1 single FAW window,
        # filled with a wrapping pattern.
        lbRng = range(0, 1)

    for lb in lbRng:
        if actsInWindow(pattLen, lb, lb + FAW, pattern) > 4:
            return False
    return True


def minPatternDistance(fromP, toP, fromLen):
    """
    Finds the smallest number of cycles (NOPs) that must be inserted between
    two patterns to satisfy all constraints spanning across them.
    """
    slen = 0
    for cmd_b in toP:
        slen = max(slen, earliest(cmd_b, fromP) - cmd_b.cycle - fromLen)

    return slen


def _refPattern(rdPatt, wrPatt, rdPattLen, wrPattLen):
    """Create the refresh pattern."""
    refPatt = [Cmd(CmdTp.REF, 0, 0)]
    prefix = max(minPatternDistance(rdPatt, refPatt, rdPattLen),
                 minPatternDistance(wrPatt, refPatt, wrPattLen))
    refPatt = [Cmd(CmdTp.REF, 0, prefix)]
    postfix = max(minPatternDistance(refPatt, rdPatt, prefix + 1),
                  minPatternDistance(refPatt, wrPatt, prefix + 1))
    return refPatt, prefix + 1 + postfix


def _rtwPattern(rdPatt, wrPatt, rdPattLen):
    return minPatternDistance(rdPatt, wrPatt, rdPattLen)


def _wtrPattern(rdPatt, wrPatt, wrPattLen):
    return minPatternDistance(wrPatt, rdPatt, wrPattLen)


def rtwPattern(ps):
    length = _rtwPattern(ps[PatternTp.RD].commandsPre,
                         ps[PatternTp.WR].commandsPre,
                         len(ps[PatternTp.RD]))
    return RawPattern(length, [], [])


def wtrPattern(ps):
    length = _wtrPattern(ps[PatternTp.RD].commandsPre,
                         ps[PatternTp.WR].commandsPre,
                         len(ps[PatternTp.WR]))
    return RawPattern(length, [], [])


def refPattern(ps):
    cmds, length = _refPattern(ps[PatternTp.RD].commandsPre,
                               ps[PatternTp.WR].commandsPre,
                               len(ps[PatternTp.RD]),
                               len(ps[PatternTp.WR]))
    return RawPattern(length, cmds, cmds)


def annotateAutoPre(P):
    lastRW = {}  # Last rd/wr command per bank
    for cmd in P:
        if cmd.cmdType in [CmdTp.RD, CmdTp.WR]:
            if cmd.bank in lastRW and cmd.cycle > lastRW[cmd.bank].cycle:
                lastRW[cmd.bank] = cmd
            else:
                lastRW[cmd.bank] = cmd

    for key, cmd in lastRW.items():
        cmd.autoPrechargeFlag = True
    return P


def rtwPatternCop(from_ps, to_ps0, to_ps1):
    """
    Conservative open-page rtw pattern
    """
    length0 = _rtwPattern(from_ps[PatternTp.RD].commandsPre,
                          to_ps0[PatternTp.WR].commandsPre,
                          len(from_ps[PatternTp.RD]))
    length1 = _rtwPattern(from_ps[PatternTp.RD].commandsPre,
                          to_ps1[PatternTp.WR].commandsPre,
                          len(from_ps[PatternTp.RD]))
    return RawPattern(max(length0, length1), [], [])


def wtrPatternCop(from_ps, to_ps0, to_ps1):
    """
    Conservative open-page wtr pattern
    """
    length0 = _wtrPattern(to_ps0[PatternTp.RD].commandsPre,
                          from_ps[PatternTp.WR].commandsPre,
                          len(from_ps[PatternTp.WR]))
    length1 = _wtrPattern(to_ps1[PatternTp.RD].commandsPre,
                          from_ps[PatternTp.WR].commandsPre,
                          len(from_ps[PatternTp.WR]))
    return RawPattern(max(length0, length1), [], [])
