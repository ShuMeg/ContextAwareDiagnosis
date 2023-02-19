"""
Author: Meghna Suresh

This module is created to push the XDK data to the neo4j graph database to form a complete context. The external
context data is complete in the context model by running this module.
"""
import json
import time as sys_time
import os
import csv
import logging
from neo4j import GraphDatabase

# uri_neo = "bolt://localhost:7687"
uri_neo = "neo4j+s://e4d7fc5b.databases.neo4j.io"
username_neo = "neo4j"
graph_db_neo = "neo4j"
# password_neo = "test_dbms"
password_neo = "L7iVdHaCY9NobsdWaB-8vohYVXEXf_ycVXmlOqQtWxk"


def push_xdk_data():
    graph_driver = GraphDatabase.driver(uri_neo, auth=(username_neo, password_neo))
    graph_session = graph_driver.session(database=graph_db_neo)

    del_query = [
        """MATCH (noise:n4sch__Instance{n4sch__name:"external_Device_Vibrations"})-[:HAS_VALUE]-(m) detach delete m""",
        """MATCH (noise:n4sch__Instance{n4sch__name:"external_Temperature"})-[:HAS_VALUE]-(m) detach delete m""",
        """MATCH (noise:n4sch__Instance{n4sch__name:"external_Pressure_data"})-[:HAS_VALUE]-(m) detach delete m""",
        """MATCH (noise:n4sch__Instance{n4sch__name:"external_Humidity_data"})-[:HAS_VALUE]-(m) detach delete m""",
        """MATCH (noise:n4sch__Instance{n4sch__name:"external_Device_Noise"})-[:HAS_VALUE]-(m) detach delete m"""]

    # delete old values
    for q in del_query:
        graph_session.run(q)

    query = """ 
            LOAD CSV WITH HEADERS FROM 'https://www.dropbox.com/s/96c12pg4zebag25/Data.csv?raw=1' AS line
            MATCH (acc:n4sch__Instance{n4sch__name: "external_Device_Vibrations" })
            MATCH (temp:n4sch__Instance{n4sch__name:"external_Temperature"})
            MATCH (pres:n4sch__Instance{n4sch__name:"external_Pressure_data"})
            MATCH (hum:n4sch__Instance{n4sch__name:"external_Humidity_data"})
            MATCH (noise:n4sch__Instance{n4sch__name:"external_Device_Noise"})

            MERGE (acc)-[:HAS_VALUE]->(a:n4sch__Value {value:toInteger(line.Acceleration ), unit: "m/s^2", time:datetime(REPLACE(line.Timestamp, ' ', 'T'))}) 

            MERGE (temp)-[:HAS_VALUE]->(t:n4sch__Value { value:line.Temperature, unit: "C",  time:datetime(REPLACE(line.Timestamp, ' ', 'T'))}) 

            MERGE (pres)-[:HAS_VALUE]->(p:n4sch__Value { value:toFloat(line.Pressure ), unit: "Pa",  time:datetime(REPLACE(line.Timestamp, ' ', 'T'))}) 

            MERGE (hum)-[:HAS_VALUE]->(h:n4sch__Value { value:(line.Humidity ), unit:"%",  time:datetime(REPLACE(line.Timestamp, ' ', 'T'))}) 

            MERGE (noise)-[:HAS_VALUE]->(no:n4sch__Value { value: (line.Noise ), unit: "dB",  time:datetime(REPLACE(line.Timestamp, ' ', 'T'))}) """
    graph_session.run(query)
    graph_session.close()
    logging.warning('XDK data pushed to Neo4j')
    print("XDK sensor data pushed to Neo4j")


if __name__ == '__main__':
    push_xdk_data()