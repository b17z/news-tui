"""Error types and Result pattern for news-tui.

This module implements Rust-style Result types for explicit error handling.
Business logic errors are returned as values (Err), not thrown as exceptions.

Use Result types for:
- Business logic errors (article not found, invalid input, etc.)
- Expected failure cases that callers should handle

Use exceptions for:
- Truly exceptional failures (out of memory, system errors)
- Programmer errors (assertions, invariant violations)
"""

from dataclasses import dataclass
from typing import Generic, Literal, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Success case of a Result.

    Attributes:
        value: The successful return value.
    """

    value: T

    @property
    def is_ok(self) -> Literal[True]:
        """Always True for Ok."""
        return True

    @property
    def is_err(self) -> Literal[False]:
        """Always False for Ok."""
        return False


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """Error case of a Result.

    Attributes:
        error: The error value describing what went wrong.
    """

    error: E

    @property
    def is_ok(self) -> Literal[False]:
        """Always False for Err."""
        return False

    @property
    def is_err(self) -> Literal[True]:
        """Always True for Err."""
        return True


# Result is either Ok[T] or Err[E]
Result = Union[Ok[T], Err[E]]


# Convenience constructors
def ok(value: T) -> Ok[T]:
    """Create a successful Result.

    Args:
        value: The success value.

    Returns:
        An Ok containing the value.
    """
    return Ok(value)


def err(error: E) -> Err[E]:
    """Create an error Result.

    Args:
        error: The error value.

    Returns:
        An Err containing the error.
    """
    return Err(error)


# Typed error types for the application
# Using discriminated unions for type-safe error handling


@dataclass(frozen=True, slots=True)
class FetchError:
    """Error fetching content from a source.

    Attributes:
        source_id: Which source failed.
        message: Human-readable error description.
        status_code: HTTP status code if applicable.
    """

    source_id: str
    message: str
    status_code: int | None = None


@dataclass(frozen=True, slots=True)
class ParseError:
    """Error parsing content (RSS, HTML, etc.).

    Attributes:
        source: What was being parsed.
        message: What went wrong.
        line: Line number if applicable.
    """

    source: str
    message: str
    line: int | None = None


@dataclass(frozen=True, slots=True)
class AnalysisError:
    """Error during content analysis.

    Attributes:
        article_id: Which article failed analysis.
        stage: Which analysis stage failed (sentiment, topics, etc.).
        message: What went wrong.
    """

    article_id: str
    stage: str
    message: str


@dataclass(frozen=True, slots=True)
class StorageError:
    """Error with database operations.

    Attributes:
        operation: What operation failed (read, write, etc.).
        message: What went wrong.
    """

    operation: str
    message: str


@dataclass(frozen=True, slots=True)
class ConfigError:
    """Error with configuration.

    Attributes:
        field: Which config field has an issue.
        message: What's wrong with it.
    """

    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Error validating user input.

    Attributes:
        field: Which field failed validation.
        message: What's wrong.
        value: The invalid value (sanitized for logging).
    """

    field: str
    message: str
    value: str | None = None


# Union of all error types
NewsTuiError = Union[
    FetchError,
    ParseError,
    AnalysisError,
    StorageError,
    ConfigError,
    ValidationError,
]


# Type aliases for common Result types
FetchResult = Result[T, FetchError]
ParseResult = Result[T, ParseError]
AnalysisResult = Result[T, AnalysisError]
StorageResult = Result[T, StorageError]
