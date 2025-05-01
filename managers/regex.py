"""
Regex suite
"""
from re import error as RegexException

from ..settings import RULE_SET
from ..models.filter import Filter

class RegexOperations:
    """
    Class designed to handle Kytos-specific regex operations.
    """

    def __init__(self):
        self._rules: dict[str, Filter] = {}
        self._rules = self._setup_rules()

    @property
    def rules(self) -> dict[str, Filter]:
        """ Getter """
        return self._rules

    def _delete_filter(self, rule: str) -> Filter:
        """
        Remove a filter from the rules dictionary and return the Filter

        Raises KeyError if the pattern does not exist

        Raises ValueError if the pattern is trying to remove an immutable Filter
        """
        try:
            if rule not in self.rules:
                raise KeyError("Pattern does not exist.")
            if not self.rules[rule].is_mutable():
                raise ValueError("Pattern cannot be removed.")
            return self.rules.pop(rule)
        except (KeyError, ValueError) as exc:
            raise exc

    def _create_filter(self, rule: str, mutable: bool, description: str) -> Filter:
        """
        Create a filter to add to the rules dictionary.

        If the created filter has an invalid regex pattern, return the exception
        """
        try:
            if rule in self.rules:
                raise ValueError("Cannot have duplicate patterns.")
            return Filter(rule, mutable, description)
        except (RegexException, ValueError) as exc:
            raise exc

    def _setup_rules(self, rule_set: list[dict[str, str]] = RULE_SET) -> dict[str, Filter]:
        """
        Setup the rules, compiling each to their regex objects

        Raises re.error (RegexException) on compilation error

        Raises ValueError if the provided pattern is already present
        """
        rules: dict[str, Filter] = {}

        for rule in rule_set:
            rules[rule["pattern"]] = self._create_filter(
                rule["pattern"], False, rule["description"]
            )

        return rules

    def is_accepted_event(self, event: str) -> bool:
        """
        Check if a given event is accepted based on a custom ruleset. Uses regex to check for
        exact matches and wildcards.

        Follows the principle of least privilege, so if it's not explicitly accepted, it is
        rejected.
        """
        for rule in self._rules.values():
            if rule.search(event):
                return True

        return False

    def create_filter(self, pattern: str, description: str) -> None:
        """
        Check if a given pattern is valid, then add it to _rules

        Raises re.error (RegexException) on compilation error

        Raises ValueError if the provided pattern is already present
        """
        try:
            self.rules[pattern] = self._create_filter(pattern, True, description)
        except (RegexException, ValueError) as exc:
            raise exc

    def list_filters(self) -> list[dict[str, str]]:
        """
        List the summary of each filter

        Returns a list of dictionaries that look like:
        {"pattern": str, "mutable": str, "description": str}
        """
        return [x.summarize() for x in self.rules.values()]

    def delete_filter(self, pattern: str) -> None:
        """
        Check if a given pattern is in rules and delete it.

        Raises KeyError if the given pattern is not present

        Raises ValueError if the given pattern immutable
        """
        try:
            self._delete_filter(pattern)
        except (KeyError, ValueError) as exc:
            raise exc
