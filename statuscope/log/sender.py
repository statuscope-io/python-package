#! /usr/bin/env python3

import requests
import simplejson
from queue import Queue
import argparse
from threading import Thread
import time

# A threaded sender/consumer that sends log messages over to Statuscope
class LogSender(Thread):
    def __init__(self, token, task_id):
        Thread.__init__(self)
        self.token = token
        self.task_id = task_id
        self.log_queue = Queue()

        print("LogSender [token=%s, taskId=%s]" % (self.token, self.task_id))

    def run(self):

        # Send log messages every 5 seconds, not immediately
        while True:
            wait_time = 5
            print("Sleeping for %s second(s) before next delivery" % (wait_time))
            time.sleep(wait_time)
            self.send_logs()

        print("LogSender is stopping")

    def add_log(self, log_message):
        print("Enqueuing log message '%s'" % log_message)
        self.log_queue.put(log_message)

    def send_logs(self):
        headers = {'Content-Type':'application/json'}

        while not self.log_queue.empty():
            try:
                log_message = self.log_queue.get()
                data = {'token':self.token, 'status':'OK', 'message':log_message}

                task_address = 'https://staging.statuscope.io/tasks/{}'.format(self.task_id)
                r = requests.post(task_address, data=simplejson.dumps(data), headers=headers)

                # Print only first 100 characters, since successful responses are shorter
                print("Server returned: {}".format(r.text[:100]))

                # Access response fields and values
                if r.json()['result'] == 'OK':
                    print('Success')
                else:
                    print('Failure')

            except requests.exceptions.ConnectionError as ConnErr:
                print("Cannot connect to server")
                return False

            except simplejson.scanner.JSONDecodeError as DecodeErr:
                print("Cannot decode server response")
                return False

