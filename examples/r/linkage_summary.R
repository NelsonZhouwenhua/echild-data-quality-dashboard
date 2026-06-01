# Companion R example for reading aggregate linkage metrics.

linkage <- read.csv("data/processed/linkage_evaluation_summary.csv")
print(linkage[, c("source", "records", "matched", "false_links", "linkage_rate", "precision", "recall")])
