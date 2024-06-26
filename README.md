# vmwarelog

vmwarelog is a tool to pull VMware vCenter logs based on time and type filters. It is better than collecting syslog with all of the noise.

## Usage

- Clone thos repository
- Use your preferred virtual environment
- Install dependencies via pip: `pip install -r requirements.txt`
- Run the script via Python by providing target vCenter instance and log output path: `python3 src/main.py -t vcenter.domain.tld -o /var/log/vcenter.log`
- You can make use of the configuration file for automation.

## Help

```bash
usage: main.py [-h] [-t VCENTER] [-p PORT] [-o OUTPUT] [-c CONF]

vmwarelog (0.1) is a tool to pull VMware vCenter logs based on time and type filters. It is better than collecting syslog with all of the noise.

optional arguments:
  -h, --help            show this help message and exit
  -t VCENTER, --target VCENTER
                        VMware vCenter host IP or FQDN
  -p PORT, --port PORT  VMware vCenter host port to connect (Default: 443)
  -o OUTPUT, --output OUTPUT
                        The file where vCenter logs are written
  -c CONF, --conf CONF  Path to configuration file (Default: conf.py)
```
