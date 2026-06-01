SELECT source,
       records,
       matched,
       correct_links,
       false_links,
       ambiguous,
       linkage_rate,
       precision,
       recall
FROM linkage_evaluation_summary
ORDER BY source;
