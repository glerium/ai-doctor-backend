import requests
import sys

url = 'http://localhost/chat'

first = True
while True:
    msg = input()
    data = {
        'input': msg,
        'first': first
    }
    if not first:
        data['patient_id'] = patient_id
    ret = requests.post(url, json=data)
    print(ret.json())
    ret = ret.json()
    first = False
    patient_id = int(ret['patient_id'])
    print(patient_id)
    if ret['success'] == False:
        break
