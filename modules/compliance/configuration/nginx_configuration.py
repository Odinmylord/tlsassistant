import os
from pathlib import Path

from crossplane import parse as nginx_parse
from crossplane import build as nginx_build

from modules.compliance.configuration.configuration_base import ConfigurationMaker


class NginxConfiguration(ConfigurationMaker):
    def __init__(self, file: Path = None):
        super().__init__("nginx")
        if file:
            self._load_conf(file)

    # Stole this function from Configuration for testing purposes
    def _load_conf(self, file: Path):
        """
        Internal method to load the nginx configuration file.

        :param file: path to the configuration file
        :type file: str
        """
        self.configuration = nginx_parse(str(file.absolute()))
        if self.configuration.get("errors", []):
            raise ValueError("Invalid nginx config file")

    def add_configuration_for_field(self, field, field_rules, data, name_index, level_index):
        config_field = self.mapping.get(field, None)
        self._output_dict[field] = {}
        if not config_field:
            # This field isn't available with this configuration
            return

        tmp_string = ""
        field_rules = self._specific_rules.get(field, field_rules)
        # the idea is that it is possible to define a custom value to insert like on/off or name to use the name
        # defined in the config file
        allow_string = field_rules.get("enable", "name")
        deny_string = field_rules.get("disable", "-name")
        separator = field_rules.get("separator", " ")
        # This parameter is needed to avoid having separators even if nothing gets added to deny (like ciphersuites)
        added_negatives = field_rules.get("added_negatives", False)
        replacements = field_rules.get("replacements", [])
        for entry in data:
            added = True
            name = entry[name_index]
            for replacement in replacements:
                name = name.replace(replacement, replacements[replacement])
            if entry[level_index] in ["must", "recommended"]:
                tmp_string += allow_string.replace("name", name)
                self._output_dict[field][name] = True
            elif entry[level_index] in ["must not", "not recommended"]:
                tmp_string += deny_string.replace("name", name)
                added = added_negatives
                self._output_dict[field][name] = False
            else:
                added = False
                self._output_dict[field][name] = False

            if added:
                tmp_string += separator

        if tmp_string and tmp_string[-1] == ":":
            tmp_string = tmp_string[:-1]
        tmp_string = tmp_string.strip()
        if tmp_string:  # this is to prevent adding a field without any value
            print(self._template)
            # The directive gets added at the beginning the http directive
            self._template["config"][0]["parsed"][1]["block"].insert(0, {"directive": field, "args": [tmp_string]})

    def _load_template(self):
        self._load_conf(Path(self._config_template_path))
        self._template = self.configuration

    def _write_to_file(self):
        if not os.path.isfile(self._config_template_path):
            raise FileNotFoundError("Invalid template file")

        with open(self._config_output, "w") as f:
            f.write(nginx_build(self._template["config"][0]["parsed"], header=True))
