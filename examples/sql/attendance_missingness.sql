SELECT academic_year,
       ROUND(100.0 * AVG(CASE WHEN attendance_rate IS NULL THEN 1 ELSE 0 END), 1) AS missing_percent
FROM education_records
GROUP BY academic_year
ORDER BY academic_year;
