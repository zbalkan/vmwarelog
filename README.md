# vmwarelog

vmwarelog is a tool to pull vmware logs based on time and type filters. It is better than collecting syslog with all of the noise.

## Usage

- Clone thos repository
- Use your preferred virtualenvironment
- Install dependencies via pip: `pip install -r requirements.txt`
- Run the script via Python by providing target: `python3 src/main.py -t vcenter.domain.tld`

## Help

```python
usage: main.py [-h] -t HOST -p PORT

vmwarelog (0.1) is a tool to pull vmware logs based on time and type filters. It is better than collecting syslog with all of the noise.

options:
  -h, --help            show this help message and exit
  -t HOST, --target HOST, --host HOST
                        VMware vCenter host IP or FQDN
  -p PORT, --port PORT  VMware vCenter host port to connect
```

