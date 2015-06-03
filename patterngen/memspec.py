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

__all__ = ['MemSpec', 'Spec', 'setMemSpec']


import os
import math
import xml.etree.ElementTree as ET

from .memconstraints import memconstraintsLut


class MemSpec(object):
    def __init__(self):
        self.clkPeriodNs = -1
        self.nbrOfBankGroups = 1

    def __repr__(self):
        out = []
        for key, val in sorted(self.__dict__.items()):
            out.append('%s: %s' % (key, val))
        return '\n'.join(out)

    @staticmethod
    def toCK(ns, period):
        # Magic: reduce the number of nanoseconds by 1% of a cycle before ceiling
        # This hopefully gets rid of the floating point inaccuracy artifacts
        return int(math.ceil(ns / period - 0.01*period))

    @classmethod
    def parse(cls, fname, memoryId='', BL=8, useExact=False):
        if not os.path.exists(fname):
            fname += '.xml'
            if not os.path.exists(fname):
                raise Exception('MemSpecParser could not find file "%s"\n' % fname)

        spec = cls()
        spec.AL = 0
        spec.path = fname
        with open(fname, 'r') as f:
            tree = ET.parse(f)
            root = tree.getroot()

            archParams = root.findall(".//memarchitecturespec/parameter")
            timeParams = root.findall(".//memtimingspec/parameter")

            typeParam = root.find(".//parameter[@id='memoryType']")
            spec.memory_type = typeParam.attrib['value']

            idParam = root.find(".//parameter[@id='memoryId']")
            spec.memory_id = idParam.attrib['value']

            clkParam = root.find(".//memtimingspec//parameter[@id='clkMhz']")
            if clkParam is not None and 'exact' in clkParam.attrib:
                spec.clkPeriodNs = float(clkParam.attrib['exact'])

            for param in archParams:
                attrs = param.attrib
                pid = attrs['id']
                if 'type' in attrs and attrs['type'] == 'string':
                    spec.__setattr__(pid, attrs['value'])
                else:
                    try:
                        spec.__setattr__(pid, int(attrs['value']))
                    except (ValueError, UnicodeEncodeError):
                        # try as string
                        spec.__setattr__(pid, attrs['value'])
                        pass

            # Setup the magic variables the 'eval' call might use:
            cc = spec.clkPeriodNs
            NE = -1
            ns = 1.0
            for param in timeParams:
                attrs = param.attrib
                pid = attrs['id']
                if useExact:
                    val = attrs['exact']
                    try:
                        """Evals the 'exact' expression from the xml file"""
                        res = eval(val)
                        spec.__setattr__(pid, MemSpec.toCK(res, spec.clkPeriodNs))
                    except:
                        print('In memspec, failed to parse value %s for param %s' % (val, pid))
                        continue
                else:
                    res = int(attrs['value'])
                    spec.__setattr__(pid, res)

        spec.BL = BL
        spec.dataRate = 2
        spec.burstCC = int(spec.BL / spec.dataRate)
        # Shorthand:
        spec.B = spec.burstCC

        try:
            spec.FAW = spec.LAW
        except:
            """ If LAW does not exist, then don't care about FAW either """
            try:
                if spec.FAW:
                    # Keep old value
                    pass
            except:
                spec.FAW = 1
            pass

        if spec.memory_type in ['DDR3']:
            try:
                if spec.CL:
                    spec.RL = spec.CL + spec.AL
            except:
                pass

            try:
                if spec.CWL:
                    spec.WL = spec.CWL + spec.AL
            except:
                pass
            assert spec.WL != 0
            assert spec.RL != 0

        if spec.memory_type in ['DDR4']:
            spec.WL = spec.CWL + spec.AL

        if spec.memory_type in ['LPDDR2', 'LPDDR3']:
            assert spec.AL == 0, "AL != 0. AL has to be 0 on a %s memory" % spec.memory_type

        if spec.memory_type == 'DDR2':
            spec.RL = spec.CL + spec.AL
            spec.WL = spec.RL - 1
            if spec.BL == 4:
                spec.RTW = 4
            elif spec.BL == 8:
                spec.RTW = 6
            else:
                assert False, "BL != 4 or 8. It has to be 4 or 8 on a DDR2 device."

        return spec


class Spec(object):
    """
    A minimalist memspec class. Used as a singleton.

    (Candidate for refactoring)
    """
    lut = None
    numBankGroups = 1
    FAW = 1
    spec = None


def setMemSpec(memspecXmlFile, useExact=False):
    """
    Initialize the singleton Spec object.

    Args:
    - useExact: use the values in the "exact" attribute of the memspec file
                instead of the "value" attribute. The spec will be printed
                after parsing such that you can see the timings that were used.
    """
    spec = MemSpec.parse(memspecXmlFile, useExact=useExact)
    Spec.spec = spec
    if useExact:
        print(spec)
    Spec.numBankGroups = spec.nbrOfBankGroups
    Spec.lut = memconstraintsLut(spec)
    Spec.FAW = spec.FAW
