# pypatterngen - The python-based SDRAM patterns generator

Memory patterns are sequences of SDRAM commands that are statically computed at design time and dynamically scheduled at run time. A description of how such patterns are used is found in this article: [Goossens, S.; Chandrasekar, K.; Akesson, B.; Goossens, K., "Power/Performance Trade-offs in Real-Time SDRAM Command Scheduling," in Computers, IEEE Transactions on , vol.PP, no.99, pp.1-1
doi: 10.1109/TC.2015.2458859](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?reload=true&arnumber=7169527).

The purpose of these scripts is to be more user-friendly, and easier to maintain than the originals that were published with the article. The main differences with respect to that version are:

 * The implementation is cleaner and more pythonic. One single representation of a pattern is shared by all functions.
 * Integration with a wrapper around DRAMPower is currently not available. In the future, these scripts should hook into the latest version of DRAMPower.
 * ILP generating functionality is removed. The GLPK wrapper was quite old, and a more direct mapper to the CPLEX input files is preferable.
 * Conservative open-page patterns can be generated, related to the paper [Goossens, Sven; Akesson, Benny; Goossens, Kees, "Conservative open-page policy for mixed time-criticality memory controllers," in Design, Automation & Test in Europe Conference & Exhibition (DATE), 2013 , vol., no., pp.525-530, 18-22 March 2013
doi: 10.7873/DATE.2013.118](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=6513564)

When citing or using the data sets or scripts, please use the following reference:

```
@ARTICLE{7169527, 
author={Goossens, S. and Chandrasekar, K. and Akesson, B. and Goossens, K.}, 
journal={Computers, IEEE Transactions on}, 
title={Power/Performance Trade-offs in Real-Time SDRAM Command Scheduling}, 
year={2015}, 
volume={PP}, 
number={99}, 
pages={1-1}, 
keywords={Bandwidth;Bismuth;Performance evaluation;Real-time systems;SDRAM;Scheduling algorithms;Timing;Memory control and access,;Real-time and embedded systems;dynamic random access memory (DRAM),}, 
doi={10.1109/TC.2015.2458859}, 
ISSN={0018-9340}, 
month={},}
```

## Usage

```bash
usage: make_patterns.py [-h] --BI BI --BC BC [--BGI BGI] --memspec MEMSPEC

Create a memory pattern

optional arguments:
  -h, --help         show this help message and exit
  --BI BI            Number of banks interleaved
  --BC BC            Number of bursts per bank
  --BGI BGI          Use bank-group interleaving (DDR4 only)
  --memspec MEMSPEC  Memory specification xml file to use.
```

The script generates memory patterns for DDR2/3/4 and LPDDR1/2/3 memories, and is written in python. It requires at least python 3.4 (since it uses Enum datatypes). We have only tested it on an Ubuntu 14.04 machine. After cloning the repo, the make_patterns.py script can be used to quickly generate patterns (without having to figure out the entire API). Its 3 required arguments are:

--BI: The number of banks to interleave over
--BC: The number of bursts per bank
--memspec: An xml file that contains a specification of the memory timings. We have provided 12 samples we often use. Running:

```bash
./make_patterns.py --BI 2 --BC 4 --memspec memspecs/DDR4/MICRON_512MB_DDR4-1866_8bit_A.xml 
```

should yield:

```
Generating patterns for a MICRON_512MB_DDR4-1866_8bit_A memory using BI 2, BC 4
PatternTp.WR (AP) length: 69
Commands: A0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-W0-N0-N0-N0-N0-W0-A1-N0-N0-N0-W0-N0-N0-N0-N0-W0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0

PatternTp.RD (AP) length: 48
Commands: A0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-R0-N0-N0-N0-N0-R0-A1-N0-N0-N0-R0-N0-N0-N0-N0-R0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1

PatternTp.RD (ANP) length: 51
Commands: A0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-R0-N0-N0-N0-N0-R0-A1-N0-N0-N0-R0-N0-N0-N0-N0-R0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0

PatternTp.RD (NAP) length: 35
Commands: R0-N0-N0-N0-N0-R0-N0-N0-N0-N0-R0-N0-N0-N0-N0-R0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1

PatternTp.WR (ANP) length: 51
Commands: A0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-W0-N0-N0-N0-N0-W0-A1-N0-N0-N0-W0-N0-N0-N0-N0-W0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0

PatternTp.WR (NAP) length: 56
Commands: W0-N0-N0-N0-N0-W0-N0-N0-N0-N0-W0-N0-N0-N0-N0-W0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0
```

The *AP* patterns contain activate and precharge commands, and are implement a close-page policy. The remaining patterns are related to the conservative open-page policy.