# Complete two-axis comparisons

All three fixed seeds per row; descriptive means, not confidence bounds.
Delta is B1 minus batch in percentage points of initial pot; lower self exploitability is better.
Same-work B1 final endpoints are reused for both batch targets. Readouts share trajectories.

| Game/encoding/rule/readout | Batch | Axis | B1 mean | Batch mean | Delta | Seed delta min–max | B1/batch work ratio |
|---|---:|---|---:|---:|---:|---|---:|
|dev_low_oop / exact / clipped / current|4|same_updates|0.042119|0.035523|0.006596|-0.047017 to 0.040626|0.251634|
|dev_low_oop / exact / clipped / current|4|same_work_label|0.081503|0.035523|0.045980|-0.022189 to 0.111587|0.999996|
|dev_low_oop / exact / clipped / current|16|same_updates|0.201093|0.001924|0.199169|0.133612 to 0.277265|0.063647|
|dev_low_oop / exact / clipped / current|16|same_work_label|0.081503|0.001924|0.079580|0.026087 to 0.141103|0.999978|
|dev_low_oop / exact / clipped / linear_average|4|same_updates|0.084673|0.034904|0.049769|0.049511 to 0.050043|0.251634|
|dev_low_oop / exact / clipped / linear_average|4|same_work_label|0.041479|0.034904|0.006576|0.006353 to 0.006762|0.999996|
|dev_low_oop / exact / clipped / linear_average|16|same_updates|0.173569|0.024035|0.149534|0.145712 to 0.152359|0.063647|
|dev_low_oop / exact / clipped / linear_average|16|same_work_label|0.041479|0.024035|0.017444|0.016500 to 0.018964|0.999978|
|dev_low_oop / exact / clipped / uniform_average|4|same_updates|0.131801|0.054999|0.076802|0.074678 to 0.078239|0.251634|
|dev_low_oop / exact / clipped / uniform_average|4|same_work_label|0.063985|0.054999|0.008986|0.008595 to 0.009690|0.999996|
|dev_low_oop / exact / clipped / uniform_average|16|same_updates|0.273952|0.034315|0.239636|0.229877 to 0.244627|0.063647|
|dev_low_oop / exact / clipped / uniform_average|16|same_work_label|0.063985|0.034315|0.029670|0.027144 to 0.031970|0.999978|
|dev_low_oop / exact / signed / current|4|same_updates|0.000000|0.000000|0.000000|0.000000 to 0.000000|0.246266|
|dev_low_oop / exact / signed / current|4|same_work_label|0.000000|0.000000|0.000000|0.000000 to 0.000000|0.999997|
|dev_low_oop / exact / signed / current|16|same_updates|0.000000|0.000000|0.000000|0.000000 to 0.000000|0.063225|
|dev_low_oop / exact / signed / current|16|same_work_label|0.000000|0.000000|0.000000|0.000000 to 0.000000|0.999992|
|dev_low_oop / exact / signed / linear_average|4|same_updates|0.000009|0.000000|0.000009|-0.000000 to 0.000024|0.246266|
|dev_low_oop / exact / signed / linear_average|4|same_work_label|0.000001|0.000000|0.000000|-0.000000 to 0.000001|0.999997|
|dev_low_oop / exact / signed / linear_average|16|same_updates|0.000140|0.000000|0.000140|0.000001 to 0.000381|0.063225|
|dev_low_oop / exact / signed / linear_average|16|same_work_label|0.000001|0.000000|0.000001|-0.000000 to 0.000001|0.999992|
|dev_low_oop / exact / signed / uniform_average|4|same_updates|0.002794|0.000470|0.002324|-0.000430 to 0.004847|0.246266|
|dev_low_oop / exact / signed / uniform_average|4|same_work_label|0.000697|0.000470|0.000227|-0.000987 to 0.001123|0.999997|
|dev_low_oop / exact / signed / uniform_average|16|same_updates|0.011179|0.000485|0.010694|0.002279 to 0.019535|0.063225|
|dev_low_oop / exact / signed / uniform_average|16|same_work_label|0.000697|0.000485|0.000212|-0.000312 to 0.000760|0.999992|
|dev_low_oop / texture_range_q8_b8 / clipped / current|4|same_updates|0.043105|0.012610|0.030495|-0.037024 to 0.096324|0.251560|
|dev_low_oop / texture_range_q8_b8 / clipped / current|4|same_work_label|0.016470|0.012610|0.003860|-0.004136 to 0.016095|0.999999|
|dev_low_oop / texture_range_q8_b8 / clipped / current|16|same_updates|0.113161|0.000000|0.113161|0.101646 to 0.131453|0.064064|
|dev_low_oop / texture_range_q8_b8 / clipped / current|16|same_work_label|0.016470|0.000000|0.016470|0.000420 to 0.032888|0.999986|
|dev_low_oop / texture_range_q8_b8 / clipped / linear_average|4|same_updates|0.060142|0.018723|0.041419|0.041009 to 0.042181|0.251560|
|dev_low_oop / texture_range_q8_b8 / clipped / linear_average|4|same_work_label|0.029205|0.018723|0.010482|0.010416 to 0.010540|0.999999|
|dev_low_oop / texture_range_q8_b8 / clipped / linear_average|16|same_updates|0.127343|0.007949|0.119395|0.118667 to 0.120736|0.064064|
|dev_low_oop / texture_range_q8_b8 / clipped / linear_average|16|same_work_label|0.029205|0.007949|0.021256|0.020656 to 0.022081|0.999986|
|dev_low_oop / texture_range_q8_b8 / clipped / uniform_average|4|same_updates|0.094050|0.029774|0.064276|0.063929 to 0.064910|0.251560|
|dev_low_oop / texture_range_q8_b8 / clipped / uniform_average|4|same_work_label|0.045406|0.029774|0.015631|0.015019 to 0.016091|0.999999|
|dev_low_oop / texture_range_q8_b8 / clipped / uniform_average|16|same_updates|0.197426|0.011609|0.185816|0.181855 to 0.188295|0.064064|
|dev_low_oop / texture_range_q8_b8 / clipped / uniform_average|16|same_work_label|0.045406|0.011609|0.033797|0.033457 to 0.034033|0.999986|
|dev_low_oop / texture_range_q8_b8 / signed / current|4|same_updates|0.042088|0.000000|0.042088|0.000000 to 0.126263|0.271781|
|dev_low_oop / texture_range_q8_b8 / signed / current|4|same_work_label|0.000000|0.000000|0.000000|0.000000 to 0.000000|0.999998|
|dev_low_oop / texture_range_q8_b8 / signed / current|16|same_updates|0.042088|0.000000|0.042088|0.000000 to 0.126263|0.068323|
|dev_low_oop / texture_range_q8_b8 / signed / current|16|same_work_label|0.000000|0.000000|0.000000|0.000000 to 0.000000|0.999991|
|dev_low_oop / texture_range_q8_b8 / signed / linear_average|4|same_updates|0.000571|0.000000|0.000571|-0.000000 to 0.001701|0.271781|
|dev_low_oop / texture_range_q8_b8 / signed / linear_average|4|same_work_label|0.000123|0.000000|0.000123|-0.000000 to 0.000367|0.999998|
|dev_low_oop / texture_range_q8_b8 / signed / linear_average|16|same_updates|0.003714|0.000000|0.003714|0.000000 to 0.010931|0.068323|
|dev_low_oop / texture_range_q8_b8 / signed / linear_average|16|same_work_label|0.000123|0.000000|0.000123|-0.000000 to 0.000367|0.999991|
|dev_low_oop / texture_range_q8_b8 / signed / uniform_average|4|same_updates|0.003209|0.000183|0.003026|-0.000050 to 0.006438|0.271781|
|dev_low_oop / texture_range_q8_b8 / signed / uniform_average|4|same_work_label|0.000888|0.000183|0.000705|-0.000243 to 0.001692|0.999998|
|dev_low_oop / texture_range_q8_b8 / signed / uniform_average|16|same_updates|0.011561|0.000485|0.011076|0.000543 to 0.021924|0.068323|
|dev_low_oop / texture_range_q8_b8 / signed / uniform_average|16|same_work_label|0.000888|0.000485|0.000403|-0.000420 to 0.001329|0.999991|
|dev_medium_oop / exact / clipped / current|4|same_updates|26.913719|10.696074|16.217645|5.019946 to 26.087708|0.257786|
|dev_medium_oop / exact / clipped / current|4|same_work_label|9.312838|10.696074|-1.383236|-4.404056 to 3.464213|0.999999|
|dev_medium_oop / exact / clipped / current|16|same_updates|40.579409|11.178711|29.400699|25.154247 to 34.756190|0.072416|
|dev_medium_oop / exact / clipped / current|16|same_work_label|9.312838|11.178711|-1.865873|-8.551428 to 1.645832|0.999961|
|dev_medium_oop / exact / clipped / linear_average|4|same_updates|7.551939|2.199593|5.352346|4.928544 to 6.021999|0.257786|
|dev_medium_oop / exact / clipped / linear_average|4|same_work_label|2.155253|2.199593|-0.044339|-0.219520 to 0.048572|0.999999|
|dev_medium_oop / exact / clipped / linear_average|16|same_updates|17.018368|2.017615|15.000753|13.999037 to 15.718906|0.072416|
|dev_medium_oop / exact / clipped / linear_average|16|same_work_label|2.155253|2.017615|0.137639|-0.014130 to 0.228754|0.999961|
|dev_medium_oop / exact / clipped / uniform_average|4|same_updates|10.241234|3.622457|6.618777|6.210744 to 7.117188|0.257786|
|dev_medium_oop / exact / clipped / uniform_average|4|same_work_label|3.663433|3.622457|0.040976|-0.191170 to 0.207480|0.999999|
|dev_medium_oop / exact / clipped / uniform_average|16|same_updates|21.049734|3.510727|17.539007|16.208531 to 18.350167|0.072416|
|dev_medium_oop / exact / clipped / uniform_average|16|same_work_label|3.663433|3.510727|0.152706|-0.141494 to 0.410638|0.999961|
|dev_medium_oop / exact / signed / current|4|same_updates|28.887272|30.172451|-1.285179|-11.410913 to 5.589766|0.257149|
|dev_medium_oop / exact / signed / current|4|same_work_label|30.590742|30.172451|0.418291|-6.076115 to 13.067087|0.999999|
|dev_medium_oop / exact / signed / current|16|same_updates|48.016408|36.321332|11.695076|7.053481 to 14.263526|0.071170|
|dev_medium_oop / exact / signed / current|16|same_work_label|30.590742|36.321332|-5.730590|-24.194133 to 18.273183|0.999975|
|dev_medium_oop / exact / signed / linear_average|4|same_updates|1.119591|0.382574|0.737017|0.317688 to 1.145668|0.257149|
|dev_medium_oop / exact / signed / linear_average|4|same_work_label|0.236525|0.382574|-0.146049|-0.439646 to 0.039206|0.999999|
|dev_medium_oop / exact / signed / linear_average|16|same_updates|7.704919|0.262595|7.442324|6.880972 to 7.824357|0.071170|
|dev_medium_oop / exact / signed / linear_average|16|same_work_label|0.236525|0.262595|-0.026070|-0.108511 to 0.052608|0.999975|
|dev_medium_oop / exact / signed / uniform_average|4|same_updates|2.216797|0.671321|1.545476|1.534883 to 1.551308|0.257149|
|dev_medium_oop / exact / signed / uniform_average|4|same_work_label|0.638879|0.671321|-0.032442|-0.085373 to -0.002788|0.999999|
|dev_medium_oop / exact / signed / uniform_average|16|same_updates|9.580535|0.710718|8.869817|8.455318 to 9.090548|0.071170|
|dev_medium_oop / exact / signed / uniform_average|16|same_work_label|0.638879|0.710718|-0.071839|-0.131497 to -0.035590|0.999975|
|dev_medium_oop / texture_range_q8_b8 / clipped / current|4|same_updates|13.842024|7.875894|5.966130|2.035784 to 11.210282|0.256805|
|dev_medium_oop / texture_range_q8_b8 / clipped / current|4|same_work_label|9.519793|7.875894|1.643899|0.159831 to 2.690830|0.999992|
|dev_medium_oop / texture_range_q8_b8 / clipped / current|16|same_updates|26.300082|10.569078|15.731005|5.693595 to 23.046364|0.070064|
|dev_medium_oop / texture_range_q8_b8 / clipped / current|16|same_work_label|9.519793|10.569078|-1.049285|-2.667126 to 0.972982|0.999966|
|dev_medium_oop / texture_range_q8_b8 / clipped / linear_average|4|same_updates|6.292382|2.534473|3.757909|3.382175 to 3.991651|0.256805|
|dev_medium_oop / texture_range_q8_b8 / clipped / linear_average|4|same_work_label|2.501852|2.534473|-0.032621|-0.543301 to 0.498803|0.999992|
|dev_medium_oop / texture_range_q8_b8 / clipped / linear_average|16|same_updates|13.204421|2.479423|10.724997|10.040506 to 11.210055|0.070064|
|dev_medium_oop / texture_range_q8_b8 / clipped / linear_average|16|same_work_label|2.501852|2.479423|0.022429|-0.915461 to 0.655714|0.999966|
|dev_medium_oop / texture_range_q8_b8 / clipped / uniform_average|4|same_updates|7.953407|3.627102|4.326305|3.953463 to 4.519527|0.256805|
|dev_medium_oop / texture_range_q8_b8 / clipped / uniform_average|4|same_work_label|3.525759|3.627102|-0.101343|-0.490340 to 0.163177|0.999992|
|dev_medium_oop / texture_range_q8_b8 / clipped / uniform_average|16|same_updates|16.230310|3.306969|12.923341|11.701909 to 13.536731|0.070064|
|dev_medium_oop / texture_range_q8_b8 / clipped / uniform_average|16|same_work_label|3.525759|3.306969|0.218790|-0.454819 to 0.824186|0.999966|
|dev_medium_oop / texture_range_q8_b8 / signed / current|4|same_updates|36.548384|28.011637|8.536747|-0.753872 to 22.176181|0.276898|
|dev_medium_oop / texture_range_q8_b8 / signed / current|4|same_work_label|31.999117|28.011637|3.987480|1.020492 to 9.770126|0.999993|
|dev_medium_oop / texture_range_q8_b8 / signed / current|16|same_updates|33.815993|21.455738|12.360255|-13.008349 to 45.691881|0.070710|
|dev_medium_oop / texture_range_q8_b8 / signed / current|16|same_work_label|31.999117|21.455738|10.543379|1.106620 to 22.343764|0.999970|
|dev_medium_oop / texture_range_q8_b8 / signed / linear_average|4|same_updates|4.822839|2.172684|2.650155|-0.613363 to 5.879192|0.276898|
|dev_medium_oop / texture_range_q8_b8 / signed / linear_average|4|same_work_label|4.354032|2.172684|2.181348|-0.274492 to 5.131348|0.999993|
|dev_medium_oop / texture_range_q8_b8 / signed / linear_average|16|same_updates|7.492759|3.553971|3.938787|3.449719 to 4.245558|0.070710|
|dev_medium_oop / texture_range_q8_b8 / signed / linear_average|16|same_work_label|4.354032|3.553971|0.800060|0.051864 to 1.942720|0.999970|
|dev_medium_oop / texture_range_q8_b8 / signed / uniform_average|4|same_updates|3.392774|1.568496|1.824278|-1.414803 to 3.915029|0.276898|
|dev_medium_oop / texture_range_q8_b8 / signed / uniform_average|4|same_work_label|2.664089|1.568496|1.095593|-0.093301 to 2.731234|0.999993|
|dev_medium_oop / texture_range_q8_b8 / signed / uniform_average|16|same_updates|7.440070|1.653649|5.786421|4.775882 to 6.354822|0.070710|
|dev_medium_oop / texture_range_q8_b8 / signed / uniform_average|16|same_work_label|2.664089|1.653649|1.010440|0.640287 to 1.498253|0.999970|

All individual seed/target conditions remain in the CSVs. Fixed EV uses the responding seat’s sign; gain has the opposite sign. Better fixed EV need not mean lower self exploitability. Known tiny ranges, three seeds and dependent readouts do not establish general strength, convergence or default/fresh/global admission.
