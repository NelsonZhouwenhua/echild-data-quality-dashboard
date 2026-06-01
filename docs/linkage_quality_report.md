# Synthetic linkage-quality report

> Synthetic demonstration only. This report does not use ECHILD, HES, NPD or children's social-care records.

## Source-level linkage evaluation

| source      |   records |   matched |   correct_links |   false_links |   missed_links |   ambiguous |   unmatched |   mean_confidence | linkage_rate   | precision   | recall   | false_link_rate   |
|:------------|----------:|----------:|----------------:|--------------:|---------------:|------------:|------------:|------------------:|:---------------|:------------|:---------|:------------------|
| education   |     95067 |     89824 |           88920 |           904 |           5243 |        1161 |        4082 |          0.931827 | 94.5%          | 99.0%       | 94.4%    | 1.0%              |
| health      |     12397 |     11910 |           11830 |            80 |            487 |         126 |         361 |          0.94352  | 96.1%          | 99.3%       | 96.0%    | 0.6%              |
| social_care |      3293 |      2925 |            2867 |            58 |            368 |          97 |         271 |          0.895259 | 88.8%          | 98.0%       | 88.6%    | 1.8%              |

## Linkage-rate variation by deprivation quintile

| source      |   deprivation_quintile |   records |   matched |   correct_links |   false_links |   missed_links |   ambiguous |   unmatched |   mean_confidence |   linkage_rate |   precision |   recall |   false_link_rate |
|:------------|-----------------------:|----------:|----------:|----------------:|--------------:|---------------:|------------:|------------:|------------------:|---------------:|------------:|---------:|------------------:|
| education   |                      1 |     18624 |     17806 |           17636 |           170 |            818 |         215 |         603 |          0.940101 |       0.956078 |    0.990453 | 0.955674 |        0.00912801 |
| education   |                      2 |     19835 |     18857 |           18666 |           191 |            978 |         263 |         715 |          0.936401 |       0.950693 |    0.989871 | 0.950214 |        0.00962944 |
| education   |                      3 |     19150 |     18112 |           17914 |           198 |           1038 |         212 |         826 |          0.932017 |       0.945796 |    0.989068 | 0.94523  |        0.0103394  |
| education   |                      4 |     18662 |     17476 |           17299 |           177 |           1186 |         231 |         955 |          0.92543  |       0.936448 |    0.989872 | 0.93584  |        0.00948451 |
| education   |                      5 |     18796 |     17573 |           17405 |           168 |           1223 |         240 |         983 |          0.924956 |       0.934933 |    0.99044  | 0.934346 |        0.00893807 |
| health      |                      1 |      2415 |      2350 |            2337 |            13 |             65 |          20 |          45 |          0.952104 |       0.973085 |    0.994468 | 0.972939 |        0.00538302 |
| health      |                      2 |      2572 |      2486 |            2474 |            12 |             86 |          36 |          50 |          0.950573 |       0.966563 |    0.995173 | 0.966406 |        0.00466563 |
| health      |                      3 |      2444 |      2359 |            2342 |            17 |             85 |          23 |          62 |          0.946493 |       0.965221 |    0.992794 | 0.964977 |        0.00695581 |
| health      |                      4 |      2527 |      2409 |            2390 |            19 |            118 |          23 |          95 |          0.937014 |       0.953304 |    0.992113 | 0.952951 |        0.0075188  |
| health      |                      5 |      2439 |      2306 |            2287 |            19 |            133 |          24 |         109 |          0.931346 |       0.945469 |    0.991761 | 0.945041 |        0.00779008 |
| social_care |                      1 |       627 |       550 |             536 |            14 |             77 |          23 |          54 |          0.890567 |       0.877193 |    0.974545 | 0.874388 |        0.0223285  |
| social_care |                      2 |       691 |       626 |             621 |             5 |             65 |          16 |          49 |          0.90667  |       0.905933 |    0.992013 | 0.905248 |        0.00723589 |
| social_care |                      3 |       726 |       646 |             634 |            12 |             80 |          21 |          59 |          0.895098 |       0.889807 |    0.981424 | 0.887955 |        0.0165289  |
| social_care |                      4 |       641 |       561 |             544 |            17 |             80 |          20 |          60 |          0.884297 |       0.875195 |    0.969697 | 0.871795 |        0.0265211  |
| social_care |                      5 |       608 |       542 |             532 |            10 |             66 |          17 |          49 |          0.898875 |       0.891447 |    0.98155  | 0.889632 |        0.0164474  |

## Interpretation note

The internal synthetic truth file is used only to test the portfolio workflow. Real administrative-data linkage evaluation requires project-specific methods, approved access arrangements and careful reporting of possible linkage bias.
