"""
A class for filter specific data, such as 
"""
import re
from re import Pattern, error

class Filter:
    """
    Filter objects to be used in RegexOperations.

    They take care of comparisons, checking for mutability, and descriptions.
    """
    def __init__(self, pattern: str, mutable: bool, description: str):
        self._pattern = self._validated_and_compile(pattern)
        self._mutable = mutable
        self._description = description

    @property
    def description(self) -> str:
        """ Getter """
        return self._description

    @property
    def pattern(self) -> Pattern:
        """ Getter """
        return self._pattern

    @property
    def mutable(self) -> bool:
        """ Getter """
        return self._mutable

    def _validated_and_compile(self, pattern: str) -> Pattern:
        """
        Private method

        Validate a string is correct and compile
        """
        try:
            return re.compile(pattern)
        except error as err:
            raise err

    def search(self, event: str) -> bool:
        """
        Check if an event is accepted by this filter

        Returns a bool
        """
        return self.pattern.match(event)

    def is_mutable(self) -> bool:
        """
        Check if the filter is mutable (can be modified)

        Returns a bool
        """
        return self.mutable

    def as_dict(self) -> dict[str, str]:
        """
        Summarize the given filter, returning it as a dictionary.
        
        Returns a dictionary that looks like:
        {"pattern": str, "mutable": bool, "description": str}
        """
        return {
            "pattern": self.pattern.pattern,
            "mutable": self.mutable,
            "description": self.description
        }
