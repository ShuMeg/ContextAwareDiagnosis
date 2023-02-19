"""
Author: Meghna Suresh

This file uses the existing ontologies in the context knowledge base to traverse the graph,
and decides if a component has an abnormality. The set of abnormal components are returned.
"""

import statistics as st
import json
import time as sys_time
import os
from neo4j import GraphDatabase
import math
import logging



#Perform Context Reasoning based on the designed Ontology of the System
def ontological_context_reasoning(session):
    abnormality_showing_nodes = session.run("""Match (n:n4sch__Class) where n.Abnormality_weight > 0   
                                            RETURN n, size((n)-[:IS_RELATED_TO]-()) AS count """)

    logging.info('Checking for abnormal behaviors')
    print("Checking for Abnormal Behaviours...")

    #choosing nodes with abnormality more than 50%
    problematic_components = list()

    for nodes in abnormality_showing_nodes:

        abnormality_percentage = float(nodes[0]["Abnormality_weight"]) / float(nodes[1])
        logging.warning((nodes, "Abnormality Percentage:"+str(abnormality_percentage * 100)+"%"))
        if abnormality_percentage > 0.5:
            problematic_components.append([nodes[0]["n4sch__name"], abnormality_percentage * 100])

    logging.warning('Problems: ')
    logging.warning(str(problematic_components))
    print("problem: \n")
    print(problematic_components)
    return problematic_components