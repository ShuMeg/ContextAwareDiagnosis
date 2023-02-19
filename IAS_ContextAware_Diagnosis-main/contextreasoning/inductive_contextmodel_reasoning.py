"""
Author: Meghna Suresh

This file uses the Neo4j graph database to obtain recent and relevant data to perform
decision logic. This data is then sent to the ontological reasoning.

"""
import statistics as st
import json
import time as sys_time
import os
from neo4j import GraphDatabase
import math
import logging

from contextreasoning.ontological_reasoning import *

uri_neo = "neo4j+s://e4d7fc5b.databases.neo4j.io"
username_neo = "neo4j"
graph_db_neo = "neo4j"
password_neo = "L7iVdHaCY9NobsdWaB-8vohYVXEXf_ycVXmlOqQtWxk"


#function to obtain averages or normal ranges for the different contexts available
def context_averages(session, context_list):
    #querying all context nodes

        #print (str(item[0]).split("properties={'n4sch__name': ")[1].strip(">").strip("}").split(", 'source': "))

    for context in context_list:



        query = "MATCH(n: n4sch__Instance {n4sch__name: " + context[0] + ", source: "+ context[1] +"}) - [: HAS_VALUE]-(m:n4sch__Value) return m order by m.time DESC LIMIT 5"

        context_values = session.run(query)

        value_list=list()
        for value in context_values:

            try:
                value_list.append(float(str(value[0]).split("'value': ")[1].strip("}>")))
            except:
                value_list.append(float(str(value[0]).split("'value': ")[1].strip("}>").strip("'")))
        #print(value_list)

        context.append(float(st.mean(value_list)) )
    #print (context_list)
    return (context_list)



#dissociate context and state relationships
def dissociate_state_relationships(session, context_list):
    for context in context_list:
        try:
            session.run("""MATCH (:n4sch__Instance{n4sch__name: " + context[0]+ "})-[r:HAS_STATE]-(:n4sch__Instance)
            DELETE r""", context=context)
        except:
            pass
    logging.warning('State relationships dissociated')
    reset_component_abnormality_weight(session)



#function to reset the component abnormality weights to 0
def reset_component_abnormality_weight(session):
    session.run("""MATCH (:n4sch__Class{n4sch__name:"Device"})-[n4sch_SCO]-(components:n4sch__Class) SET components.Abnormality_weight = 0""")
    logging.warning('Abnormality weights reset to zero...')


#function to reset states for different contexts
def reset_state(session):
    session.run("""MATCH (m)-[r:HAS_STATE]-(n) detach delete r""")
    logging.warning('State relationships dissociated')


#function to reset the abnormality votes from the context
def reset_abnormality_votes(session):
    session.run("MATCH (m)-[r:IS_RELATED_TO]-(n) SET r.Abnormality_vote = 0")
    logging.warning('Abnormality votes reset')



#perform inductive knowledge reasoning
def inductive_reasoning(session, context_list):
    for context in context_list:
        if context[0] == "'Entrance_Water_Flow'":
            if context[2]==0:
                session.run("MATCH (n:n4sch__Instance{n4sch__name:" + context[0]+ ", source:" + context[1]+"}) MATCH (m:n4sch__Instance{n4sch__name: 'No_Flow'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run(
                    "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1] + "}) MATCH (m:n4sch__Instance{n4sch__name: 'Flow_OK'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

        elif context[0] == "'Lock'":
            if context[2] == 0:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1] + "}) MATCH (m:n4sch__Instance{n4sch__name: 'Open'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Close'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

        elif context[0] =="'Exit_Water_Flow'":
            if context[2] == 0:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'No_Flow'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Flow_OK'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

        elif context[0] == "'Pressure'":
            if context[2] > 1150 :
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")


        elif context[0] == "'Rotation_Speed'":

            if 50 <= context[2] <= 60:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 50:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            elif context[2] > 60:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Water_Level'":
            if context[1] == "'Pump Out.'":
                if  context[2] > 30:
                    session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
                else:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

            elif context[1] == "'Water Inlet.'":
                if  context[2] < 20.0:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
                else:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

        elif context[0] == "'Mass_Air_Flow'":

            if context[2] <= 50:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

        elif context[0] == "'Vibration'":
            if context[1] == "'Fan.'":
                if context[2] <= 25:
                    session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
                else:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            elif context[1] == "'Drum Motor.'":
                if context[2] <= 25:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
                else:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[
                            1] + "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Loudness'":
            if context[1] == "'Fan.'":
                if context[2] <= 7:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
                else:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

            elif context[1] == "'Drum Motor.'":
                if context[2] <= 7:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run(
                        "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
                else:
                    session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                    session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1 ")
                    session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                        context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Temperature'":

            if 30 <= context[2] <= 70:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 30:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})   SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Washing_Powder_Fill_Level'":

            if 35 <= context[2] <= 75:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 35:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Laundry_Weight'":

            if  context[2] <= 10:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (n:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO] MERGE (n)-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Laundry_Fill_Level'":

            if 35 <= context[2] <= 75:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 35:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1 ")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Used_Modes'":

            if context[2] == 1:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0] + ", source: " + context[1] + "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0] + ", source: " + context[1] + "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")


        elif context[0] == "'Usage_Frequency'":

            if 4 <= context[2] <= 9:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 4:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1 ")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Washing_Powder'":

            if context[2] == 1:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0] + ", source: " + context[
                    1] + "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")

        elif context[0] == "'external_Device_Vibrations'":

            if 2000 <= context[2] <= 5000:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 2000:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1 ")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'external_Device_Noise'":

            if  65 <= context[2] <= 80:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 65:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            else:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'external_Temperature'":

            if 15.0 <= context[2] <= 30.0:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 15.0:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'external_Pressure_data'":

            if 95000 <= context[2] <= 102500:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 95000:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})   SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'external_Humidity_data'":

            if 5.0 <= context[2] <= 80.0:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            elif context[2] < 5.0:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Low'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})   SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
            else:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run(
                    "MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +
                    context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")

        elif context[0] == "'Water_Hardness'":

            if context[2] <= 14:
                session.run("MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'Normal'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 0")
            else:
                session.run( "MATCH (n:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "}) MATCH (m:n4sch__Instance{n4sch__name: 'High'}) MERGE (n)-[:HAS_STATE]-(m)")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " + context[0]+ ", source: " + context[1]+ "})  SET components.Abnormality_weight = components.Abnormality_weight+1")
                session.run("MATCH (:n4sch__Class{n4sch__name:'Device'})-[n4sch_SCO]-(components:n4sch__Class)-[rel:IS_RELATED_TO]-(:n4sch__Instance{n4sch__name: " +context[0] + ", source: " + context[1] + "})  SET rel.Abnormality_vote = 1")
    logging.warning('Inductive reasoning done!!!')

#start inductive context reasoning
def inductive_context_reasoning():

    graph_driver = GraphDatabase.driver(uri_neo, auth=(username_neo, password_neo))
    graph_session = graph_driver.session(database=graph_db_neo)

    #query context_list
    context_nodes = graph_session.run("""MATCH (:n4sch__Class{n4sch__name:"Context"})<-[:n4sch__SCO]-(m)-[:IS_TYPE]-(
    n:n4sch__Instance) return n""")
    context_list = list()

    for item in context_nodes:
        context_list.append(str(item[0]).split("properties={'n4sch__name': ")[1].strip(">").strip("}").split(", 'source': "))


    dissociate_state_relationships(graph_session, context_list)                     #dissociating state relationships in the graph


    reset_component_abnormality_weight(graph_session)                               #reset abnormality weights

    reset_state(graph_session)                                                      #reset context states
    #print(context_list)
    averages=context_averages(graph_session, context_list)                          #derive averages from most recent data

    print(averages)
    #check(graph_session, context_list)
    inductive_reasoning(graph_session, averages)                                     #perform inductive reasoning

    logging.warning('Performing ontological reasoning')
    p = ontological_context_reasoning(graph_session)                                #perform ontological reasoning

    return p

