from modules.compliance.compliance_base import Generator


class GenerateMany(Generator):
    def _worker(self, sheets_to_check):
        columns = ["name", "level", "condition", "guidelineName"]
        name_index = columns.index("name")
        level_index = columns.index("level")
        # fill the entries field with the data from the sheets
        self._retrieve_entries(sheets_to_check, columns)