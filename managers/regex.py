"""
Regex suite
"""
from re import error as RegexException, Pattern, compile
from uuid import uuid4

from ..settings import RULE_SET
from ..models.filter import Filter

class RegexOperations:
    """
    Class designed to handle Kytos-specific regex operations.
    """

    def __init__(self):
        """ Must call startup """
        self._rules: dict[str, Filter] = {}

    @property
    def rules(self) -> dict[str, Filter]:
        """ Getter """
        return self._rules

    @rules.setter
    def rules(self, new_rules: dict[str, Filter]) -> None:
        """ Setter """
        if not isinstance(new_rules, dict):
            raise ValueError("Rules must be of type dict[str, Filter].")
        for filter_id, filter_obj in new_rules.items():
            if not isinstance(filter_id, str):
                raise ValueError("Rule key must be of type str")
            if not isinstance(filter_obj, Filter):
                raise ValueError("Rule values must be of type Filter")

        self._rules = new_rules

    async def start_up(self) -> None:
        """
        Initialize the RegexOperations instance
        """
        self.rules = await self._setup_rules()

    async def _delete_filter(self, filter_id: str) -> Filter:
        """
        Remove a filter from the rules dictionary and return the Filter

        Raises KeyError if the pattern does not exist

        Raises ValueError if the pattern is trying to remove an immutable Filter
        """
        try:
            if filter_id not in self.rules:
                raise KeyError("Pattern does not exist.")
            if not self.rules[filter_id].is_mutable():
                raise ValueError("Pattern cannot be removed.")
            return self.rules.pop(filter_id)
        except (KeyError, ValueError) as exc:
            raise exc

    async def _create_filter(self, rule: str, mutable: bool, description: str) -> Filter:
        """
        Create a filter to add to the rules dictionary.

        If the created filter has an invalid regex pattern, return the exception
        """
        try:
            compiled_rule: Pattern = compile(rule)
            for filter_obj in self.rules.values():
                if filter_obj.pattern.pattern == compiled_rule.pattern:
                    raise ValueError("Cannot have duplicate patterns.")
            return Filter(rule, mutable, description)
        except (RegexException, ValueError) as exc:
            raise exc

    async def _setup_rules(self, rule_set: list[dict[str, str]] = RULE_SET) -> dict[str, Filter]:
        """
        Setup the rules, compiling each to their regex objects

        Raises re.error (RegexException) on compilation error

        Raises ValueError if the provided pattern is already present
        """
        rules: dict[str, Filter] = {}

        for rule in rule_set:
            rules[str(uuid4().hex)] = await self._create_filter(
                rule["pattern"], False, rule["description"]
            )

        return rules

    async def is_accepted_event(self, event: str) -> bool:
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

    async def create_filter(self, pattern: str, description: str) -> dict[str, dict[str, str]]:
        """
        Check if a given pattern is valid, then add it to _rules. Returns the created filter.

        Raises re.error (RegexException) on compilation error

        Raises ValueError if the provided pattern is already present
        """
        try:
            filter_id: str = str(uuid4().hex)
            filter_obj: Filter = await self._create_filter(pattern, True, description)

            self.rules[filter_id] = filter_obj

            return {filter_id: filter_obj.as_dict()}
        except (RegexException, ValueError) as exc:
            raise exc

    async def list_filters(self) -> list[dict[str, dict[str, str]]]:
        """
        List the summary of each filter

        Returns a list of dictionaries that look like:
        [str: {"pattern": str, "mutable": str, "description": str}, ...]
        """
        return [
            {filter_id: filter_obj.as_dict()} for filter_id, filter_obj in self.rules.items()
        ]

    async def delete_filter(self, filter_id: str) -> dict[str, str]:
        """
        Check if a given pattern is in rules and delete it. Returns deleted pattern as a dict.

        Raises KeyError if the given pattern is not present

        Raises ValueError if the given pattern immutable
        """
        try:
            return (await self._delete_filter(filter_id)).as_dict()
        except (KeyError, ValueError) as exc:
            raise exc
