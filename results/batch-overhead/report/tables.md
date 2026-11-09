# Batch function costs

Known first-seed cost diagnosis only.
Whole old measurement includes trainer setup/warm, observations and hashes.
Tree/context preparation is outside these function profiles and inside the stage cap.
Self times may be aggregated as instrumented work; cumulative times overlap.
The mean consumes a traversal generator: inclusive mean cost is not validation-only cost.
No EV/strength score, optimizer, new forecast or long-study admission.

## B1: top function self costs

| Function | Total calls | Self seconds | Inclusive seconds (overlap) |
|---|---:|---:|---:|
| cached_nodes.py:242 select | 406064 | 1.562493924 | 2.087957448 |
| row_policy.py:24 _policy_row | 342414 | 1.128498448 | 2.598317165 |
| ~:0 <method 'reduce' of 'numpy.ufunc' objects> | 1705652 | 0.916069513 | 0.916069513 |
| controlled_training.py:196 _apply | 67140 | 0.891955265 | 1.706519093 |
| mccfr.py:73 visit | 800059 | 0.792603378 | 6.515252835 |
| fromnumeric.py:86 _wrapreduction_any_all | 1265518 | 0.557412808 | 1.562095397 |
| cached_nodes.py:230 frozen | 342414 | 0.290966026 | 2.975434431 |
| fromnumeric.py:88 <dictcomp> | 1265518 | 0.282703661 | 0.282703661 |
| cached_nodes.py:58 child | 732935 | 0.185840838 | 0.226157460 |
| fromnumeric.py:2548 all | 707028 | 0.175956417 | 1.091447726 |
| ~:0 <method 'sum' of 'numpy.ndarray' objects> | 440134 | 0.170160181 | 0.473145130 |
| numerictypes.py:475 issubdtype | 406064 | 0.165470661 | 0.357882399 |
| fromnumeric.py:2436 any | 558490 | 0.129652998 | 0.776257086 |
| frozen_batches.py:102 _apply | 67140 | 0.126544352 | 1.842369421 |
| numerictypes.py:293 issubclass_ | 812128 | 0.125781441 | 0.176499873 |

## B4: top function self costs

| Function | Total calls | Self seconds | Inclusive seconds (overlap) |
|---|---:|---:|---:|
| frozen_batches.py:152 select | 405312 | 1.571083836 | 2.104282639 |
| ~:0 <method 'reduce' of 'numpy.ufunc' objects> | 2064383 | 1.023151306 | 1.023151306 |
| mccfr.py:73 visit | 800345 | 0.793340947 | 5.679416824 |
| frozen_batches.py:27 mean_updates | 16552 | 0.784954127 | 7.750723858 |
| row_policy.py:24 _policy_row | 225658 | 0.775177857 | 1.747793506 |
| fromnumeric.py:86 _wrapreduction_any_all | 1741101 | 0.735859658 | 1.934466091 |
| controlled_training.py:196 _apply | 16568 | 0.552733625 | 1.064730332 |
| fromnumeric.py:88 <dictcomp> | 1741101 | 0.281903780 | 0.281903780 |
| frozen_batches.py:140 frozen | 345222 | 0.273312748 | 2.112155625 |
| fromnumeric.py:2548 all | 1163912 | 0.268489346 | 1.563741864 |
| cached_nodes.py:58 child | 734137 | 0.187012422 | 0.227896060 |
| numerictypes.py:475 issubdtype | 405312 | 0.165480739 | 0.364410960 |
| ~:0 <method 'copy' of 'numpy.ndarray' objects> | 938142 | 0.148728487 | 0.148728487 |
| numerictypes.py:293 issubclass_ | 810624 | 0.131718611 | 0.182618117 |
| fromnumeric.py:2436 any | 577189 | 0.130027404 | 0.769240977 |

## B16: top function self costs

| Function | Total calls | Self seconds | Inclusive seconds (overlap) |
|---|---:|---:|---:|
| frozen_batches.py:152 select | 405846 | 1.524487743 | 2.056523574 |
| ~:0 <method 'reduce' of 'numpy.ufunc' objects> | 1635103 | 0.783037018 | 0.783037018 |
| mccfr.py:73 visit | 802291 | 0.771523432 | 4.819374295 |
| frozen_batches.py:27 mean_updates | 4228 | 0.731213644 | 6.794365421 |
| fromnumeric.py:86 _wrapreduction_any_all | 1402875 | 0.576771460 | 1.502266226 |
| row_policy.py:24 _policy_row | 134604 | 0.457822347 | 1.025254866 |
| controlled_training.py:196 _apply | 4244 | 0.326218933 | 0.636803013 |
| frozen_batches.py:140 frozen | 341239 | 0.235711676 | 1.347845529 |
| fromnumeric.py:2548 all | 973838 | 0.219585678 | 1.260479848 |
| fromnumeric.py:88 <dictcomp> | 1402875 | 0.218724579 | 0.218724579 |
| cached_nodes.py:58 child | 734643 | 0.178523946 | 0.217801664 |
| numerictypes.py:475 issubdtype | 405846 | 0.159277222 | 0.361111911 |
| numerictypes.py:293 issubclass_ | 811692 | 0.138230352 | 0.185956430 |
| ~:0 <method 'copy' of 'numpy.ndarray' objects> | 839122 | 0.131030666 | 0.131030666 |
| getlimits.py:178 __new__ | 811692 | 0.118914523 | 0.153240184 |

