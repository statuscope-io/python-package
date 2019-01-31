#! /usr/bin/env python3

import requests
import simplejson
from queue import Queue
import argparse
import threading
import time

# A threaded sender/consumer that sends log messages over to Statuscope
class Logger(threading.Thread):
    def __init__(self, token, task_id):
        threading.Thread.__init__(self)
        self.token = token
        self.task_id = task_id
        self.log_queue = Queue()
        self.stop_event = threading.Event()
        self.flush_event = threading.Event()

        print("LogSender [token=%s, taskId=%s]" % (self.token, self.task_id))

    def flush(self):
        """ Triggers a flush event to consume the queue, and then a stop event """

        self.flush_event.set()
        self.stop_event.set()

    def run(self):
        """ Principal thread function, sends logs in the queue or carries out a flush request """

        # Wait time in seconds between each batch of logs
        wait_time = 5

        # Send log messages every 5 seconds, not immediately
        while not self.stop_event.isSet() or (self.flush_event.isSet() and not self.log_queue.empty()):
            print("Sleeping for %s second(s) before next delivery" % (wait_time))

            # Do not wait if there is a flush request, jump to send_logs() directly
            if not self.flush_event.isSet():
                try:
                    # Wait for fractions of the total wait time, to be more responsive when there is a flush request
                    for i in range(100):
                        if not self.flush_event.isSet():
                            time.sleep(wait_time / 100.0)
                except Exception as e:
                    print(str(e))

            self.send_logs()

        print("LogSender is stopping")

    def log(self, log_message):
        print("Enqueuing log message '%s'" % log_message)
        self.log_queue.put(log_message)

    def send_logs(self):
        headers = {'Content-Type':'application/json'}

        while not self.log_queue.empty():
            try:
                log_message = self.log_queue.get()
                data = {'token':self.token, 'message':log_message}

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
