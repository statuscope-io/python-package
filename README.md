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
    log_sender.daemon = True
    log_sender.start()

    counter = 0
    while True:
        counter = counter + 1

        try:
            time.sleep(1)

            log_sender.add_log("Here is a log %s" % counter)

        except KeyboardInterrupt:
            print("Ctrl-C received, exiting...")
            sys.exit()
```

Then to update a log task,

```bash
python3 test.py --token cfa0d2ed --task_id QbZJjD2u3uzFvTYAM
```

