"""
Submitted XX.XX.XXXX
Author: Pashtrik Asani, Gabriella Ilena, Aniruddha Jahagirdar, Meghna Suresh

This module retrieves user input from the mobile application and generates data
based on it. This also routes the results from context analysis to the web interface.
"""
from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
import yaml
import json
import pickle
import os
import time
import datetime
import logging
from contextmodel.contextmodel import contextmodel
from contextmodel.sql_preprocessing import sql_to_graph
from contextmodel.context_analysis import analyze_context
from contextmodel.rules_embedding import rules_to_graph
from contextmodel.health_analysis import accelerometer_analysis, noise_analysis, humidity_analysis, duration_analysis
from contextmodel.health_check import health_check
from prediction.Acc_Prediction import Acc_predict
from prediction.Noise_Prediction import Noise_predict
from prediction.Hum_Prediction import Humidity_predict
from contextreasoning.simulated_data_wrapper import *
from contextreasoning.xdk_data_wrapper import *
from contextreasoning.inductive_contextmodel_reasoning import *

app = Flask(__name__)

# Configure db
db = yaml.full_load(open(r'E:\Meg_Thesis\Thesis__\Ani\IAS_Context-master\IAS_Context-master\db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

# Configure Neo4j db
uri = "neo4j+s://0c5e103c.databases.neo4j.io"
username = "neo4j"
password = "b8HEnf1dgwy6D33Z6nBdjsgsN95KqgT3Ed0lHjvG2J0"
graph_db = "neo4j"

#machine related flags
isMachineOn = True
isStartTimeInitialized = False

@app.route('/', methods=['GET', 'POST'])
def index():
	global isStartTimeInitialized

	if request.method == 'POST':
		# Get the json data and insert into the DataBase
		reqJson = request.get_json()
		if (reqJson["source"] == "XDK"):

			xdk_data = request.json
			data = xdk_data['data']

			acc, temp, noise = data["acceleration"], data["temperature"], data["noise"]
			humidity, pressure = data["humidity"], data["pressure"]

			# algorithm to detect machine running state
			#    if(len(motionDetectionWindow) == 6):
			#        motionDetectionWindowAverage = np.sum(motionDetectionWindow)/len(motionDetectionWindow)
			#        upperLimit = motionDetectionWindowAverage + 100
			#        lowerLimit = motionDetectionWindowAverage - 100
			#        motionDetectionWindow.pop(0)

			#        if( lowerLimit <=  acc <= upperLimit):
			#            isMachineOn = False
			#        else:
			#            #send data only if the machine state is determined as Running
			#            isMachineOn = True
			isMachineOn = True
			temp = float(temp / 1000)
			humidity = float(humidity / 100)
			noise = float(20 * math.log10((noise * math.pow(10, 1.9) * math.pow(10, 6)) / 20))
			timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

			###write new data to CSV
			xdk_file = r"C:\\Users\\meghn\\Dropbox\\Data.csv"
			with open(xdk_file, 'a', newline='') as f:
				writer = csv.writer(f)
				writer.writerow([timeStamp.strip('"'), acc, temp, noise, humidity, pressure])
				f.close()

			#####send machine_start_time to generate data and trigger data generation once
			if isStartTimeInitialized == False:
				logging.warning('Receiving new data from XDK sensor')
				machine_start_time = datetime.datetime.now()
				isStartTimeInitialized = True
				generate_data(machine_start_time)

			return 'Success_XDK'

		elif (reqJson['nameValuePairs']['mode'] == False):
			phase = reqJson['nameValuePairs']['phase']
			sensor = reqJson['nameValuePairs']['sensor']
			desiredValueType = reqJson['nameValuePairs']['desiredValueType']
			desiredValue = reqJson['nameValuePairs']['desiredValue']
			observedValue = reqJson['nameValuePairs']['observedValue']

			range_data = len(phase)
			print('Request json string is: {}'.format(reqJson))

			cur = mysql.connection.cursor()

			# stores the data into MySQL Database sensordata
			for item in range(range_data):
				cur.execute(
					"INSERT INTO sensordata (phase, sensor, desired_value_type, desired_value, observed_value) VALUES (%s,%s,%s,%s,%s)",
					(phase[item], sensor[item], desiredValueType[item], desiredValue[item], observedValue[item]))
				mysql.connection.commit()

			cur.close()
			return "Success!!!"
		else:

			# creates ContextModel and fetches the result
			c = contextmodel(app, db, reqJson, mysql)
			result = c.getresult()
			subresult = c.getsubresult()
			resultpass = c.getresultpass()

			# creates JSON with the results
			jsondata = {}
			jsondata['result'] = result
			jsondata['subresult'] = subresult
			jsondata['passresult'] = resultpass

			# stores result into pickle
			filename = os.path.dirname(__file__) + "\\contextmodel\\contextdata\\Result\\contextresultjson.txt"
			with open(filename, "wb") as fp:  # Pickling
				pickle.dump(jsondata, fp)
		return "Success!!!"
	else:
		push_xdk_data()
		# Exports sql data to .csv
		t0 = time.process_time()
		out_path = "C:\\Users\\meghn\\Dropbox\\context_data.csv"
		sql_to_graph(uri=uri, username=username, password=password, file_path=out_path,
					 db_name=graph_db)
		t1 = time.process_time() - t0
		print("Export finished in ", t1, "seconds.")


		Acc_predict()
		Noise_predict()
		Humidity_predict()

		return render_template('index.html')

@app.route("/abnormalitydetection")
def display_ontological_reasoning():
    push_xdk_data()
    problem_components= [["results" , inductive_context_reasoning()],
                         ["timestamp" , datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]

    return render_template('abnormality_detection.html', pc=problem_components)

@app.route('/diagnosis_result')
def show_analysis_results():
	result = analyze_context(uri=uri, username=username, password=password, db_name=graph_db)
	return render_template('diagnosis.html', result=result)


@app.route('/usage')
def show_usage():
	result = analyze_context(uri=uri, username=username, password=password, db_name=graph_db)
	return render_template('usage.html', result=result)


@app.route('/context_model')
def show_viz():
	return render_template('model_visualization.html')

#Analysis health check and passes all values to web page when called 
@app.route('/health_analysis')
def health_analysis():
	acc = accelerometer_analysis(uri=uri, username=username, password=password, db_name=graph_db)
	noise = noise_analysis(uri=uri, username=username, password=password, db_name=graph_db)
	hum = humidity_analysis(uri=uri, username=username, password=password, db_name=graph_db)
	duration = duration_analysis(uri=uri, username=username, password=password, db_name=graph_db)
	return render_template('health_analysis.html', acc=acc, noise=noise, hum=hum, duration=duration)

#Plredicts graph and shows analysis for predicted values of accelerometer, noise and humidity
@app.route('/Health_Status')
def health_status():
	Acc_predict()
	Noise_predict()
	Humidity_predict()
	hc = health_check(uri=uri, username=username, password=password, db_name=graph_db)
	return render_template('health_status.html', hc=hc)

# Run this to embed the state combinations as rules
@app.route('/embed_rules')
def embed_rules():
	rules_to_graph(uri=uri, username=username, password=password, db_name=graph_db)
	return "Rules embedding complete."


@app.route("/contextresult")
def sendresultjson():
	# shows the result of the contextmodel if it's available
	try:
		filename = os.path.dirname(__file__) + "\\contextmodel\\contextdata\\Result\\contextresultjson.txt"
		with open(filename, "rb") as fp:
			jsondata = pickle.load(fp)
	except Exception:
		jsondata = []
	json_data = json.dumps(jsondata)
	print("data deleted")
	try:
		filename = os.path.dirname(__file__) + "\\contextmodel\\contextdata\\Result\\contextresultjson.txt"
		os.remove(filename)
		print("data deleted")
	except Exception:
		pass
	return json_data


@app.route("/deletecontextresult")
def getdeletejson():
	# deletes the contextresult, is used when application has already fetched the result
	print("data deleted")
	try:
		filename = os.path.dirname(__file__) + "\\contextmodel\\contextdata\\Result\\contextresultjson.txt"
		os.remove(filename)
		print("data deleted")
	except Exception:
		pass


@app.route("/contextmodelcheck")
def checkcontextmodel():
	# experimental, only for programmer, if he wants to check if the contextmodel works without the need of the application
	reqJson = {'nameValuePairs': {'mode': 'true', 'diagnosisMode': 'Complete Short Program', 'phase': [1, 1],
								  'sensor': ['Drucksensor', 'Drucksensor'],
								  'desiredValueType': ['greaterOrEqual', 'lowerOrEqual'], 'desiredValue': [20, 5],
								  'observedValue': [58, 58], 'time': ['dd', '32'], 'unit': ['23', '23']}}
	c = contextmodel(app, db, reqJson, mysql)
	result = c.getresult()
	subresult = c.getsubresult()
	resultpass = c.getresultpass()
	jsondata = {}
	jsondata['result'] = result
	jsondata['subresult'] = subresult
	jsondata['passresult'] = resultpass
	filename = os.path.dirname(__file__) + "\\contextmodel\\contextdata\\Result\\contextresultjson.txt"
	with open(filename, "wb") as fp:  # Pickling
		pickle.dump(jsondata, fp)
	return jsondata


if __name__ == '__main__':
	# app.run(host="0.0.0.0", port=5000, debug=True)
	logging.basicConfig(filename="C:\\Users\\meghn\\Dropbox\\log.log",
						level=logging.INFO)
	logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

	logger = logging.getLogger("server")
	logger.info('Starting Server....')
	app.run(port=5000, debug=True)
