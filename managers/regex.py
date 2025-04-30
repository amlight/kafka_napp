"""
Regex suite
"""

import re

from re import Pattern

from ..settings import RULE_SET

class RegexOperations:
    """
    Class designed to handle Kytos-specific regex operations.
    
    This is a necessary manager as, for example, "kytos/mef_eline.*" is not a valid regex
    operations out of the box. It would allow for matches like "kytos/mef_eline1234", which is not
    correct. 
    """

    def __init__(self):
        self._rules: list[Pattern] = self._setup_rules()

    def _wildcard_to_regex(self, pattern: str) -> str:
        """
        Convert wild card patterns in common regex to Python specific format
        """
        escaped: str = re.escape(pattern)
        regex = escaped.replace("\\*", ".*")
        return regex

    def _setup_rules(self, rule_set: list[dict[str, str]] = RULE_SET) -> list[Pattern]:
        """
        Setup the rules, compiling each to their regex objects
        """
        rules: list[Pattern] = []

        for rule in rule_set:

            if rule["type"] == "wildcard":
                rules.append(re.compile(self._wildcard_to_regex(rule["pattern"])))
            elif rule["type"] == "match":
                rules.append(re.compile(rule["pattern"]))

        return rules


    def is_accepted_event(self, event: str) -> bool:
        """
        Check if a given event is accepted based on a custom ruleset. Uses regex to check for
        exact matches and wildcards.

        Follows the principle of least privilege, so if it's not explicitly accepted, it is
        rejected.
        """
        for rule in self._rules:
            if rule.match(event):
                return True

        return False
