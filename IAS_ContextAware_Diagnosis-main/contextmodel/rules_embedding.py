'''
Submitted 27.10.2021
Author: Gabriella Ilena

This module generates the state combinations as rules and stores them as data in the application model. Run this
module by running the server and calling the API on http://localhost:5000/embed_rules
'''

import sys
import random
from neo4j import GraphDatabase
from itertools import product


def create_anomaly_rels(session, defect_name, program_name, state, context, combo_id):
    session.run("""
        WITH $defect as dnames
        UNWIND dnames as dname
        MATCH (ai:n4sch__Instance{n4sch__name: dname})
        MERGE (co:n4sch__Combination{n4sch__name:'State Combination', combo_id:$combo_id, mode: $program})
        MERGE (st:n4sch__Instance{n4sch__name:$state, source: $context})
        MERGE (st) - [:HAS_COMBINATION] - (co)
        MERGE (co) - [r:CAUSES_ANOMALY{mode: $program}] -> (ai)
        ON CREATE SET r.time=[]
        """, state=state, defect=defect_name, program=program_name, context=context, combo_id=combo_id)
    return


def create_suggestion_rels(session, node_name, program_name, state, context, combo_id):
    if combo_id != 0:
        session.run("""
            WITH $node as nnames
            UNWIND nnames as nname
            MATCH (ai:n4sch__Instance{n4sch__name: nname})
            MERGE (co:n4sch__Combination{n4sch__name:'State Combination', combo_id:$combo_id, mode: $program})
            MERGE (st:n4sch__Instance{n4sch__name:$state, source: $context})
            MERGE (st) - [:HAS_COMBINATION] - (co)
            MERGE (co) - [:SUGGESTS{mode: $program}] -> (ai)
            """, state=state, node=node_name, program=program_name, context=context, combo_id=combo_id)
    return

# Configure Neo4j db
#uri = "neo4j+s://0c5e103c.databases.neo4j.io"
#username = "neo4j"
#password = "b8HEnf1dgwy6D33Z6nBdjsgsN95KqgT3Ed0lHjvG2J0"
#graph_db = "neo4j" 
#uri=uri, username=username, password=password, db_name=graph_db
def rules_to_graph(uri, username, password, db_name):

    # Connect to graph database
    try:
        graph_driver = GraphDatabase.driver(uri, auth=(username, password))
        graph_session = graph_driver.session(database=db_name)

        # Get program names
        query_res = graph_session.run("""MATCH (:n4sch__Class{n4sch__name:"Context"})<-[:n4sch__SCO]-(m)-[:IS_TYPE]-(n:n4sch__Instance) WHERE size(n.mode) > 2 
                    RETURN DISTINCT n.mode""")
        programs = list()
        for item in query_res:
            programs.append(item[0])

        # Seed is important: without it, the same state combinations can then have different ids
        # resulting in duplicated nodes
        random.seed(0)
        for program in programs:
            print(program)
            if program == "Health Check":
                state1 = ['Balanced', 'Unbalanced']
                state2 = ['Overloaded', 'Load OK']
                state_combinations = list(product(state1, state2))
                for item in state_combinations:
                    flags_anomaly = {'actuator': False, 'Overload': False}
                    current_state = {'XDK_Accelerometer': item[0], 'Load_Weight': item[1]}
                    id = "ca" + str(random.randint(0, 1000))
                    if current_state['XDK_Accelerometer'] == 'Unbalanced':
                        if current_state['Load_Weight'] == 'Load OK':
                            flags_anomaly['actuator'] = True
                        else:
                            flags_anomaly['Overload'] = True
                    else:
                        # normal: do nothing
                        pass
                    # Create relationships between state and current context data
                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["Overload"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Machine Overloaded",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass

                state3 = ['Normal', 'Loud']
                state4 = ['Overloaded', 'Load OK']
                state_combinations = list(product(state3, state4))
                for item in state_combinations:
                    flags_anomaly = {'actuator': False, 'Overload': False}
                    current_state = {'XDK_Noise': item[0], 'Load_Weight': item[1]}
                    id = "ca" + str(random.randint(0, 1000))
                    if current_state['XDK_Noise'] == 'Loud':
                        if current_state['Load_Weight'] == 'Load OK':
                            flags_anomaly['actuator'] = True
                        else:
                            flags_anomaly['Overload'] = True
                    else:
                        # normal: do nothing
                        pass
                    # Create relationships between state and current context data
                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["Overload"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Machine Overloaded",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass
                state5 = ['Not Humid', 'Humid']
                state_combinations = list(product(state5))
                for item in state_combinations:
                    flags_anomaly = {'actuator': False}
                    current_state = {'XDK_Humidity': item[0]}
                    id = "ca" + str(random.randint(0, 1000))
                    if current_state['XDK_Humidity'] == 'Humid':
                        flags_anomaly['actuator'] = True
                    else:
                        # normal: do nothing
                        pass
                    # Create relationships between state and current context data
                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass
                state6 = ['Duration OK', 'Duration Long']
                state_combinations = list(product(state6))
                for item in state_combinations:
                    flags_anomaly = {'Load Sense Defect': False}
                    current_state = {'Duration': item[0]}
                    id = "ca" + str(random.randint(0, 1000))
                    if current_state['Duration'] == 'Duration Long':
                        flags_anomaly['Load Sense Defect'] = True
                    else:
                        # normal: do nothing
                        pass
                    # Create relationships between state and current context data
                    if flags_anomaly["Load Sense Defect"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Load Sense Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass  
            elif program == "Pump Out Program":
                state1 = ['High', 'Low']
                state2 = ['No Flow', 'Flow OK']
                state_combinations = list(product(state1, state2))
                for item in state_combinations:
                    flags_anomaly = {'actuator': False, 'sensor': False}
                    current_state = {'Water_Level': item[0], 'Exit_Water_Flow': item[1]}
                    id = "ca" + str(random.randint(0, 1000))
                    if current_state['Water_Level'] == 'High':
                        if current_state['Exit_Water_Flow'] == 'No Flow':
                            flags_anomaly['actuator'] = True
                        else:
                            flags_anomaly['sensor'] = True
                    else:
                        if current_state['Exit_Water_Flow'] == 'No Flow':
                            flags_anomaly['sensor'] = True
                        else:
                            pass
                    # Create relationships between state and current context data

                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["sensor"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Sensor Defect",
                                                program_name=program, context=key, state=value, combo_id=id)                                   
                    else:
                        pass
            elif program == "Door Lock Program":
                state1 = ['Normal', 'Low']
                state2 = ['Locked', 'Unlocked']
                state_combinations = list(product(state1, state2))
                for item in state_combinations:
                    id = "ca" + str(random.randint(0, 1000))
                    current_state = {'Pressure': item[0], 'Lock': item[1]}
                    flags_anomaly = {'actuator': False, 'sensor': False}
                    if current_state['Pressure'] == 'Normal':
                        if current_state['Lock'] == 'Locked':
                            # normal: do nothing
                            pass
                        else:
                            flags_anomaly['sensor'] = True
                    else:
                        if current_state['Lock'] == 'Locked':
                            flags_anomaly['sensor'] = True
                        else:
                            flags_anomaly['actuator'] = True

                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["sensor"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Sensor Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass
            elif program == "Fan Program":
                state1 = ['Normal', 'High']
                state2 = ['Normal', 'High']
                state3 = ['Normal', 'Low']
                state_combinations = list(product(state1, state2, state3))
                for item in state_combinations:
                    id = "ca" + str(random.randint(0, 1000))
                    current_state = {'Loudness': item[0], 'Vibration': item[1], 'Mass_Air_Flow': item[2]}
                    flags_anomaly = {"actuator": False, "position": False, "object": False}
                    if all(i == 'Normal' for i in current_state.values()):
                        # normal: do nothing
                        pass
                    elif ('Normal', 'High', 'Normal') == item:
                        flags_anomaly['position'] = True
                    elif ('High', 'High', 'Normal') == item:
                        flags_anomaly['object'] = True
                    else:
                        flags_anomaly['actuator'] = True

                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["position"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Position",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["object"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Foreign Object",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass
            elif program == "Drum Motor Program":
                state1 = ['Normal', 'High']
                state2 = ['Normal', 'High']
                state3 = ['Normal', 'Low', 'High']
                state_combinations = list(product(state1, state2, state3))
                for item in state_combinations:
                    id = "ca" + str(random.randint(0, 1000))
                    current_state = {'Loudness': item[0], 'Vibration': item[1], 'Rotation_Speed': item[2]}
                    flags_anomaly = {"actuator": False, "position": False, "object": False, "undefined": False, "power_supply": False}
                    
                    if current_state['Loudness'] == 'Normal':
                        if current_state['Vibration'] == 'Normal':
                            if current_state['Rotation_Speed'] == 'Normal':
                                # normal: do nothing
                                pass
                            else:
                                flags_anomaly['actuator'] = True
                        elif current_state['Vibration'] == 'High':
                            if current_state['Rotation_Speed'] == 'High':
                                flags_anomaly['actuator'] = True
                            else:
                                flags_anomaly['position'] = True
                    elif current_state['Loudness'] == 'High':
                        if current_state['Vibration'] == 'Normal':
                            if current_state['Rotation_Speed'] == 'Normal':
                                flags_anomaly['undefined'] = True
                            else:
                                flags_anomaly['actuator'] = True
                        elif current_state['Vibration'] == 'High':
                            if current_state['Rotation_Speed'] == 'Low':
                                flags_anomaly['object'] = True
                            else:
                                flags_anomaly['power_supply'] = True

                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["position"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Position",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["object"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Foreign Object",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["power_supply"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Power Supply",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly['undefined']:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Undefined",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass
            elif program == "Water Inlet Program":
                state1 = ['Normal', 'Low']
                state2 = ['No Flow', 'Flow OK']
                state3 = ['Normal', 'Hard']
                state_combinations = list(product(state1, state2, state3))
                for item in state_combinations:
                    id = "ca" + str(random.randint(0, 1000))
                    flags_anomaly = {'actuator': False, 'sensor': False, 'hard_water': False}
                    current_state = {'Water_Level': item[0], 'Entrance_Water_Flow': item[1], 'Water_Hardness': item[2]}
                    if current_state['Water_Hardness'] == 'Normal':
                        if current_state['Water_Level'] == 'Normal':
                            if current_state['Entrance_Water_Flow'] == 'Flow OK':
                                # normal: do nothing
                                pass
                            else:
                                flags_anomaly['sensor'] = True
                        else:
                            if current_state['Entrance_Water_Flow'] == 'Flow OK':
                                flags_anomaly['sensor'] = True
                            else:
                                flags_anomaly['actuator'] = True
                    elif current_state['Water_Hardness'] == 'Hard':
                        if current_state['Water_Level'] == 'Normal':
                            if current_state['Entrance_Water_Flow'] == 'Flow OK':
                                flags_anomaly["hard_water"] = True
                            else:
                                flags_anomaly['sensor'] = True
                                flags_anomaly["hard_water"] = True
                        else:
                            if current_state['Entrance_Water_Flow'] == 'Flow OK':
                                flags_anomaly['sensor'] = True
                                flags_anomaly["hard_water"] = True
                            else:
                                flags_anomaly['actuator'] = True
                                flags_anomaly["hard_water"] = True
                        
                    if flags_anomaly["actuator"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["sensor"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Sensor Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly["hard_water"]:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Hard Water",
                                                program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass
            elif program == "Long Time Check":
                # Detergent fill level, detergent type, and water hardness
                detergent_fill = ['Normal', 'Low', 'High']
                detergent_type = ['Weak', 'Normal', 'Strong']
                water_hardness = ['Normal', 'Soft', 'Hard']
                state_combinations = list(product(detergent_fill, detergent_type, water_hardness))
                for item in state_combinations:
                    id = "cs" + str(random.randint(0, 1000))
                    flags_suggestion = {'reduce_detergent': False, 'stronger_more_detergent': False}
                    current_state = {'Washing_Powder_Fill_Level': item[0], "Washing_Powder": item[1], 'Water_Hardness': item[2]}
                    if current_state["Washing_Powder_Fill_Level"] == "High":
                        if current_state["Water_Hardness"] == "Soft":
                            flags_suggestion['reduce_detergent'] = True
                        elif current_state["Water_Hardness"] == "Normal":
                            if current_state["Washing_Powder"] == "Weak":
                                # optimal: do nothing
                                pass
                            else:
                                flags_suggestion['reduce_detergent'] = True
                        else:
                            if current_state["Washing_Powder"] == "Weak":
                                flags_suggestion['stronger_more_detergent'] = True
                            elif current_state["Washing_Powder"] == "Normal":
                                # optimal: do nothing
                                pass
                            else:
                                flags_suggestion['reduce_detergent'] = True
                    elif current_state["Washing_Powder_Fill_Level"] == "Low":
                        if current_state["Water_Hardness"] == "Soft":
                            if current_state["Washing_Powder"] == "Strong" or current_state["Washing_Powder"] == "Normal":
                                # optimal: do nothing
                                pass
                            else:
                                flags_suggestion['stronger_more_detergent'] = True
                        elif current_state["Water_Hardness"] == "Normal":
                            if current_state["Washing_Powder"] == "Weak" or current_state["Washing_Powder"] == "Normal":
                                flags_suggestion['stronger_more_detergent'] = True
                            else:
                                # optimal: do nothing
                                pass
                        else:
                            flags_suggestion['stronger_more_detergent'] = True
                    else:
                        if current_state["Water_Hardness"] == "Normal":
                            if current_state["Washing_Powder"] == "Weak":
                                flags_suggestion['stronger_more_detergent'] = True
                            elif current_state["Washing_Powder"] == "Normal":
                                # optimal: do nothing
                                pass
                            else:
                                flags_suggestion['reduce_detergent'] = True
                        elif current_state["Water_Hardness"] == "Soft":
                            if current_state["Washing_Powder"] == "Weak":
                                # optimal: do nothing
                                pass
                            else:
                                flags_suggestion['reduce_detergent'] = True
                        else:
                            if current_state["Washing_Powder"] == "Strong":
                                # optimal: do nothing
                                pass
                            else:
                                flags_suggestion['stronger_more_detergent'] = True

                    if flags_suggestion['reduce_detergent']:
                        for key, value in current_state.items():
                            create_suggestion_rels(session=graph_session, node_name="Reduce Detergent",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_suggestion['stronger_more_detergent']:
                        for key, value in current_state.items():
                            create_suggestion_rels(session=graph_session, node_name="Stronger/More Detergent",
                                                   program_name=program, context=key, state=value, combo_id=id)
                    else:
                        pass

                # Temperature and used modes
                temperature = ['Normal', 'Low', 'High']
                modes = ['Delicate', 'Normal', 'Deep Clean']
                state_combinations = list(product(temperature, modes))
                for item in state_combinations:
                    id = "ca" + str(random.randint(0, 1000))
                    current_state = {'Temperature': item[0], 'Used_Modes': item[1]}
                    flags_anomaly = {'actuator': False, 'sensor': False}
                    if current_state["Temperature"] == "Normal":
                        if current_state["Used_Modes"] == "Delicate":
                            flags_anomaly['actuator'] = True
                            flags_anomaly['sensor'] = True
                        elif current_state["Used_Modes"] == "Normal":
                            # normal: do nothing
                            pass
                        else:
                            flags_anomaly['actuator'] = True
                            flags_anomaly['sensor'] = True
                    elif current_state["Temperature"] == "Low":
                        if current_state["Used_Modes"] == "Delicate":
                            # normal: do nothing
                            pass
                        elif current_state["Used_Modes"] == "Normal":
                            flags_anomaly['actuator'] = True
                            flags_anomaly['sensor'] = True
                        else:
                            flags_anomaly['actuator'] = True
                            flags_anomaly['sensor'] = True
                    else:
                        if current_state["Used_Modes"] == "Delicate":
                            flags_anomaly['actuator'] = True
                            flags_anomaly['sensor'] = True
                        elif current_state["Used_Modes"] == "Normal":
                            flags_anomaly['actuator'] = True
                            flags_anomaly['sensor'] = True
                        else:
                            # normal: do nothing
                            pass

                    if flags_anomaly['actuator']:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Actuator Defect",
                                                program_name=program, context=key, state=value, combo_id=id)
                    elif flags_anomaly['sensor']:
                        for key, value in current_state.items():
                            create_anomaly_rels(session=graph_session, defect_name="Sensor Defect",
                                                program_name=program, context=key, state=value, combo_id=id)

                # Laundry Fill
                laundry_fill = ['Normal', 'Low', 'High']
                laundry_weight = ['Low', 'High']
                state_combinations = list(product(laundry_fill, laundry_weight))
                for item in state_combinations:
                    id = "cs" + str(random.randint(0, 1000))
                    current_state = {'Laundry_Fill_Level': item[0], 'Laundry_Weight': item[1]}
                    if current_state["Laundry_Weight"] == "Low":
                        if current_state["Laundry_Fill_Level"] == "High":
                            # normal: do nothing
                            pass
                        else:
                            for key, value in current_state.items():
                                create_suggestion_rels(session=graph_session, node_name="Increase Laundry",
                                                       program_name=program,
                                                       state=value, context=key, combo_id=id)
                    else:
                        for key, value in current_state.items():
                            create_suggestion_rels(session=graph_session, node_name="Reduce Laundry", program_name=program,
                                                   state=value, context=key, combo_id=id)

                # Usage Frequency
                frequency = ['Normal', 'Low', 'High']
                for i in frequency:
                    id = "cs" + str(random.randint(0, 1000))
                    current_state = {'Usage_Frequency': i}
                    if current_state["Usage_Frequency"] == "Normal":
                        # optimal: do nothing
                        pass
                    elif current_state["Usage_Frequency"] == "Low":
                        create_suggestion_rels(session=graph_session, node_name="Run Diagnosis Programs", program_name=program,
                                               state=i, context='Usage_Frequency', combo_id=id)
                    else:
                        create_suggestion_rels(session=graph_session, node_name="Reduce Usage Frequency", program_name=program,
                                               state=i, context='Usage_Frequency', combo_id=id)
            ''' 
            -------------------------
            ADD NEW RULES HERE
            -------------------------
            elif program == "<program_name>":
                # Declare states of each source
                source1_state = [...]
                source2_state = [...]
                
                # Create combinations of states that will be checked for conditions
                state_combinations = list(product(source1_state, source2_state, ...))
                
                # For each combination, create the corresponding relationship to anomaly and/or suggestions (if any)
                for item in state_combinations:
                    # Create ID
                    # Define conditions for state combination (if-else)
                        # Call the create_anomaly_rels(params) or create_suggestion_rels(params) as necessary
                ...
                
            '''
        # Merge the created states with the State class
        graph_session.run('''MATCH (m:n4sch__Class{n4sch__name: "State"})
        MATCH (n:n4sch__Instance) WHERE exists(n.source)
        MERGE (n) - [:IS_TYPE] - (m)''')

        # Creates relationships between states to the context sources
        graph_session.run('''MATCH (n:n4sch__Instance)-[:IS_TYPE]-(:n4sch__Class{n4sch__name: "State"})
        MATCH (m:n4sch__Instance)-[:IS_TYPE]-(:n4sch__Class)-[:n4sch__SCO]-(:n4sch__Class{n4sch__name:"Context"})
        WITH m, n
        FOREACH(x in CASE WHEN n.source=m.n4sch__name THEN [1] ELSE [] END |    MERGE (m)-[r:YIELDS_STATE]-(n)
        ON CREATE SET r.time=[])''')

        print("Rules embedding to the anomaly knowledge graph complete.")
    except:
        print("Cannot establish connection to graph database!")
        print(sys.exc_info()[0])
        raise
    finally:
        graph_session.close()
    return
#rules_to_graph()