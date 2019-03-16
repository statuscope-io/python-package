#! /usr/bin/env python3

import requests
import simplejson
from queue import Queue
import argparse
import threading
import time

class LoggerConfig():
    def __init__(self):
        self.logs_enabled = False
        self.destination = 'production'
        self.component = None

    def enable_logs(self):
        self.logs_enabled = True

    def set_component(self, component):
        if isinstance(component, str):
            self.component = component

    def get_component(self):
        return self.component

    def disable_logs(self):
        self.logs_enabled = False

    def is_logs_enabled(self):
        return self.logs_enabled

    def send_to_staging(self):
        self.destination = 'staging'

    def is_sending_to_staging(self):
        return self.destination == 'staging'

    def send_to_production(self):
        self.destination = 'production'

    def is_sending_to_production(self):
        return self.destination == 'production'

    def send_to_test(self):
        self.destination = 'test'

    def is_sending_to_test(self):
        return self.destination == 'test'

# A threaded sender/consumer that sends log messages over to Statuscope
class Logger(threading.Thread):
    def __init__(self, token, task_id, config=None):
        threading.Thread.__init__(self)
        self.token = token
        self.task_id = task_id
        self.log_queue = Queue()
        self.stop_event = threading.Event()
        self.flush_event = threading.Event()

        # Read the config and set internal variables
        # If no config is given, create a default one
        if config:
            self.config = config
        else:
            self.config = LoggerConfig()

        self.base_url = ''
        if self.config.is_sending_to_production():
            self.base_url = 'https://api.statuscope.io'
        elif self.config.is_sending_to_staging():
            self.base_url = 'https://staging.statuscope.io'
        elif self.config.is_sending_to_test():
            self.base_url = 'http://localhost:3000'
        else:
            self._log("ERROR: Shall send logs either to production, to staging, or to test. Destination invalid.")

        self._log("LogSender [token=%s, taskId=%s]" % (self.token, self.task_id))

    def _log(self, message):
        '''
        Internal log method
        '''
        if self.config.is_logs_enabled():
            print(message)

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
            self._log("Sleeping for %s second(s) before next delivery" % (wait_time))

            # Do not wait if there is a flush request, jump to send_logs() directly
            if not self.flush_event.isSet():
                try:
                    # Wait for fractions of the total wait time, to be more responsive when there is a flush request
                    for i in range(100):
                        if not self.flush_event.isSet():
                            time.sleep(wait_time / 100.0)
                except Exception as e:
                    self._log(str(e))

            self.send_logs()

        self._log("LogSender is stopping")

    def debug(self, log_message, component=None):
        self._log("Enqueuing log message '%s:%s:%s'" % ('DEBUG', component, log_message))
        self.log_queue.put({'severity': 'debug', 'component': component, 'message': log_message})

    def info(self, log_message, component=None):
        self._log("Enqueuing log message '%s:%s:%s'" % ('INFO', component, log_message))
        self.log_queue.put({'severity': 'info', 'component': component, 'message': log_message})

    def warn(self, log_message, component=None):
        self._log("Enqueuing log message '%s:%s:%s'" % ('WARN', component, log_message))
        self.log_queue.put({'severity': 'warning', 'component': component, 'message': log_message})

    def error(self, log_message, component=None):
        self._log("Enqueuing log message '%s:%s:%s'" % ('ERROR', component, log_message))
        self.log_queue.put({'severity': 'error', 'component': component, 'message': log_message})

    def alert(self, log_message, component=None):
        self._log("Enqueuing log message '%s:%s:%s'" % ('ALERT', component, log_message))
        self.log_queue.put({'severity': 'alert', 'component': component, 'message': log_message})

    def send_logs(self):
        headers = {'Content-Type':'application/json'}

        while not self.log_queue.empty():
            try:
                log_item = self.log_queue.get()

                # Verify queue element
                if not isinstance(log_item, dict):
                    self._log('Queue element is not a dict, skipping.')
                    continue
                elif not 'message' in log_item or not 'severity' in log_item:
                    self._log('Log element does not have message and/or severity field')
                    continue

                # Set obligatory fields
                data = {'token':self.token, 'severity': log_item['severity'], 'message': log_item['message'], 'seqid': int(time.time() * 1000.0)}
                # Set component fields; if there is one given in the (debug|info|warning|error|alert) call, it takes
                # preceence, if not, we check if there has been a global one set through the set_component() call
                if 'component' in log_item and log_item['component']:
                    self._log("There is a component field in the log call")
                    data['component'] = log_item['component']
                elif self.config.get_component():
                    self._log("A global component value has been set in the configuration")
                    data['component'] = self.config.get_component()
                else:
                    self._log("Neither log call nor configuration has a component field")

                task_address = '{}/tasks/{}'.format(self.base_url, self.task_id)
                r = requests.post(task_address, data=simplejson.dumps(data), headers=headers)

                # Print only first 100 characters, since successful responses are shorter
                self._log("Server returned: {}".format(r.text[:100]))

                # Access response fields and values
                if r.json()['result'] == 'OK':
                    self._log('Success')
                else:
                    self._log('Failure')

            except requests.exceptions.ConnectionError as ConnErr:
                self._log("Cannot connect to server")
                return False

            except simplejson.scanner.JSONDecodeError as DecodeErr:
                self._log("Cannot decode server response")
                return False
