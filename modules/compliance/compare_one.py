from modules.compliance.compliance_base import Compliance


class CompareOne(Compliance):
    def _worker(self, sheets_to_check):
        """
        :param sheets_to_check: dict of sheets that should be checked in the form: sheet:{protocol, version_of_protocol}
        :type sheets_to_check: dict

        :return: processed results
        :rtype: dict
        """
        if not self._user_configuration:
            raise ValueError("No configuration provided")
        for sheet in sheets_to_check:
            columns_orig = ["name", "level", "condition", "guidelineName"]
            # If the sheet isn't in the dictionary then I can use the default value
            columns = self.sheet_columns.get(sheet, {"columns": columns_orig})["columns"]
            name_index = columns.index("name")
            name_columns = self.sheet_columns.get(sheet, {}).get("name_columns", [name_index])
            level_index = columns.index("level")
            condition_index = columns.index("condition")
            guideline = list(sheets_to_check[sheet].keys())[0]
            if not self._output_dict.get(sheet):
                self._output_dict[sheet] = {}
            table_name = self._database_instance.get_table_name(sheet, guideline, sheets_to_check[sheet][guideline])
            self._database_instance.input([table_name])
            data = self._database_instance.output(columns)
            config_field = sheet
            for entry in data:
                if config_field:
                    name = entry[name_index]
                    level = entry[level_index]
                    condition = entry[condition_index]
                    enabled = self._condition_parser.is_enabled(self._user_configuration, config_field, name,
                                                                entry, condition=condition)
                    valid_condition = True
                    if condition:
                        valid_condition = self._condition_parser.run(condition, enabled)
                        if self._condition_parser.entry_updates.get("levels"):
                            levels = self._condition_parser.entry_updates.get("levels")
                            levels.insert(0, level)
                            to_use = self.level_to_use(levels)
                            level = levels[to_use]
                    has_alternative = self._condition_parser.entry_updates.get("has_alternative")
                    additional_notes = self._condition_parser.entry_updates.get("notes", "")
                    if has_alternative or additional_notes:
                        # This is to trigger the output condition. This works because I'm assuming that "THIS" is only
                        # used in a positive (recommended, must) context.
                        valid_condition = True
                    # if it has multiple name_columns they get only shown in the output
                    name = "_".join([str(entry[i]) for i in name_columns])
                    self.update_result(sheet, name, level, enabled, entry[-1], valid_condition)
                    note = ""
                    if has_alternative and not enabled and isinstance(condition, str) and condition.count(" ") > 1:
                        parts = entry[condition_index].split(" ")
                        # Tokens[1] is the logical operator
                        note = f"\nNOTE: {name} {parts[1].upper()} {' '.join(parts[2:])} is needed"
                    if additional_notes:
                        note += "\nNOTE:"
                        note += "\n".join(additional_notes)
                    if self._output_dict[sheet].get(name) is not None:
                        self._output_dict[sheet][name] += note