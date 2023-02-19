LOAD CSV WITH HEADERS FROM 'file:///contextdata.csv' AS row 
MATCH (ex:n4sch__Class{n4sch__name:'External'}) 
MATCH (inf:n4sch__Class{n4sch__name:'Inferred'})
MATCH (int:n4sch__Class{n4sch__name:'Internal'})
WITH ex, inf, int, row
FOREACH (i in CASE WHEN row.datasource = "Water_Hardness" THEN [1] ELSE [] END |
  MERGE (d:n4sch__Instance {n4sch__name: row.datasource, mode: row.diagnosisMode})
  MERGE (d)-[:IS_TYPE]->(ex)
  MERGE (d)-[:HAS_VALUE]->(v:n4sch__Value {phase: row.phase, value: toFloat(row.observed_value), unit: row.unit, time:datetime(REPLACE(row.time, ' ', 'T'))})
)

FOREACH (i in CASE WHEN row.datasource = "Usage_Frequency" OR row.datasource = "Washing_Powder" OR row.datasource = "Used_Modes" THEN [1] ELSE [] END |
  MERGE (d:n4sch__Instance {n4sch__name: row.datasource, mode: row.diagnosisMode})
  MERGE (d)-[:IS_TYPE]->(inf)
  MERGE (d)-[:HAS_VALUE]->(v:n4sch__Value {phase: row.phase, value: toFloat(row.observed_value), unit: row.unit, time:datetime(REPLACE(row.time, ' ', 'T'))})
)

FOREACH (i in CASE WHEN row.datasource <> "Water_Hardness" AND row.datasource <> "Usage_Frequency" AND row.datasource <> "Washing_Powder" AND row.datasource <> "Used_Modes" THEN [1] ELSE [] END |
  MERGE (d:n4sch__Instance {n4sch__name: row.datasource, mode: row.diagnosisMode})
  MERGE (d)-[:IS_TYPE]->(int)
  MERGE (d)-[:HAS_VALUE]->(v:n4sch__Value {phase: row.phase, value: toFloat(row.observed_value), unit: row.unit, time:datetime(REPLACE(row.time, ' ', 'T'))})
)
