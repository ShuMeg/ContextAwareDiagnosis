#make a POST request
import requests

while(True):
    
    dictToSend = ({
               "source": "XDK", 
               "data": 
                       {
                        "temperature": 22.4  * 1000,
                        "acceleration": 4321 , 
                        "humidity": 78 * 100 ,
                        "pressure": 101000 ,
                        "noise": 2.6e-5
                        } 
               })
    
    
    #res = requests.post('http://192.168.100.5:5000/', json=dictToSend)
    res = requests.post('http://localhost:5000/', json=dictToSend)
    print('response from server:',res.text)
dictFromServer = res.json()
