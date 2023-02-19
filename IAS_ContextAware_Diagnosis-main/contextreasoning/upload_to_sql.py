"""
Author: Meghna Suresh

This module is used to push the latest simulation of internal sensor data generated to the SQL database.
"""
import pickle
import os
from cmath import phase
import mysql.connector
import sqlalchemy
from neo4j import GraphDatabase
import logging
from contextreasoning.sql_preprocessing_latest_data import *

mysql_host = 'localhost'
mysql_user = 'root'
mysql_password = 'root1234567890'
mysql_db = 'test'

mydb = mysql.connector.connect(
    host=mysql_host,
    user=mysql_user,
    password=mysql_password,
    database=mysql_db
)

mycursor = mydb.cursor()

context_internal_dictionary = {
    "Pump Out Program": ["Water_Level", "Exit_Water_Flow"],
    "Complete Short Program": [""],
    "Fan Program": ["Loudness", "Vibration", "Mass_Air_Flow"],
    "Drum Motor Program": ["Loudness", "Vibration", "Rotation_Speed"],
    "Door Lock Program": ["Pressure", "Lock"],
    "Water Inlet Program": ["Water_Level", "Entrance_Water_Flow", "Liquid", "Water_Hardness"],
    "Long Time Check": ["Laundry_Fill_Level", "Laundry_Weight", "Washing_Powder_Fill_Level", "Water_Hardness",
                        "Temperature", "Usage_Frequency", "Used_Modes", "Washing_Powder"]
}

process_dict = [
    "soak_process",
    "wash_process",
    "rinse_process",
    "spin_process",
    "drain_process"
]


def uploadSimulatedNewContext():
    valid = 1
    mycursor = mydb.cursor()

    for index, item in enumerate(context_internal_dictionary):
        for context_item in context_internal_dictionary[item]:
            for phase in range(1, 6):
                for process in process_dict:
                    filename = ""
                    try:
                        if (item != "Long Time Check"):
                            filename = os.path.dirname(os.path.abspath(
                                __file__)) + "\\contextdata" + "\\" + item + "\\" + context_item + "\\" + context_item + "_Ph" + str(
                                phase) + "_" + process + ".txt"
                        elif (item == "Long Time Check" and phase == 1):
                            filename = os.path.dirname(os.path.abspath(
                                __file__)) + "\\contextdata" + "\\" + item + "\\" + context_item + "\\" + context_item + "_" + process + ".txt"
                        with open(filename, "rb") as fp:
                            valuelist = pickle.load(fp)
                            unit = pickle.load(fp)
                            timelist = pickle.load(fp)
                        for i, value in enumerate(valuelist):
                            mycursor.execute(
                                "INSERT INTO graphcontextdata (valid, diagnosisMode, phase, datasource, observed_value, time, unit) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                (str(valid), item, str(phase), context_item, str(value), str(timelist), unit))
                            mydb.commit()
                    except Exception:
                        pass
    print("upload to SQL done.")
    logging.warning('upload to SQL done.')

    sql_uri = 'mysql://root:root1234567890@localhost:3306/test'
    engine = sqlalchemy.create_engine(sql_uri)
    out_path = r"C:\\Users\\meghn\\Dropbox\\test_data.csv"
    #uri = "bolt://localhost:7687/"
    uri = "neo4j+s://e4d7fc5b.databases.neo4j.io"
    username = "neo4j"
    #password = "test_dbms"
    password = "L7iVdHaCY9NobsdWaB-8vohYVXEXf_ycVXmlOqQtWxk"
    graph_db = "neo4j"
    graph_driver = GraphDatabase.driver(uri, auth=(username, password))
    graph_session = graph_driver.session(database=graph_db)

    latest_sql_to_graph(graph_session, engine, out_path)
    mycursor.close()


if __name__ == '__main__':
    uploadSimulatedNewContext()