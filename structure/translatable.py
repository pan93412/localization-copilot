from dataclasses import dataclass, field


@dataclass
class Translation:
    source: str
    translation: str
    fuzzy: bool
    context: str | None = None
    confidence: float | None = None  # for LLM, 0.0 - 1.0


@dataclass
class Translatable:
    source: str
    context: str | None = None

    references: list[Translation] = field(default_factory=list)
