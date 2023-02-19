MATCH (ex:n4sch__Class{n4sch__name:'External'}) 
MATCH (inf:n4sch__Class{n4sch__name:'Inferred'})
MATCH (int:n4sch__Class{n4sch__name:'Internal'})

//external context from XDK
MERGE (acc:n4sch__Instance{n4sch__name: "external_Device_Vibrations" })-[:IS_TYPE]->(ex)
MERGE (temp:n4sch__Instance{n4sch__name:"external_Temperature"})-[:IS_TYPE]->(ex)
MERGE (pres:n4sch__Instance{n4sch__name:"external_Pressure_data"})-[:IS_TYPE]->(ex)
MERGE (hum:n4sch__Instance{n4sch__name:"external_Humidity_data"})-[:IS_TYPE]->(ex)
MERGE (noise:n4sch__Instance{n4sch__name:"external_Device_Noise"})-[:IS_TYPE]->(ex);
