import os
from pathlib import Path

from crossplane import build as nginx_build
from crossplane import parse as nginx_parse

from modules.compliance.configuration.configuration_base import ConfigurationMaker
from modules.configuration.configuration import Configuration
from utils.type import WebserverType


class NginxConfiguration(ConfigurationMaker):
    def __init__(self, file: Path = None):
        super().__init__("nginx")
        if file:
            self._load_conf(file)

    # Borrowing this function from Configuration for testing purposes
    def _load_conf(self, file: Path):
        """
        Internal method to load the nginx configuration file.

        :param file: path to the configuration file
        :type file: str
        """
        self.configuration = Configuration(path=str(file), type_=WebserverType.NGINX, process=False).get_conf()

    def add_configuration_for_field(self, field, field_rules, data, columns, guideline, target=None):
        config_field = self.mapping.get(field, None)
        name_index = columns.index("name")
        level_index = columns.index("level")
        condition_index = columns.index("condition")
        self._output_dict[field] = {}

        if not config_field:
            # This field isn't available with this configuration
            return

        tmp_string = ""
        field_rules = self._specific_rules.get(field, field_rules)
        for entry in data:
            condition = ""
            if isinstance(entry, dict):
                name = entry["entry"][name_index]
                level = entry["level"]
                guideline = entry["source"]
                if guideline in entry["entry"]:
                    guideline_pos = entry["entry"].index(guideline)
                    # to get the condition for the guideline I calculate guideline's index and then search it near it
                    step = len(columns)
                    guideline_counter = guideline_pos // step
                    condition = entry["entry"][condition_index + guideline_counter * step]
            else:
                name = entry[name_index]
                level = entry[level_index]
                condition = entry[condition_index]

            if target and target.replace("*", "") not in name:
                continue

            replacements = field_rules.get("replacements", [])
            for replacement in replacements:
                name = name.replace(replacement, replacements[replacement])
            tmp_string += self._get_string_to_add(field_rules, name, level, field)
            if self._output_dict[field].get(name):
                if condition:
                    index = len(self.conditions_to_check)
                    self.conditions_to_check[index] = {
                        "columns": columns,
                        "data": data,
                        "expression": condition,
                        "field": config_field,
                        "guideline": guideline,
                        "level": level
                    }
                self._output_dict[field][name]["guideline"] = guideline

        if tmp_string and tmp_string[-1] == ":":
            tmp_string = tmp_string[:-1]
        tmp_string = tmp_string.strip()
        # this is to prevent adding a field without any value
        if tmp_string:
            # The directive gets added at the beginning of the http directive
            # the breakdown of the below instruction is:
            # loaded_template: dictionary
            # config: list of loaded files (in this case one)
            # parsed: list of dictionaries that represent directives (1 is the http directive)
            # block: list of dictionaries that represent directives inside the directive got before
            # each directive has a directive field for the name and an args (list) one for the params it should have
            # The args value is a list only containing tmp_string because the params are prepared while reading them.
            args = tmp_string
            comment = ""
            if tmp_string.count("#") == 1:
                args, comment = tmp_string.split("#")
            directive_to_add = {"directive": config_field, "args": [args]}
            self._template["config"][0]["parsed"][1]["block"].insert(0, directive_to_add)
            if comment:
                directive_to_add = {"directive": "#", "comment": comment}
                self._template["config"][0]["parsed"][1]["block"].insert(0, directive_to_add)

    def remove_field(self, field):
        to_remove = []
        for directive in self._template["config"][0]["parsed"][1]["block"]:
            if directive.get("directive") == field:
                to_remove.append(directive)
        for directive in to_remove:
            del self._template["config"][0]["parsed"][1]["block"][directive]

    def _load_template(self):
        self._load_conf(Path(self._config_template_path))
        self._template = self.configuration

    def _write_to_file(self):
        if not os.path.isfile(self._config_template_path):
            raise FileNotFoundError("Invalid template file")

        with open(self._config_output, "w") as f:
            f.write(nginx_build(self._template["config"][0]["parsed"], header=True))
