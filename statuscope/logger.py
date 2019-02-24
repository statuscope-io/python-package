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

    def enable_logs(self):
        self.logs_enabled = True

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
    def __init__(self, token, task_id, config):
        threading.Thread.__init__(self)
        self.token = token
        self.task_id = task_id
        self.log_queue = Queue()
        self.stop_event = threading.Event()
        self.flush_event = threading.Event()

        # Read the config and set internal variables
        self.config = config
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

    def debug(self, log_message):
        self._log("Enqueuing log message '%s:%s'" % ('DEBUG', log_message))
        self.log_queue.put(('debug', log_message))

    def info(self, log_message):
        self._log("Enqueuing log message '%s:%s'" % ('INFO', log_message))
        self.log_queue.put(('info', log_message))

    def warn(self, log_message):
        self._log("Enqueuing log message '%s:%s'" % ('WARN', log_message))
        self.log_queue.put(('warning', log_message))

    def error(self, log_message):
        self._log("Enqueuing log message '%s:%s'" % ('ERROR', log_message))
        self.log_queue.put(('error', log_message))

    def alert(self, log_message):
        self._log("Enqueuing log message '%s:%s'" % ('ALERT', log_message))
        self.log_queue.put(('alert', log_message))

    def send_logs(self):
        headers = {'Content-Type':'application/json'}

        while not self.log_queue.empty():
            try:
                log_message = self.log_queue.get()

                # Verify queue element
                if not isinstance(log_message, tuple):
                    self._log('Queue element is not a tuple, skipping.')
                    continue
                elif len(log_message) != 2:
                    self._log('Log element does not have severity and/or message, or has invalid size')
                    continue

                data = {'token':self.token, 'severity': log_message[0], 'message': log_message[1], 'seqid': int(time.time() * 1000.0)}

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
