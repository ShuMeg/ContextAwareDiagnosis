//Device instances
MATCH (dev:n4sch__Class{n4sch__name: "Devices"}) 
SET dev.n4sch__name = "Automated Wash-Dryer"
MATCH (dev:n4sch__Class{n4sch__name: "Devices"})
MATCH (app:n4sch__Class{n4sch__name: "Appliance"})
MERGE (dev)-[:n4sch__SCO]->(app)

 
//Task instances
MATCH (tsk:n4sch__Class{n4sch__name: "Tasks"})
MERGE (:n4sch__Instance {n4sch__name: "Detect Defect"}) - [:IS_TYPE] -> (tsk)
MERGE (:n4sch__Instance {n4sch__name: "Washing"}) - [:IS_TYPE] -> (tsk)
MERGE (:n4sch__Instance {n4sch__name: "Suggest Maintenance"}) - [:IS_TYPE] -> (tsk)
MERGE (:n4sch__Instance {n4sch__name: "Drying"}) - [:IS_TYPE] -> (tsk);

//Communication instances
MATCH (com:n4sch__Class{n4sch__name: "Communication"})
MERGE (:n4sch__Instance {n4sch__name: "NFC Tag"}) - [:IS_TYPE] -> (com)
MERGE (:n4sch__Instance {n4sch__name: "Web Server"}) - [:IS_TYPE] -> (com);

//Control instances
MATCH (ct:n4sch__Class{n4sch__name: "Control"})
MERGE (:n4sch__Instance {n4sch__name: "Controller Board"}) - [:IS_TYPE] -> (ct)
MERGE (:n4sch__Instance {n4sch__name: "Context Reasoning Engine"}) - [:IS_TYPE] -> (ct);

//Actuator instances
MATCH (a:n4sch__Class{n4sch__name: "Actuator"})
MATCH (fan {n4sch__name: "Fan"}) 
MATCH (wiv {n4sch__name:"Water_Inlet_valve"}) 
MATCH (mot {n4sch__name: "Motor"})
MATCH (wap {n4sch__name: "Water_pump"})
WITH a, fan, wiv, mot, wap
MERGE (fan) - [:IS_TYPE] -> (a)
MERGE (wiv) - [:IS_TYPE] -> (a)
MERGE (mot) - [:IS_TYPE] -> (a)
MERGE (wap) - [:IS_TYPE] -> (a)
MERGE (:n4sch__Instance {n4sch__name: "Door Lock") - [:IS_TYPE] -> (a) 


//Sensor instances
MATCH (sn:n4sch__Class{n4sch__name: "Sensor"})
MERGE (:n4sch__Instance {n4sch__name: "Temperature Sensor", type: "Internal", mode: "Long Time Check"}) - [:IS_TYPE] -> (sn)
MERGE (:n4sch__Instance {n4sch__name: "Ambient Temperature Sensor", type: "External"}) - [:IS_TYPE] -> (sn)
MERGE (:n4sch__Instance {n4sch__name: "Ambient Humidity Sensor", type: "External"}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Washing Powder Fill Level Sensor", type: "Internal", mode: "Long Time Check"}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Door Lock Sensor", type: "Internal", mode: "Door Lock Program"}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Loudness Sensor", type: "Internal", mode: ["Drum Motor Program", "Fan Program"]}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Vibration Sensor", type: "Internal", mode: ["Drum Motor Program", "Fan Program"]}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Mass Air Flow Sensor", type: "Internal", mode: "Fan Program"}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Pressure Sensor", type: "Internal", mode: "Door Lock Program"}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Rotation Speed Sensor", type: "Internal", mode: "Drum Motor Program"}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Water Flow Sensor", type: "Internal", mode: ["Water Inlet Program", "Pump Out Program"]}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Water Fill Level Sensor", type: "Internal", mode: ["Water Inlet Program", "Pump Out Program"]}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Laundry Fill Level Sensor", type: "Internal", mode: "Long Time Check"}) - [:IS_TYPE] -> (sn) 
MERGE (:n4sch__Instance {n4sch__name: "Laundry Weight Sensor", type: "Internal", mode: "Long Time Check"}) - [:IS_TYPE] -> (sn) 

//external sensors
MATCH (sn:n4sch__Class{n4sch__name: "External_sensors"})
MERGE (:n4sch__Instance {n4sch__name: "External Temperature Sensor", type: "External"}) - [:IS_TYPE] -> (sn)
MERGE (:n4sch__Instance {n4sch__name: "External Pressure Sensor", type: "External"}) - [:IS_TYPE] -> (sn)
MERGE (:n4sch__Instance {n4sch__name: "External Humidity Sensor", type: "External"}) - [:IS_TYPE] -> (sn)
MERGE (:n4sch__Instance {n4sch__name: "External Device Noise Sensor", type: "External"}) - [:IS_TYPE] -> (sn)
MERGE (:n4sch__Instance {n4sch__name: "External Device Vibrations Sensor", type: "External"}) - [:IS_TYPE] -> (sn) 


/////for states
MATCH (n:n4sch__Class {n4sch__name: "Open/Close"})
MERGE (:n4sch__Instance {n4sch__name: "Open"})-[:IS_TYPE]-(n)
MERGE (:n4sch__Instance {n4sch__name: "Close"})-[:IS_TYPE]-(n)

MATCH (n:n4sch__Class {n4sch__name: "Multi-Level"})
MERGE (:n4sch__Instance {n4sch__name: "Low"})-[:IS_TYPE]-(n)
MERGE (:n4sch__Instance {n4sch__name: "High"})-[:IS_TYPE]-(n)
MERGE (:n4sch__Instance {n4sch__name: "Normal"})-[:IS_TYPE]-(n)

MATCH (n:n4sch__Class {n4sch__name: "On/Off"})
MERGE (:n4sch__Instance {n4sch__name: "On"})-[:IS_TYPE]-(n)
MERGE (:n4sch__Instance {n4sch__name: "Off"})-[:IS_TYPE]-(n)


MATCH (n:n4sch__Class {n4sch__name: "Flow-Level"})
MERGE (:n4sch__Instance {n4sch__name: "Flow_OK"})-[:IS_TYPE]-(n)
MERGE (:n4sch__Instance {n4sch__name: "No_Flow"})-[:IS_TYPE]-(n)

//Components
MATCH (m {n4sch__name:"Automated Wash-Dryer"})<-[r:n4sch__SCO]-(n)
merge (m)<-[rel:HAS_COMPONENTS]-(n)
delete r

Printed_Control_Board
MATCH (m {n4sch__name:"Printed_Control_Board"}) SET m.n4sch__name = "Controller-Board"