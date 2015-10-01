# pypatterngen - The python-based SDRAM patterns generator

Memory patterns are sequences of SDRAM commands that are statically computed at design time and dynamically scheduled at run time. A description of how such patterns are used is found in the article: *Power/Performance Trade-offs in Real-Time SDRAM Command Scheduling in IEEE Transactions on Computers* ([ieeexplore](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=7169527)). The SDRAM controller in the [CompSOC](http://www.compsoc.eu) platform executes these memory patterns, enabling us to give (real-time) guarantees on worst-case bandwidth and worst-case response time.

If you use or wish to cite these scripts for a publication, then please use use this [reference](#citing).

## Usage

```
usage: make_patterns.py [-h] --BI BI --BC BC [--BGI {0,1}] --memspec MEMSPEC

Create a memory pattern

optional arguments:
  -h, --help         show this help message and exit
  --BI BI            Number of banks interleaved
  --BC BC            Number of bursts per bank
  --BGI {0,1}        Use bank-group interleaving (DDR4 only)
  --memspec MEMSPEC  Memory specification xml file to use.
```

The script generates memory patterns for DDR2/3/4 and LPDDR1/2/3 memories, and is written in python. It requires at least python 3.4 (since it uses Enum datatypes). We have only tested it on an Ubuntu 14.04 machine. After cloning the repo, the `make_patterns.py` script can be used to quickly generate patterns (without having to figure out the entire API). Its 3 required arguments are:

 * `--BI`: The number of banks to interleave over
 * `--BC`: The number of bursts per bank
 * `--memspec`: An xml file that contains a specification of the memory timings. We have provided 12 samples we often use. Running:

```bash
./make_patterns.py --BI 2 --BC 4 --memspec memspecs/DDR4/MICRON_512MB_DDR4-1866_8bit_A.xml
```

should yield:

```
Generating patterns for a MICRON_512MB_DDR4-1866_8bit_A memory using BI 2, BC 4
Worst-case bandwidth: 834.260 MB/s
PatternTp.WR (AP): length: 69
Commands: A0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-W0-N0-N0-N0-N0-W0-A1-N0-N0-N0-W0-N0-N0-N0-N0-W0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-W1-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0

PatternTp.RD (AP): length: 48
Commands: A0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-N0-R0-N0-N0-N0-N0-R0-A1-N0-N0-N0-R0-N0-N0-N0-N0-R0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1-N0-N0-N0-N0-R1

PatternTp.RTW (AP): length: 0
Commands: 

PatternTp.WTR (AP): length: 0
Commands: 
```

The *AP* patterns contain activate and precharge commands, and are implement a close-page policy. Worst-case bandwidth is calculated based on this publication: [ieeexplore](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=5591843), under the assumption that the data efficiency is 1, i.e. the request size is equal to the atom size (BI * BC * BL * memory_width).

The optional argument:
 * `--BGI`: Use bank-group interleaving (DDR4 only)
may be set to 1 to enable pairwise bank-group interleaving (PBGI), which may generate shorter schedules for DDR4 memories, since it avoids the long CCD_L constraint by interleaving bursts across bank groups.

## Development
The purpose of these scripts is to be more user-friendly, and easier to maintain than the originals that were published with this article. The main differences with respect to that version are:

 * The implementation is cleaner and more pythonic. One single representation of a pattern is shared by all functions.
 * Integration with the wrapper around [DRAMPower 3.1](https://github.com/ravenrd/DRAMPower) is currently not available. In the future, these scripts should hook into the latest version of DRAMPower.
 * ILP generating functionality is removed. The GLPK wrapper we originally used was quite old and only worked on older machines. A more direct mapper to the CPLEX input files is preferable if we decide to re-implement it.
 * Conservative open-page patterns can be generated, related to the paper Goossens, Sven; Akesson, Benny; Goossens, Kees, "Conservative open-page policy for mixed time-criticality memory controllers," in Design, Automation & Test in Europe Conference & Exhibition (DATE), 2013 , vol., no., pp.525-530, 18-22 March 2013
doi: 10.7873/DATE.2013.118 ([pdf](http://www.es.ele.tue.nl/~sgoossens/pub/goossens13-date.pdf), [ppt](http://www.es.ele.tue.nl/~sgoossens/pub/goossens13-date_presentation.pdf), [ieeexplore](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=6513564))

## Citing
When citing or using the data sets or scripts, please use this reference:
```
@ARTICLE{7169527, 
author={Goossens, S. and Chandrasekar, K. and Akesson, B. and Goossens, K.}, 
journal={Computers, IEEE Transactions on}, 
title={Power/Performance Trade-offs in Real-Time SDRAM Command Scheduling}, 
year={2015}, 
volume={PP}, 
number={99}, 
pages={1-1}, 
keywords={Bandwidth;Performance evaluation;Real-time systems;SDRAM;Scheduling algorithms;Timing;Memory control and access,;Real-time and embedded systems;dynamic random access memory (DRAM),}, 
doi={10.1109/TC.2015.2458859}, 
ISSN={0018-9340}, 
month={},}
```

## Other related publications

 * **On the conservative open-page policy**: *Goossens, Sven; Akesson, Benny; Goossens, Kees, "Conservative open-page policy for mixed time-criticality memory controllers," in Design, Automation & Test in Europe Conference & Exhibition (DATE), 2013, pp.525-530, doi: 10.7873/DATE.2013.118* ([ieeexplore](http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6513564&isnumber=6513446))
 * **On the implementation of the memory controller back-end**: *Goossens, S.; Kuijsten, J.; Akesson, B.; Goossens, K., "A reconfigurable real-time SDRAM controller for mixed time-criticality systems," in Hardware/Software Codesign and System Synthesis (CODES+ISSS), 2013 International Conference on, pp.1-10, 
doi: 10.1109/CODES-ISSS.2013.6658989* ([ieeexplore](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=6658989))
 * **On the real-time analysis of memory patterns**: *Akesson, B.; Hayes, W.; Goossens, K., "Classification and Analysis of Predictable Memory Patterns," in Embedded and Real-Time Computing Systems and Applications (RTCSA), 2010 IEEE 16th International Conference on , pp.367-376 doi: 10.1109/RTCSA.2010.35* ([ieeexplore](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=5591843))
 * **A high-level overview of the memory controller including front-end**: *Akesson, B.; Goossens, K., "Architectures and modeling of predictable memory controllers for improved system integration," in Design, Automation & Test in Europe Conference & Exhibition (DATE), 2011 , pp.1-6, doi: 10.1109/DATE.2011.5763145* ([ieeexplore](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=5763145))
 * **CompSOC platform overview**: *Kees Goossens, Arnaldo Azevedo, Karthik Chandrasekar, Manil Dev Gomony, Sven Goossens, Martijn Koedam, Yonghui Li, Davit Mirzoyan, Anca Molnos, Ashkan Beyranvand Nejad, Andrew Nelson, and Shubhendu Sinha, "Virtual Execution Platforms for Mixed-Time-Criticality Systems: The CompSOC Architecture and Design Flow", ACM SIGBED Volume 10(3), Oct 2013.* ([pdf](http://www.es.ele.tue.nl/~kgoossens/2013-sigbed.pdf), [mirror](http://sigbed.seas.upenn.edu/archives/2013-10/crts2012_submission_5.pdf))

 


