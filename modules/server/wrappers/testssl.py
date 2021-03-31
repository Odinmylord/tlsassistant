import json
import subprocess
import sys
from os import sep, devnull, path, remove
import uuid
import logging


class Testssl:
    def __init__(self):
        self.__testssl = f"dependencies{sep}3.0.4{sep}testssl.sh-3.0.4{sep}testssl.sh"
        self.__input_dict = {}
        self.__scan_dict = {}

    def validate_ip(self, s):
        a = s.split(".")
        if len(a) != 4:
            return False
        for x in a:
            if not x.isdigit():
                return False
            i = int(x)
            if i < 0 or i > 255:
                return False
        return True

    def input(self, **kwargs):
        self.__input_dict = kwargs

    def output(self, **kwargs) -> dict:
        return (
            self.__scan_dict[kwargs["hostname"]]
            if "hostname" in kwargs
            else self.__scan_dict
        )

    def run(self, **kwargs):
        self.input(**kwargs)
        if "hostname" not in self.__input_dict:
            raise AssertionError("IP or hostname args not found.")
        else:
            self.__scan(
                str(self.__input_dict["hostname"]),
                force=self.__input_dict["force"]
                if "force" in self.__input_dict
                else False,
                one=self.__input_dict["one"] if "one" in self.__input_dict else True,
            )
        return self.output(hostname=self.__input_dict["hostname"])

    def __scan(self, hostname: str, force: bool, one: bool) -> dict:
        return self.__scan_hostname(hostname, force, one)

    def __scan_hostname(self, hostname: str, force: bool, one: bool) -> dict:
        # scan
        if force:
            logging.debug("Starting testssl analysis")
            file_name = uuid.uuid4().hex
            logging.debug(
                f"Scanning {hostname}, saving result to temp file {file_name}"
            )
            with open(devnull, "w") as null:
                cmd = [
                    "bash",
                    self.__testssl,
                    f"--jsonfile=dependencies{sep}{file_name}.json",
                ]
                if one and not self.validate_ip(hostname):
                    logging.debug("Scanning with --IP=one..")
                    cmd.append(f"--ip=one")
                cmd.append(hostname)
                subprocess.check_call(
                    cmd,
                    stderr=sys.stderr,
                    stdout=(
                        sys.stdout
                        if logging.getLogger().isEnabledFor(
                            logging.DEBUG
                        )  # if the user asked for debug mode, let him see the output.
                        else null  # else /dev/null
                    ),
                )
                if path.exists(f"dependencies{sep}{file_name}.json"):
                    with open(
                            f"dependencies{sep}{file_name}.json", "r"
                    ) as file:  # load temp file
                        data = file.read()
                        self.__scan_dict[hostname] = json.loads(data)
                    remove(f"dependencies{sep}{file_name}.json")
        else:
            if hostname not in self.__scan_dict:
                self.__scan_dict[hostname] = self.__scan_hostname(
                    hostname, force=True, one=one
                )
        return self.__scan_dict[hostname]