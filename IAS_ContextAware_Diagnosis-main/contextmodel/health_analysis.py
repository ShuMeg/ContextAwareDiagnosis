'''
Submitted 22.04.2022
Author: Aniruddha Jahagirdar

This module accesses the neo4j grap database from querying and updates to analyze context values for healh check program, producing relevant
states, and getting the appropriate message from the application model for health analysis application.
'''

from neo4j import GraphDatabase

# Configure Neo4j db
uri = "neo4j+s://0c5e103c.databases.neo4j.io"
username = "neo4j"
password = "b8HEnf1dgwy6D33Z6nBdjsgsN95KqgT3Ed0lHjvG2J0"
graph_db = "neo4j"

#Gets average values of accelerometer reading for the specified spin
def get_accvalues(session, spin_num):
    query = """MATCH (n:n4sch_XDKAccValue{n4sch_Spin: $spin})
    RETURN AVG(apoc.convert.toInteger(n.n4sch_Value))"""
    value_result = session.run(query, spin=spin_num)
    return value_result

#Gets average values of noise reading for the specified spin
def get_noisevalues(session, spin_num):
    query = """MATCH (n:n4sch_XDKNoiseValue{n4sch_Spin: $spin})
    RETURN AVG(apoc.convert.toInteger(n.n4sch_Value))"""
    value_result = session.run(query, spin=spin_num)
    return value_result

#Gets average values of humidity reading for the specified spin
def get_humvalues(session, spin_num):
    query = """MATCH (n:n4sch_XDKHumidityValue{n4sch_Spin: $spin})
    RETURN AVG(apoc.convert.toInteger(n.n4sch_Value))"""
    value_result = session.run(query, spin=spin_num)
    return value_result

#Gets expectect duration value for the specified spin
def get_durationvalues(session, spin_num):
    query = """MATCH (n:n4sch_Duration_Value{spin: $spin})
    WHERE n.n4sch_name = 'Expected_Duration'
    RETURN (toInteger(n.n4sch_Value))"""
    value_result = session.run(query, spin=spin_num)
    return value_result

#Gets actual duration value for the specified spin
def get_actualdurationvalues(session, spin_num):
    query = """MATCH (n:n4sch_Duration_Value{spin: $spin})
    WHERE n.n4sch_name = 'Actual_Duration'
    RETURN (toInteger(n.n4sch_Value))"""
    value_result = session.run(query, spin=spin_num)
    return value_result

#Gets Load weight for the specified spin
def get_loadvalues(session, spin_num):
    query = """MATCH (n:n4sch__LoadWeight{spin: $spin})
    RETURN DISTINCT n.weight, n.unit"""
    value_load = session.run(query, spin=spin_num)
    return value_load

#Gets Wash type for the specified spin
def get_washtype(session, spin_num):
    query = """MATCH (n:n4sch__LoadWeight{spin: $spin})
    RETURN DISTINCT n.wash_mode"""
    wash_type = session.run(query, spin=spin_num)
    return wash_type

#Sets anomaly as actuator, control or sensor
def check_anomaly(session, states):
    # Format list of dictionaries to match the Cypher query format
    defect = session.run("""
        WITH $states as nodes
        UNWIND nodes as node
        MATCH (st:n4sch__Instance{n4sch__name:node.name}) - [:HAS_COMBINATION] - (co) - [:CAUSES_ANOMALY] - (a)
        WITH a, co, size(nodes) as inputCnt, count(DISTINCT st) as cnt
        WHERE cnt = inputCnt
        RETURN a.n4sch__name, co.combo_id
    """, states=states)
    return defect

#Retrieves anomaly message and its components based on anomaly  
def get_anomaly_message(session, program, message_cause, message_type, source):
    if message_type.lower() == "error":
        if "actuator" in message_cause.lower():
            component = "Actuator"
        elif "machine overloaded" in message_cause.lower():
            component = "Actuator"
        elif "load sense defect" in message_cause.lower():
            component = "Control"
        else:
            component = ""
        #fetches error message from neo4j database if anomaly is detcted
        message = session.run("""WITH $message_cause as causes
            UNWIND causes as mcause
            MATCH (e:n4sch__Instance)-[:IS_TYPE]-(:n4sch__Class{n4sch__name:$component})
            WHERE e.mode = $program AND e.source = $source
            WITH collect(e.n4sch__name) as components, mcause
            MATCH (m) - [:IS_TYPE] - (:n4sch__Class{n4sch__name:"Message"})
            WHERE mcause in m.cause
            RETURN replace(m.message, "-foo-", apoc.text.join(components, ', '))""",
                    component=component, program=program,
                    message_cause=message_cause, source=source)
    elif message_type.lower() == "normal":
        #fetches normal message from neo4j database if anomaly is none
        message = session.run("""WITH ["Actuator", "Sensor", "Control"] as components
            UNWIND components as component
            MATCH (e:n4sch__Instance{mode:$program})-[:IS_TYPE]-(:n4sch__Class{n4sch__name:component})
            WHERE e.mode = $program AND e.source = $source
            WITH collect(e.n4sch__name) as components
            MATCH (m:n4sch__Instance{n4sch__name:"Normal message"}) - [:IS_TYPE] - (:n4sch__Class{n4sch__name:"Message"})
            RETURN replace(m.message, "-foo-", apoc.text.join(components, ', '))""",
                    program=program, source=source)
    elif message_type.lower() == "overload":
        #fetches overload message from neo4j database if machine is overloaded
        message = session.run("""MATCH (n:n4sch__Instance)
            WHERE n.n4sch__name = 'Overload Message'
            RETURN n.message""")
    else:
        pass
    return message

#Function to analysis accelerometer readings
def accelerometer_analysis(uri, username, password, db_name):
    # Connect to graph database
    graph_driver = GraphDatabase.driver(uri, auth=(username, password))
    graph_session = graph_driver.session(database=db_name)

    # Get program names
    query_res = graph_session.run("""MATCH (:n4sch__Class{n4sch__name:"Context"})<-[:n4sch__SCO]-(m)-[:IS_TYPE]-(n:n4sch__Instance) WHERE size(n.mode) > 2 
            RETURN DISTINCT n.mode""")
    programs = list()
    for item in query_res:
        programs.append(item[0])

    for selected_program in programs:
        program_results = list()
        if selected_program == "Health Check":
            # Get number of spins
                query_res1 = graph_session.run("""MATCH (:n4sch__Instance{n4sch__name:"Load_Weight"})-[:LOAD_WEIGHT]->(n:n4sch__LoadWeight) WHERE size(n.spin) > 2 
            RETURN DISTINCT n.spin""")
                spins = list()
                for item in query_res1:
                    spins.append(item[0])
                for selected_spin in spins:
                    if selected_spin == "Spin_1":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average accelerometer reading
                        query_value = get_accvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            second_state = list()
                            if item[0] <= 5000:
                                sub_result = 'Balanced'
                                current_state.append({'name': sub_result})
                                second_result = 'Load OK'
                                second_state.append({'name': second_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="error")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source="Unbalanced", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Unbalanced'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                        
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=current_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult1= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_2":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average accelerometer reading
                        query_value = get_accvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            second_state = list()
                            if item[0] <= 4200:
                                sub_result = 'Balanced'
                                current_state.append({'name': sub_result})
                                second_result = 'Load OK'
                                second_state.append({'name': second_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="error")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source="Unbalanced", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Unbalanced'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                       
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=current_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult2= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_3":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average accelerometer reading
                        query_value = get_accvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            second_state = list()
                            if item[0] <= 4200:
                                sub_result = 'Balanced'
                                current_state.append({'name': sub_result})
                                second_result = 'Load OK'
                                second_state.append({'name': second_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="error")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source="Unbalanced", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Unbalanced'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                    
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=current_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult3= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_4":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average accelerometer reading
                        query_value = get_accvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            second_state = list()
                            if item[0] <= 4200:
                                sub_result = 'Balanced'
                                current_state.append({'name': sub_result})
                                second_result = 'Load OK'
                                second_state.append({'name': second_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="error")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source="Unbalanced", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Unbalanced'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                   
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=current_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult4= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_5":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average accelerometer reading
                        query_value = get_accvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            second_state = list()
                            if item[0] <= 4200:
                                sub_result = 'Balanced'
                                current_state.append({'name': sub_result})
                                second_result = 'Load OK'
                                second_state.append({'name': second_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, message_cause=Anomaly, message_type="error")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source="Unbalanced", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Unbalanced'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                     
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=current_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult5= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}   
        else:
            pass
    graph_session.close()
    program_results.append(subresult1)
    program_results.append(subresult2)
    program_results.append(subresult3)
    program_results.append(subresult4)
    program_results.append(subresult5)
    return program_results

def noise_analysis(uri, username, password, db_name):
    # Connect to graph database
    graph_driver = GraphDatabase.driver(uri, auth=(username, password))
    graph_session = graph_driver.session(database=db_name)

    # Get program names
    query_res = graph_session.run("""MATCH (:n4sch__Class{n4sch__name:"Context"})<-[:n4sch__SCO]-(m)-[:IS_TYPE]-(n:n4sch__Instance) WHERE size(n.mode) > 2 
            RETURN DISTINCT n.mode""")
    programs = list()
    for item in query_res:
        programs.append(item[0])
    
    for selected_program in programs:
        program_results = list()
        if selected_program == "Health Check":
            # Get number of spins
                query_res1 = graph_session.run("""MATCH (:n4sch__Instance{n4sch__name:"Load_Weight"})-[:LOAD_WEIGHT]->(n:n4sch__LoadWeight) WHERE size(n.spin) > 2 
            RETURN DISTINCT n.spin""")
                spins = list()
                for item in query_res1:
                    spins.append(item[0])

                for selected_spin in spins:
                    if selected_spin == "Spin_1":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average noise reading    
                        query_value = get_noisevalues(graph_session, selected_spin)
                        value_list = list()
                        second_state = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            msg_list = list()
                            if item[0] <= 80:
                                sub_result = 'Normal'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause=Anomaly, message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Loud'
                                current_state.append({'name': sub_result})
                                # Get Load Weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                      
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult1= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_2":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get avaerage noise reading
                        query_value = get_noisevalues(graph_session, selected_spin)
                        value_list = list()
                        second_state = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            msg_list = list()
                            if item[0] <= 80:
                                sub_result = 'Normal'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause=Anomaly, message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Loud'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                       
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult2= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_3":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average noise reading
                        query_value = get_noisevalues(graph_session, selected_spin)
                        value_list = list()
                        second_state = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            msg_list = list()
                            if item[0] <= 80:
                                sub_result = 'Normal'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause=Anomaly, message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Loud'
                                current_state.append({'name': sub_result})
                                # Get Load Weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                       
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult3= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_4":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average noise reading
                        query_value = get_noisevalues(graph_session, selected_spin)
                        value_list = list()
                        second_state = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            msg_list = list()
                            if item[0] <= 80:
                                sub_result = 'Normal'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause=Anomaly, message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Loud'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                        
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult4= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
                    if selected_spin == "Spin_5":
                        query_load = get_loadvalues(graph_session, selected_spin)
                        load_list = list()
                        for item in query_load:
                            load_list.append(item[0])
                        # Get average noise reading
                        query_value = get_noisevalues(graph_session, selected_spin)
                        value_list = list()
                        second_state = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            msg_list = list()
                            if item[0] <= 80:
                                sub_result = 'Normal'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                                if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause=Anomaly, message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                                else:
                                    msg_list = list()
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, Source="", message_cause="", message_type="normal")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                sub_result = 'Loud'
                                current_state.append({'name': sub_result})
                                # Get load weight
                                query_load = get_loadvalues(graph_session, selected_spin)
                                load_list = list()
                                for item in query_load:
                                    load_list.append(item[0])
                                    if item[0] <= '5.0':
                                        second_result = 'Load OK'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                            # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                            for item in msg:
                                                msg_list.append(item[0])                                                                    
                                    else:
                                        second_result = 'Overloaded'
                                        second_state.append({'name': second_result})
                                        # Check for anomaly based on current states
                                        defect = check_anomaly(session=graph_session, states=second_state)
                                        if defect.peek() is not None:
                                        # Get anomaly message
                                            msg_list = list()
                                            for item in defect:
                                                Anomaly = item[0]
                                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="overload")
                                            for item in msg:
                                                msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult5= {'Spin': selected_spin, 'State': current_state, 'Load': second_state, 'Weight': load_list, 'Message': msg_list}
    graph_session.close()
    program_results.append(subresult1)
    program_results.append(subresult2)
    program_results.append(subresult3)
    program_results.append(subresult4)
    program_results.append(subresult5)
    return program_results

def humidity_analysis(uri, username, password, db_name):
    # Connect to graph database
    graph_driver = GraphDatabase.driver(uri, auth=(username, password))
    graph_session = graph_driver.session(database=db_name)

    # Get program names
    query_res = graph_session.run("""MATCH (:n4sch__Class{n4sch__name:"Context"})<-[:n4sch__SCO]-(m)-[:IS_TYPE]-(n:n4sch__Instance) WHERE size(n.mode) > 2 
            RETURN DISTINCT n.mode""")
    programs = list()
    for item in query_res:
        programs.append(item[0])
    
    for selected_program in programs:
        program_results = list()
        if selected_program == "Health Check":
        # Get number of Spins
                query_res1 = graph_session.run("""MATCH (:n4sch__Instance{n4sch__name:"Load_Weight"})-[:LOAD_WEIGHT]->(n:n4sch__LoadWeight) WHERE size(n.spin) > 2 
            RETURN DISTINCT n.spin""")
                spins = list()
                for item in query_res1:
                    spins.append(item[0])

                for selected_spin in spins:
                    if selected_spin == "Spin_1":
                        # Get average humidity values
                        query_value = get_humvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            if item[0] <= 18:
                                sub_result = 'Not Humid'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                            else:
                                sub_result = 'Humid'
                                current_state.append({'name': sub_result})
                                defect = check_anomaly(session=graph_session, states=current_state)
                                
                            if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                msg_list = list()
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source="Humid", message_cause="", message_type="normal")
                                for item in msg:
                                    msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult1= {'Spin': selected_spin, 'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_2":
                        # Get average humidity values
                        query_value = get_humvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            if item[0] <= 18:
                                sub_result = 'Not Humid'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                            else:
                                sub_result = 'Humid'
                                current_state.append({'name': sub_result})
                                defect = check_anomaly(session=graph_session, states=current_state)
                                
                            if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                msg_list = list()
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source="Humid", message_cause="", message_type="normal")
                                for item in msg:
                                    msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult2= {'Spin': selected_spin, 'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_3":
                        # Get average humidity values
                        query_value = get_humvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            if item[0] <= 18:
                                sub_result = 'Not Humid'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                            else:
                                sub_result = 'Humid'
                                current_state.append({'name': sub_result})
                                defect = check_anomaly(session=graph_session, states=current_state)
                                
                            if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                msg_list = list()
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source="Humid", message_cause="", message_type="normal")
                                for item in msg:
                                    msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult3= {'Spin': selected_spin, 'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_4":
                        # Get average humidity values
                        query_value = get_humvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            if item[0] <= 18:
                                sub_result = 'Not Humid'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                            else:
                                sub_result = 'Humid'
                                current_state.append({'name': sub_result})
                                defect = check_anomaly(session=graph_session, states=current_state)
                                
                            if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                msg_list = list()
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source="Humid", message_cause="", message_type="normal")
                                for item in msg:
                                    msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult4= {'Spin': selected_spin, 'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_5":
                        # Get average humidity values
                        query_value = get_humvalues(graph_session, selected_spin)
                        value_list = list()
                        for item in query_value:
                            value_list.append(item[0])
                            current_state = list()
                            if item[0] <= 18:
                                sub_result = 'Not Humid'
                                current_state.append({'name': sub_result})
                                # Check for anomaly based on current states
                                defect = check_anomaly(session=graph_session, states=current_state)
                            else:
                                sub_result = 'Humid'
                                current_state.append({'name': sub_result})
                                defect = check_anomaly(session=graph_session, states=current_state)
                                
                            if defect.peek() is not None:
                                # Get anomaly message
                                    msg_list = list()
                                    for item in defect:
                                        Anomaly = item[0]
                                    msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                                    for item in msg:
                                        msg_list.append(item[0])
                            else:
                                msg_list = list()
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source="Humid", message_cause="", message_type="normal")
                                for item in msg:
                                    msg_list.append(item[0])
                            # Stores result in dictionary
                            subresult5= {'Spin': selected_spin, 'State': current_state, 'Message': msg_list}
    graph_session.close()
    program_results.append(subresult1)
    program_results.append(subresult2)
    program_results.append(subresult3)
    program_results.append(subresult4)
    program_results.append(subresult5)
    return program_results 

def duration_analysis(uri, username, password, db_name):
    # Connect to graph database
    graph_driver = GraphDatabase.driver(uri, auth=(username, password))
    graph_session = graph_driver.session(database=db_name)

    # Get program names
    query_res = graph_session.run("""MATCH (:n4sch__Class{n4sch__name:"Context"})<-[:n4sch__SCO]-(m)-[:IS_TYPE]-(n:n4sch__Instance) WHERE size(n.mode) > 2 
            RETURN DISTINCT n.mode""")
    programs = list()
    for item in query_res:
        programs.append(item[0])
    
    for selected_program in programs:
        program_results = list()
        if selected_program == "Health Check":
        # Get number of Spins
                query_res1 = graph_session.run("""MATCH (:n4sch__Instance{n4sch__name:"Load_Weight"})-[:LOAD_WEIGHT]->(n:n4sch__LoadWeight) WHERE size(n.spin) > 2 
            RETURN DISTINCT n.spin""")
                spins = list()
                for item in query_res1:
                    spins.append(item[0])

                for selected_spin in spins:
                    if selected_spin == "Spin_1":
                        # Get expected duration value
                        query_value = get_durationvalues(graph_session, selected_spin)
                        for item in query_value:
                            eduration = item[0]
                        # Get actual duration value
                        query_value = get_actualdurationvalues(graph_session, selected_spin)
                        for item in query_value:
                            aduration = item[0]
                        current_state = list()
                        if aduration - eduration < 5:
                            sub_result = 'Duration OK'
                            current_state.append({'name': sub_result})
                            defect = check_anomaly(session=graph_session, states=current_state)
                        else:
                            sub_result = 'Duration Long'
                            current_state.append({'name': sub_result})
                            # Check for anomaly based on current states
                            defect = check_anomaly(session=graph_session, states=current_state)
                        if defect.peek() is not None:
                            # Get anomaly message
                            msg_list = list()
                            for item in defect:
                                Anomaly = item[0]
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                            for item in msg:
                                msg_list.append(item[0])
                        else:
                            msg_list = list()
                            msg = get_anomaly_message(session=graph_session, program=selected_program, source="Duration Long", message_cause="", message_type="normal")
                            for item in msg:
                                msg_list.append(item[0])
                        # Stores result in dictionary
                        subresult1= {'Spin': selected_spin, 'Expected_Duration': eduration, 'Actual_Duration': aduration,'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_2":
                        # Get expected duration value
                        query_value = get_durationvalues(graph_session, selected_spin)
                        for item in query_value:
                            eduration = item[0]
                        # Get actual duration value
                        query_value = get_actualdurationvalues(graph_session, selected_spin)
                        for item in query_value:
                            aduration = item[0]
                        current_state = list()
                        if aduration - eduration < 5:
                            sub_result = 'Duration OK'
                            current_state.append({'name': sub_result})
                            # Check for anomaly based on current states
                            defect = check_anomaly(session=graph_session, states=current_state)
                        else:
                            sub_result = 'Duration Long'
                            current_state.append({'name': sub_result})
                            defect = check_anomaly(session=graph_session, states=current_state)
                        if defect.peek() is not None:
                            # Get anomaly message
                            msg_list = list()
                            for item in defect:
                                Anomaly = item[0]
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                            for item in msg:
                                msg_list.append(item[0])
                        else:
                            msg_list = list()
                            msg = get_anomaly_message(session=graph_session, program=selected_program, source="Duration Long", message_cause="", message_type="normal")
                            for item in msg:
                                msg_list.append(item[0])
                        # Stores result in dictionary
                        subresult2= {'Spin': selected_spin, 'Expected_Duration': eduration, 'Actual_Duration': aduration,'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_3":
                        # Get expected duration value
                        query_value = get_durationvalues(graph_session, selected_spin)
                        for item in query_value:
                            eduration = item[0]
                        # Get actual duration value
                        query_value = get_actualdurationvalues(graph_session, selected_spin)
                        for item in query_value:
                            aduration = item[0]
                        current_state = list()
                        if aduration - eduration < 5:
                            sub_result = 'Duration OK'
                            current_state.append({'name': sub_result})
                            defect = check_anomaly(session=graph_session, states=current_state)
                        else:
                            sub_result = 'Duration Long'
                            current_state.append({'name': sub_result})
                            # Check for anomaly based on current states
                            defect = check_anomaly(session=graph_session, states=current_state)
                        if defect.peek() is not None:
                            # Get anomaly message
                            msg_list = list()
                            for item in defect:
                                Anomaly = item[0]
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                            for item in msg:
                                msg_list.append(item[0])
                        else:
                            msg_list = list()
                            msg = get_anomaly_message(session=graph_session, program=selected_program, source="Duration Long", message_cause="", message_type="normal")
                            for item in msg:
                                msg_list.append(item[0])
                        # Stores result in dictionary
                        subresult3= {'Spin': selected_spin, 'Expected_Duration': eduration, 'Actual_Duration': aduration,'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_4":
                        # Get expected duration value
                        query_value = get_durationvalues(graph_session, selected_spin)
                        for item in query_value:
                            eduration = item[0]
                        # Get actual duration value
                        query_value = get_actualdurationvalues(graph_session, selected_spin)
                        for item in query_value:
                            aduration = item[0]
                        current_state = list()
                        if aduration - eduration < 5:
                            sub_result = 'Duration OK'
                            current_state.append({'name': sub_result})
                            defect = check_anomaly(session=graph_session, states=current_state)
                        else:
                            sub_result = 'Duration Long'
                            current_state.append({'name': sub_result})
                            # Check for anomaly based on current states
                            defect = check_anomaly(session=graph_session, states=current_state)
                        if defect.peek() is not None:
                            # Get anomaly message
                            msg_list = list()
                            for item in defect:
                                Anomaly = item[0]
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                            for item in msg:
                                msg_list.append(item[0])
                        else:
                            msg_list = list()
                            msg = get_anomaly_message(session=graph_session, program=selected_program, source="Duration Long", message_cause="", message_type="normal")
                            for item in msg:
                                msg_list.append(item[0])
                        # Stores result in dictionary
                        subresult4= {'Spin': selected_spin, 'Expected_Duration': eduration, 'Actual_Duration': aduration,'State': current_state, 'Message': msg_list}
                    if selected_spin == "Spin_5":
                        # Get expected duration value
                        query_value = get_durationvalues(graph_session, selected_spin)
                        for item in query_value:
                            eduration = item[0]
                        # Get actual duration value
                        query_value = get_actualdurationvalues(graph_session, selected_spin)
                        for item in query_value:
                            aduration = item[0]
                        current_state = list()
                        if aduration - eduration < 5:
                            sub_result = 'Duration OK'
                            current_state.append({'name': sub_result})
                            defect = check_anomaly(session=graph_session, states=current_state)
                        else:
                            sub_result = 'Duration Long'
                            current_state.append({'name': sub_result})
                            # Check for anomaly based on current states
                            defect = check_anomaly(session=graph_session, states=current_state)
                        if defect.peek() is not None:
                            # Get anomaly message
                            msg_list = list()
                            for item in defect:
                                Anomaly = item[0]
                                msg = get_anomaly_message(session=graph_session, program=selected_program, source=sub_result, message_cause=Anomaly, message_type="Error")
                            for item in msg:
                                msg_list.append(item[0])
                        else:
                            msg_list = list()
                            msg = get_anomaly_message(session=graph_session, program=selected_program, source="Duration Long", message_cause="", message_type="normal")
                            for item in msg:
                                msg_list.append(item[0])
                        # Stores result in dictionary
                        subresult5= {'Spin': selected_spin, 'Expected_Duration': eduration, 'Actual_Duration': aduration,'State': current_state, 'Message': msg_list}
    graph_session.close()
    program_results.append(subresult1)
    program_results.append(subresult2)
    program_results.append(subresult3)
    program_results.append(subresult4)
    program_results.append(subresult5)
    return program_results