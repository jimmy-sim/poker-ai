# Saved batch current-policy diagnosis

Known saved games only; no new training or policy changes.
All 216 current scores; 432 average scores reused; 1,728 fixed targets; 1,152 paired fixed contrasts.
Current minus average self gaps change both players; fixed targets keep opponents unchanged.
Fixed gains are unilateral; do not equate them to half-summed self exploitability.
All modes/seeds/opponents retained; shared trajectories are not independent samples.
No pure-variance causal or selected/default/fresh/global claim.

| Game | Encoding | Rule | Batch | Readout | Final exact (%pot) | Within | Extra |
|---|---|---|---:|---|---:|---:|---:|
| dev_low_oop | exact | clipped | 1 | current | 0.081503343 | 0.081503343 | 0.000000000 |
| dev_low_oop | exact | clipped | 1 | linear_average | 0.041479289 | 0.041479289 | 0.000000000 |
| dev_low_oop | exact | clipped | 1 | uniform_average | 0.063985144 | 0.063985144 | 0.000000000 |
| dev_low_oop | exact | clipped | 4 | current | 0.035522957 | 0.035522957 | 0.000000000 |
| dev_low_oop | exact | clipped | 4 | linear_average | 0.034903505 | 0.034903505 | 0.000000000 |
| dev_low_oop | exact | clipped | 4 | uniform_average | 0.054999334 | 0.054999334 | 0.000000000 |
| dev_low_oop | exact | clipped | 16 | current | 0.001923536 | 0.001923536 | 0.000000000 |
| dev_low_oop | exact | clipped | 16 | linear_average | 0.024035353 | 0.024035353 | 0.000000000 |
| dev_low_oop | exact | clipped | 16 | uniform_average | 0.034315432 | 0.034315432 | 0.000000000 |
| dev_low_oop | exact | signed | 1 | current | 0.000000000 | 0.000000000 | 0.000000000 |
| dev_low_oop | exact | signed | 1 | linear_average | 0.000000548 | 0.000000548 | 0.000000000 |
| dev_low_oop | exact | signed | 1 | uniform_average | 0.000696990 | 0.000696990 | 0.000000000 |
| dev_low_oop | exact | signed | 4 | current | 0.000000000 | 0.000000000 | 0.000000000 |
| dev_low_oop | exact | signed | 4 | linear_average | 0.000000070 | 0.000000070 | 0.000000000 |
| dev_low_oop | exact | signed | 4 | uniform_average | 0.000470454 | 0.000470454 | 0.000000000 |
| dev_low_oop | exact | signed | 16 | current | 0.000000000 | 0.000000000 | 0.000000000 |
| dev_low_oop | exact | signed | 16 | linear_average | 0.000000026 | 0.000000026 | 0.000000000 |
| dev_low_oop | exact | signed | 16 | uniform_average | 0.000484906 | 0.000484906 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | clipped | 1 | current | 0.016469839 | 0.016469839 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | clipped | 1 | linear_average | 0.029205034 | 0.029205034 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | clipped | 1 | uniform_average | 0.045405838 | 0.045405838 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | clipped | 4 | current | 0.012609599 | 0.012591997 | 0.000017602 |
| dev_low_oop | texture_range_q8_b8 | clipped | 4 | linear_average | 0.018723130 | 0.018723130 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | clipped | 4 | uniform_average | 0.029774449 | 0.029774449 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | clipped | 16 | current | 0.000000000 | 0.000000000 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | clipped | 16 | linear_average | 0.007948619 | 0.007808082 | 0.000140537 |
| dev_low_oop | texture_range_q8_b8 | clipped | 16 | uniform_average | 0.011609094 | 0.011339863 | 0.000269231 |
| dev_low_oop | texture_range_q8_b8 | signed | 1 | current | 0.000000000 | 0.000000000 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | signed | 1 | linear_average | 0.000122588 | 0.000122575 | 0.000000013 |
| dev_low_oop | texture_range_q8_b8 | signed | 1 | uniform_average | 0.000888257 | 0.000836530 | 0.000051726 |
| dev_low_oop | texture_range_q8_b8 | signed | 4 | current | 0.000000000 | 0.000000000 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | signed | 4 | linear_average | 0.000000009 | 0.000000009 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | signed | 4 | uniform_average | 0.000183178 | 0.000183178 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | signed | 16 | current | 0.000000000 | 0.000000000 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | signed | 16 | linear_average | 0.000000026 | 0.000000026 | 0.000000000 |
| dev_low_oop | texture_range_q8_b8 | signed | 16 | uniform_average | 0.000484899 | 0.000484899 | 0.000000000 |
| dev_medium_oop | exact | clipped | 1 | current | 9.312837882 | 9.312837882 | 0.000000000 |
| dev_medium_oop | exact | clipped | 1 | linear_average | 2.155253310 | 2.155253310 | 0.000000000 |
| dev_medium_oop | exact | clipped | 1 | uniform_average | 3.663433054 | 3.663433054 | 0.000000000 |
| dev_medium_oop | exact | clipped | 4 | current | 10.696074356 | 10.696074356 | 0.000000000 |
| dev_medium_oop | exact | clipped | 4 | linear_average | 2.199592635 | 2.199592635 | 0.000000000 |
| dev_medium_oop | exact | clipped | 4 | uniform_average | 3.622457160 | 3.622457160 | 0.000000000 |
| dev_medium_oop | exact | clipped | 16 | current | 11.178710524 | 11.178710524 | 0.000000000 |
| dev_medium_oop | exact | clipped | 16 | linear_average | 2.017614713 | 2.017614713 | 0.000000000 |
| dev_medium_oop | exact | clipped | 16 | uniform_average | 3.510727310 | 3.510727310 | 0.000000000 |
| dev_medium_oop | exact | signed | 1 | current | 30.590742310 | 30.590742310 | 0.000000000 |
| dev_medium_oop | exact | signed | 1 | linear_average | 0.236525087 | 0.236525087 | 0.000000000 |
| dev_medium_oop | exact | signed | 1 | uniform_average | 0.638878983 | 0.638878983 | 0.000000000 |
| dev_medium_oop | exact | signed | 4 | current | 30.172451323 | 30.172451323 | 0.000000000 |
| dev_medium_oop | exact | signed | 4 | linear_average | 0.382574458 | 0.382574458 | 0.000000000 |
| dev_medium_oop | exact | signed | 4 | uniform_average | 0.671321139 | 0.671321139 | 0.000000000 |
| dev_medium_oop | exact | signed | 16 | current | 36.321331934 | 36.321331934 | 0.000000000 |
| dev_medium_oop | exact | signed | 16 | linear_average | 0.262595207 | 0.262595207 | 0.000000000 |
| dev_medium_oop | exact | signed | 16 | uniform_average | 0.710718039 | 0.710718039 | 0.000000000 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 1 | current | 9.519792652 | 7.593282240 | 1.926510412 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 1 | linear_average | 2.501852107 | 1.811454079 | 0.690398028 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 1 | uniform_average | 3.525759064 | 2.918434470 | 0.607324594 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 4 | current | 7.875893933 | 5.650830715 | 2.225063218 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 4 | linear_average | 2.534472843 | 1.783077178 | 0.751395664 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 4 | uniform_average | 3.627102416 | 2.920584185 | 0.706518231 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 16 | current | 10.569077746 | 8.338636614 | 2.230441132 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 16 | linear_average | 2.479423497 | 1.483119578 | 0.996303918 |
| dev_medium_oop | texture_range_q8_b8 | clipped | 16 | uniform_average | 3.306968914 | 2.515778567 | 0.791190346 |
| dev_medium_oop | texture_range_q8_b8 | signed | 1 | current | 31.999117056 | 29.448281135 | 2.550835921 |
| dev_medium_oop | texture_range_q8_b8 | signed | 1 | linear_average | 4.354031565 | 0.243207295 | 4.110824270 |
| dev_medium_oop | texture_range_q8_b8 | signed | 1 | uniform_average | 2.664089052 | 0.372604718 | 2.291484334 |
| dev_medium_oop | texture_range_q8_b8 | signed | 4 | current | 28.011637274 | 25.086103911 | 2.925533363 |
| dev_medium_oop | texture_range_q8_b8 | signed | 4 | linear_average | 2.172683537 | 0.094214622 | 2.078468914 |
| dev_medium_oop | texture_range_q8_b8 | signed | 4 | uniform_average | 1.568496405 | 0.377025356 | 1.191471049 |
| dev_medium_oop | texture_range_q8_b8 | signed | 16 | current | 21.455738111 | 17.718600917 | 3.737137194 |
| dev_medium_oop | texture_range_q8_b8 | signed | 16 | linear_average | 3.553971423 | 0.103146786 | 3.450824637 |
| dev_medium_oop | texture_range_q8_b8 | signed | 16 | uniform_average | 1.653648849 | 0.395648391 | 1.258000458 |
