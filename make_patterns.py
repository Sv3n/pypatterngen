#!/usr/bin/env python3.4
"""
Command-line pattern generation example.
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

from patterngen import setMemSpec, PatternSet, Pattern, Spec, PatternTp, CmdTp
from patterngen import rtwPattern, wtrPattern, refPattern
from patterngen import makeOpenPage, patternGenBGI
import argparse


def parseArguments():
    parser = argparse.ArgumentParser(description='Create a memory pattern')
    parser.add_argument('--BI', dest='BI', type=int, required=True, help='Number of banks interleaved')
    parser.add_argument('--BC', dest='BC', type=int, required=True, help='Number of bursts per bank')
    parser.add_argument('--BGI', dest='BGI', type=int, required=False, default=0, choices=[0, 1], help='Use bank-group interleaving (DDR4 only)')
    parser.add_argument('--memspec', dest='memspec', type=str, required=True, help='Memory specification xml file to use.')
    return parser.parse_args()


def canUseBsPbgi(bi, bc, bgi):
    """
    Return true when bgi is true, and when it makes sense to use it.
    """
    if Spec.spec.memory_type == 'DDR4' and bi > 1 and bc > 1:
        return bgi
    return False


def addAuxPatterns(ps):
    """
    Add the read-to-write, write-to-read and refresh patterns to pattern set ps.
    """
    tp = PatternTp.RTW
    ps[tp] = Pattern(tp, rtwPattern(ps))
    tp = PatternTp.WTR
    ps[tp] = Pattern(tp, wtrPattern(ps))
    tp = PatternTp.REF
    ps[tp] = Pattern(tp, refPattern(ps))


def patternSet(memspec, bi, bc, useBsPbgi):
    """Create a pattern set based on the given BI/BC/BGI parameters"""

    """Create a new PatternSet object"""
    ps = PatternSet(bi, bc, useBsPbgi)

    print("Generating patterns for a {memory} memory using BI {BI}, BC {BC}".format(memory=Spec.spec.memory_id, BI=bi, BC=bc))

    """Fill it with rd/wr patterns"""
    for rw in [CmdTp.RD, CmdTp.WR]:
        p = Pattern(rw, patternGenBGI(BI=bi, BC=bc, rdOrWr=rw, useBsPbgi=useBsPbgi))
        ps[PatternTp.fromCmdTp(rw)] = p

    """Add auxiliary patterns"""
    addAuxPatterns(ps)

    return ps


def main():
    args = parseArguments()
    """Load memory specification. It is shared by all the patterngen tools."""
    setMemSpec(args.memspec)
    """Only use bank-group interleaving when there is something to interleave"""
    useBsPbgi = canUseBsPbgi(args.BI, args.BC, args.BGI)

    """Create a (close-page) pattern set and print it"""
    ps = patternSet(args.memspec, args.BI, args.BC, useBsPbgi)
    print('Worst-case bandwidth: {worst_case_bandwidth:.3f} MB/s'.format(worst_case_bandwidth=ps.worstCaseBandwidth()))
    for tp in [PatternTp.WR, PatternTp.RD, PatternTp.RTW, PatternTp.WTR]:
        print("{tp} (AP): {pattern_set}".format(tp=str(tp), pattern_set=ps[tp]))


if __name__ == '__main__':
    main()
