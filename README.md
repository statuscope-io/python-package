# python-package
Source code of the Python package that is on PyPI

# Install & Update
```python
sudo pip3 install --upgrade statuscope
```

# Example

Here is a sample use of the package.

```python
import argparse
import time
import sys
import random

from statuscope.logger import Logger

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

    log_sender = Logger(args.token, args.task_id)
    log_sender.start()

    # We'll generate some silly log messages because test data is usually so boring
    objects = [ 'plane', 'bike', 'book', 'icecream', 'dog' ]
    colors = [ 'yellow', 'green', 'red', 'black', 'pink', 'white' ]

    counter = 0
    while True:
        counter = counter + 1

        try:
            time.sleep(1)

            log_sender.log("Log %s: I have a %s %s" % (counter, random.choice(colors), random.choice(objects)))

        except KeyboardInterrupt:
            print("Ctrl-C received, exiting...")
            log_sender.flush()
            try:
                log_sender.join()
            except Exception as e:
                print(str(e))
            sys.exit()
```

Then to update a log task,

```bash
python3 test.py --token cfa0d2ed --task_id QbZJjD2u3uzFvTYAM
```
