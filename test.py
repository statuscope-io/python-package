
import argparse
import time
import sys
import random

from statuscope.logger import Logger
from statuscope.logger import LoggerConfig

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sends logs to Statuscope.io')
    parser.add_argument('-t',
                        '--token',
                        help='API token or task-specific token',
                        required=True)
    parser.add_argument('-i',
                        '--task_id',
                        help='Task ID',
                        required=True)
    args = parser.parse_args()

    # Enable logs and send to staging server at staging.statuscope.io
    log_config = LoggerConfig()
    log_config.enable_logs()
    log_config.send_to_test()
    log_config.set_component('staging')

    log_sender = Logger(args.token, args.task_id, log_config)
    log_sender.start()

    # We'll generate some silly log messages because test data is usually so boring
    objects = [ 'plane', 'bike', 'book', 'icecream', 'dog' ]
    colors = [ 'yellow', 'green', 'red', 'black', 'pink', 'white' ]
    components = [ 'auth', 'backend', 'frontend', 'db', 'payment' ]
    severities = [ 'debug', 'info', 'warning', 'error', 'alert' ]

    counter = 0
    while True:
        counter = counter + 1

        try:
            time.sleep(1)

            severity = random.choice(severities)
            component = random.choice(components)
            color = random.choice(colors)
            object = random.choice(objects)

            if severity == 'debug':
                log_sender.debug("Log %s: I have a %s %s" % (counter, color, object), component)
            elif severity == 'info':
                log_sender.info("Log %s: I have a %s %s" % (counter, color, object))
            elif severity == 'warning':
                log_sender.warn("Log %s: I have a %s %s" % (counter, color, object), component)
            elif severity == 'error':
                log_sender.error("Log %s: I have a %s %s" % (counter, color, object))
            elif severity == 'alert':
                log_sender.alert("Log %s: I have a %s %s" % (counter, color, object), component)


        except KeyboardInterrupt:
            print("Ctrl-C received, exiting...")
            log_sender.flush()
            try:
                log_sender.join()
            except Exception as e:
                print(str(e))
            sys.exit()
