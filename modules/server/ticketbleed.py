from modules.server.testssl_base import Testssl_base
import logging


class Ticketbleed(Testssl_base):
    """
    Analysis of the ticketbleed testssl results
    """

    # to override
    def _set_arguments(self):
        """
        Sets the arguments for the testssl command
        """
        self._arguments = ["-T"]

    # to override
    def _worker(self, results):
        """
        The worker method, which runs the testssl command

        :param results: dict
        :return: dict
        :rtype: dict
        """
        return self._obtain_results(results, ["ticketbleed"])