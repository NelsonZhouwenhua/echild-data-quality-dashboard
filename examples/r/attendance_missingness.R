# Companion R example for an aggregate missingness summary.
# The Streamlit application uses Python; this file shows an equivalent R workflow.

education <- read.csv("data/processed/education_linked.csv")
summary <- aggregate(
  is.na(education$attendance_rate),
  by = list(academic_year = education$academic_year),
  FUN = mean
)
names(summary)[2] <- "attendance_missing_rate"
print(summary)
