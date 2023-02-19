"""
Author: Meghna Suresh

This module is used to transfer latest internal sensor data that is generated 
from SQL to CSV file in the cloud (Dropbox), and then to the graph database Neo4j.

"""
import pandas as pd
import sys
import sqlalchemy
import logging
import datetime
from neo4j import GraphDatabase


#to populate the CSV with the latest data, and then push the data
#to the Neo4j Graph Database 
def latest_sql_to_graph(graph_session, connection, out_file_path):
    query_time = "SELECT time from graphcontextdata ORDER BY time DESC LIMIT 1"
    time_df = pd.read_sql(sql=query_time,
                          con=connection, parse_dates=['time'], columns=["idsensordata", "diagnosisMode", "phase",
                                                                         "datasource", "observed_value", "time",
                                                                         "unit"])
    latest_time = time_df.iloc[0]["time"] - datetime.timedelta(hours=2)
    latest_time = latest_time.strftime('%m/%d/%Y, %H:%M:%S')

    query = "SELECT *, AVG(observed_value) AS avg_val FROM graphcontextdata WHERE `time` > '" + str(
        latest_time) + "' AND `phase` != 0 AND `diagnosisMode` != 'Complete Short Program' GROUP BY diagnosisMode, `phase`, datasource, `time`;"
    context_df = pd.read_sql(sql=query,
                             con=connection, parse_dates=['time'], columns=["idsensordata", "diagnosisMode", "phase",
                                                                            "datasource", "observed_value", "time",
                                                                            "unit"])

    logging.warning('Reading new data from SQL')
    print("reading new data")

    # Delete rows that contain null values in any of its columns
    context_df = context_df.dropna()
    context_df = context_df[~context_df.unit.str.contains("internal")]

    # Create .csv file in the Import folder of Neo4j -> files are named with creation timestamp

    logging.warning('Writing data to CSV')
    print("Writing data to .csv...")
    context_df.to_csv(out_file_path, header=True, index=False)
    logging.warning('Write succesful')
    #print("Write successful, data written to " + out_file_path)
    # Cypher query to load the CSV
    logging.warning('Exporting CSV to graph')
    print("Exporting .csv data to graph...")
    query_load = '''LOAD CSV WITH HEADERS FROM 'https://www.dropbox.com/s/38pfaqz0pzw57rp/test_data.csv?raw=1' AS row FIELDTERMINATOR ','
                            MATCH (ex:n4sch__Class{n4sch__name:'External'}) 
                            MATCH (inf:n4sch__Class{n4sch__name:'Inferred'})
                            MATCH (int:n4sch__Class{n4sch__name:'Internal'})
                            WITH ex, inf, int, row
                            FOREACH (i in CASE WHEN row.datasource = "Water_Hardness" AND row.diagnosisMode <> "Long Time Check"  THEN [1] ELSE [] END |
                            //MERGE (d:n4sch__Instance {n4sch__name: row.datasource, mode: row.diagnosisMode})
                            MERGE (d:n4sch__Instance {n4sch__name:row.datasource, source: REPLACE(row.diagnosisMode, ' Program', '.')})
                            MERGE (d)-[:IS_TYPE]->(ex)
                            MERGE (d)-[:HAS_VALUE]->(v:n4sch__Value {phase: row.phase, value: toFloat(row.observed_value), unit: row.unit, time:datetime(REPLACE(row.time, ' ', 'T'))})
                            )

                            FOREACH (i in CASE WHEN row.datasource <> "Water_Hardness" AND row.datasource <> "Usage_Frequency" AND row.datasource <> "Washing_Powder" AND row.datasource <> "Used_Modes" AND row.diagnosisMode = "Long Time Check"  THEN [1] ELSE [] END |
                            //MERGE (d:n4sch__Instance {n4sch__name: row.datasource, mode: row.diagnosisMode})
                            MERGE (d:n4sch__Instance {n4sch__name: row.datasource, source: "Internal."})
                            MERGE (d)-[:IS_TYPE]->(int)
                            MERGE (d)-[:HAS_VALUE]->(v:n4sch__Value {phase: row.phase, value: toFloat(row.observed_value), unit: row.unit, time:datetime(REPLACE(row.time, ' ', 'T'))})
                            )

                            FOREACH (i in CASE WHEN (row.datasource = "Usage_Frequency" OR row.datasource = "Washing_Powder" OR row.datasource = "Used_Modes")  THEN [1] ELSE [] END |
                            MERGE (d:n4sch__Instance {n4sch__name: row.datasource, source: "Inferred."})
                            MERGE (d)-[:IS_TYPE]->(inf)
                            MERGE (d)-[:HAS_VALUE]->(v:n4sch__Value {phase: row.phase, value: toFloat(row.observed_value), unit: row.unit, time:datetime(REPLACE(row.time, ' ', 'T'))})
                            )


                            FOREACH (i in CASE WHEN row.datasource <> "Water_Hardness" AND row.datasource <> "Usage_Frequency" AND row.datasource <> "Washing_Powder" AND row.datasource <> "Used_Modes" AND row.diagnosisMode <> "Long Time Check" THEN [1] ELSE [] END |
                            MERGE (d:n4sch__Instance {n4sch__name:row.datasource, source: REPLACE(row.diagnosisMode, ' Program', '.')})
                            MERGE (d)-[:IS_TYPE]->(int)
                            MERGE (d)-[:HAS_VALUE]->(v:n4sch__Value {phase: row.phase, value: toFloat(row.observed_value), unit: row.unit, time:datetime(REPLACE(row.time, ' ', 'T'))})
                            )
                        '''
    try:
        graph_session.run(query_load)
        logging.warning('Graph export successful')
        print("Graph export successful.")
    except Exception as e:
        print(str(e))
        logging.warning(str(e))
        logging.warning('Unable to run graph query!')
        print("Unable to run graph query!")
    finally:
        graph_session.close()

