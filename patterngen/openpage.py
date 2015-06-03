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

import copy
from .cmd import CmdTp, Cmd
from .patterngen import earliest, addActAndRw, annotateAutoPre, minPatternDistance, RawPattern, maxCmdCycle


def firstFreeCycle(cycle, P):
    """Find the first empty cycle in pattern P that is >= cycle"""
    while len([cmd for cmd in P if cmd.cycle == cycle]) != 0:
        cycle += 1
    return cycle


def getFirstPre(P):
    Inf = 100000  # A suitable abstraction of infinity
    cc = Inf
    idex = -1
    for i, cmd in enumerate(P):
        if cmd.autoPrechargeFlag or cmd.cmdType == CmdTp.PRE:
            if cmd.cycle < cc:
                cc = cmd.cycle
                idex = i
    assert(idex != -1)
    return idex


def toAnp(P):
    """
    Convert an AP pattern to an ANP pattern

    Copies pattern P (in AP mode, i.e. containing ACT and (auto) PRE commands).
    It then removes the precharges, and all trailing NOPs after the final RD/WR
    command, yielding the ANP pattern.
    """
    P = copy.deepcopy(P)
    # Remove all precharges:
    P = [cmd for cmd in P if cmd.cmdType != CmdTp.PRE]
    for cmd in P:
        cmd.autoPrechargeFlag = False

    # Chop trailing NOPs

    # Find the first rd/wr in the NA* schedule
    # This ensures we compare with the right bank when executing earliest()
    smallestCc = min([cmd.cycle for cmd in P if cmd.cmdType in [CmdTp.WR, CmdTp.RD]])
    for cmd in P:
        if cmd.cycle == smallestCc:
            smallestRdWrCmd = cmd

    # Find the earliest possible location of a next RD/WR after this pattern.
    newLen = earliest(smallestRdWrCmd, P)
    return RawPattern(newLen, P, P)


def patternGenNap(BI, BC, rdOrWr, useBsPbgi, ANP, ANPLength):
    """
    Create NAP pattern based on ANP pattern, by concatenating a new set of bursts
    to it, and then chopping off the ANP-part.

    A large portion of this code duplicates the patternGenBGI function, so
    it is a target for refactoring.
    """
    BGi = 2 if useBsPbgi and BI > 1 else 1
    P = copy.deepcopy(ANP)  # The ANP pattern is the base of this pattern
    notTheFirstBurst = 1  # Causes addActAndRw() to never add an ACT command
    for bg in range(0, int(BI / BGi)):
        for burst in range(0, BC):
            for offset in range(0, BGi):
                bnk = bg * BGi + offset
                P = addActAndRw(bnk, rdOrWr, notTheFirstBurst, P)

    # Annotate the precharges:
    PWPre = list(P)
    for bnk in range(0, BI):
        preCyc = earliest(Cmd(CmdTp.PRE, bnk, 0), P)
        PWPre.append(Cmd(CmdTp.PRE, bnk, preCyc))

    # We should be able to use the ANP pattern after the NAP pattern:
    dist = minPatternDistance(PWPre, ANP, maxCmdCycle(P) + 1)
    pattLen = maxCmdCycle(P) + 1 + dist

    # Separate ANP from NAP patterns
    P = [cmd for cmd in P if cmd.cycle >= ANPLength]
    PWPre = [cmd for cmd in PWPre if cmd.cycle >= ANPLength]
    for cmd in PWPre:
        # Note that P and PWPre share Cmd objects, and thus we only process the latter.
        cmd.cycle = cmd.cycle - ANPLength

    pattLen = pattLen - ANPLength

    # Finalize
    P = annotateAutoPre(P)
    P = sorted(P, key=lambda c: c.cycle)
    PWPre = sorted(PWPre, key=lambda c: c.cycle)

    return RawPattern(pattLen, PWPre, P)


def stretchPrecharge(pattLen, P, nextPattern):
    """
    Move the precharges towards the end of the pattern, while ensuring nextPattern
    can still be scheduled after it.
    """
    P = copy.deepcopy(P)
    while True:
        Pbackup = copy.deepcopy(P)
        firstPre = P[getFirstPre(P)]

        if firstPre.autoPrechargeFlag:
            # Try to convert
            preCC = firstFreeCycle(earliest(Cmd(CmdTp.PRE, firstPre.bank, 0), P), P)
            P.append(Cmd(CmdTp.PRE, firstPre.bank, preCC))
            firstPre.autoPrechargeFlag = False
        else:
            # Try to move
            preCC = firstFreeCycle(firstPre.cycle + 1, P)
            firstPre.cycle = preCC

        # Are we still within the bounds of the pattern?
        if preCC >= pattLen or minPatternDistance(P, nextPattern, pattLen) != 0:
            # print('Precharge conversion on %s would increase pattern length. Returning...' % firstPre)
            return Pbackup

        # print('\nMoved precharge %s forward to %d.' % (firstPre, preCC))
        P = sorted(P, key=lambda c: c.cycle)
