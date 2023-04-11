#!/usr/bin/env python

import time
import threading
import requests
import json
from random import randrange
from flask import Flask, request, jsonify


CONTENT_HEADER = {"Content-Type": "application/json"}
DELIVERY_INTERVAL_SEC = 5
PLC_ENDPOINT_URI = "http://plc:6064/data_in"
turbine_speed_range = 3000
air_temperature_range = 50
power_range = 20000
speed_device_event = threading.Event()
temperature_device_event = threading.Event()
power_device_event = threading.Event()

host_name = "0.0.0.0"
port = 6068
app = Flask(__name__)             # create an app instance

@app.route("/turn_off", methods=['POST'])
def turn_off():
    global speed_device_event,temperature_device_event, power_device_event
    try:
        content = request.json
        if content['device'] == 'power':
            power_device_event.set()
        if content['device'] == 'temperature':
            temperature_device_event.set()
        if content['device'] == 'speed':
            speed_device_event.set()
        print(f"[ALARM] отключен датчик: {content['device']}")
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})


@app.route("/turn_on", methods=['POST'])
def turn_on():
    global speed_device_event,temperature_device_event, power_device_event
    try:
        content = request.json
        if content['device'] == 'power' and power_device_event.is_set():
            power_device_event.clear()
            threading.Thread(
                target=lambda:  power_pushing()).start()
        if content['device'] == 'temperature' and temperature_device_event.is_set():
            temperature_device_event.clear()
            threading.Thread(
                target=lambda:  temperature_pushing()).start()
        if content['device'] == 'speed' and speed_device_event.is_set():
            speed_device_event.clear()
            threading.Thread(
                target=lambda:  speed_pushing()).start()
        print(f"[ATTENTION] датчик перезапущен: {content['device']}")
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})


@app.route("/reset_range_value", methods=['POST'])
def reset():
    global turbine_speed_range, air_temperature_range, power_range
    try:
        content = request.json
        if content['device'] == 'temperature':
            air_temperature_range = content['value']
        if content['device'] == 'power':
            power_range = content['value']
        if content['device'] == 'speed':
            turbine_speed_range = content['value']
        print(f"[ATTENTION] максимальное значение {content['value']} изменено на {content['value']}")
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})


def temperature_pushing():
    global temperature_device_event
    while not temperature_device_event.is_set():
        time.sleep(DELIVERY_INTERVAL_SEC)
        data = {
            "device": "temperature_device",
            "value": randrange(air_temperature_range)
            }
        try:
            response = requests.post(
                PLC_ENDPOINT_URI,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
            print(f"[info] результат отправки данных: {response}")
        except Exception as e:
            print(f"[error] ошибка отправки данных: {e}")

def speed_pushing():
    global speed_device_event
    while not speed_device_event.is_set():
        time.sleep(DELIVERY_INTERVAL_SEC)
        data = {
            "device": "speed_device",
            "value": randrange(turbine_speed_range)
            }
        try:
            response = requests.post(
                PLC_ENDPOINT_URI,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
            print(f"[info] результат отправки данных: {response}")
        except Exception as e:
            print(f"[error] ошибка отправки данных: {e}")

def power_pushing():
    global power_device_event
    while not power_device_event.is_set():
        time.sleep(DELIVERY_INTERVAL_SEC)
        data = {
            "device": "power_device",
            "value": randrange(power_range)
            }
        try:
            response = requests.post(
                PLC_ENDPOINT_URI,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
            print(f"[info] результат отправки данных: {response}")
        except Exception as e:
            print(f"[error] ошибка отправки данных: {e}")


if __name__ == "__main__":
    
    threading.Thread(
                target=lambda: temperature_pushing()).start()
    threading.Thread(
                target=lambda: speed_pushing()).start()
    threading.Thread(
                target=lambda: power_pushing()).start()
    app.run(port = port, host=host_name)
    
   