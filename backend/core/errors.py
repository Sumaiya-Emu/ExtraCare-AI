"""Domain errors that should fail closed rather than silently becoming a 'Safe' result."""


class AnalysisUnavailableError(RuntimeError):
    """Raised when the system cannot produce a trustworthy assessment."""


class AnalysisParsingError(AnalysisUnavailableError):
    """Raised when an LLM response cannot be validated as the required JSON schema."""
