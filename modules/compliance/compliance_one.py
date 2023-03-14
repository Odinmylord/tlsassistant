from modules.compliance.compliance_base import Compliance


class ComplianceOne(Compliance):
    def _worker(self, sheets_to_check):
        """
        :param sheets_to_check: dict of sheets that should be checked in the form: sheet:{protocol, version_of_protocol}
        :type sheets_to_check: dict

        :return: processed results
        :rtype: dict
        """
        if not self._user_configuration:
            raise ValueError("No configuration provided")
        columns = ["name", "evaluation", "condition"]
        name_index = columns.index("name")
        evaluation_index = columns.index("evaluation")
        for sheet in sheets_to_check:
            # If the sheet isn't in the dictionary then I can use the default value
            columns = self.sheet_columns.get(sheet, columns)
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
                    evaluation = entry[evaluation_index]
                    enabled = self.is_enabled(config_field, name, entry)
                    self.update_result(sheet, name, evaluation, enabled)