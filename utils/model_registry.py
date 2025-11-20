"""Model registry for Claude Code, Codex, and Gemini backends."""

from typing import Dict

# Gemini models
GEMINI_MODELS: Dict[str, str] = {
    # Gemini 3 Series
    "gemini-3-pro-preview": "gemini-3-pro-preview",

    # Gemini 2.5 Series
    "gemini-2.5-pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",

    # Gemini 2.0 Series
    "gemini-2.0-flash": "gemini-2.0-flash",
    "gemini-2.0-flash-lite": "gemini-2.0-flash-lite",

    # Aliases
    "gemini-3": "gemini-3-pro-preview",
    "gemini-2.5": "gemini-2.5-pro",
    "flash": "gemini-2.5-flash",
    "lite": "gemini-2.5-flash-lite",
    "best": "gemini-3-pro-preview",
}

GEMINI_DESCRIPTIONS = {
    "gemini-3-pro-preview": "Gemini 3 Pro Preview - State of the art",
    "gemini-2.5-pro": "Gemini 2.5 Pro - Strong performance",
    "gemini-2.5-flash": "Gemini 2.5 Flash - Fast and efficient",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite - Lightweight",
    "gemini-2.0-flash": "Gemini 2.0 Flash - Previous generation fast model",
}

GEMINI_CATEGORIES = {
    "Gemini 3 Series": ["gemini-3-pro-preview"],
    "Gemini 2.5 Series": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
    "Gemini 2.0 Series": ["gemini-2.0-flash", "gemini-2.0-flash-lite"],
    "Quick Aliases": ["best", "flash", "lite"],
}

GEMINI_EXPECTED = {
    "gemini-3-pro-preview": {"min": 30, "max": 40, "typical": 35},
    "gemini-2.5-pro": {"min": 25, "max": 35, "typical": 30},
    "gemini-2.5-flash": {"min": 20, "max": 30, "typical": 25},
}

# Claude models
CLAUDE_MODELS: Dict[str, str] = {
    # Opus models (most capable)
    "claude-opus-4.1": "claude-opus-4-1-20250805",
    "claude-opus-4.0": "claude-opus-4-20250514",

    # Sonnet models
    "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
    "claude-sonnet-4.0": "claude-sonnet-4-20250514",
    "claude-3.7-sonnet": "claude-3-7-sonnet-20250219",

    # Haiku models
    "claude-haiku-4.5": "claude-haiku-4-5-20251001",
    "claude-3.5-haiku": "claude-3-5-haiku-20241022",

    # Aliases
    "opus-4.1": "claude-opus-4.1",
    "opus-4.0": "claude-opus-4.0",
    "sonnet-4.5": "claude-sonnet-4.5",
    "sonnet-4": "claude-sonnet-4.0",
    "sonnet-3.7": "claude-3.7-sonnet",
    "best": "claude-sonnet-4.5", # Or Opus 4.1 depending on preference, user said "newest Opus or Sonnet 4.5"
    "balanced": "claude-sonnet-4.0",
    "fast": "claude-haiku-4.5",
    "latest": "claude-sonnet-4.5",
}

CLAUDE_DESCRIPTIONS = {
    "claude-opus-4.1": "Opus 4.1 - Latest and most capable",
    "claude-opus-4.0": "Opus 4.0 - Very strong performance",
    "claude-sonnet-4.5": "Sonnet 4.5 - State of the art balanced model",
    "claude-sonnet-4.0": "Sonnet 4.0 - Strong balanced model",
    "claude-haiku-4.5": "Haiku 4.5 - Fast and smart",
    "claude-3.7-sonnet": "Sonnet 3.7 - Reliable previous gen",
}

CLAUDE_CATEGORIES = {
    "Opus Models (Most Capable)": ["claude-opus-4.1", "claude-opus-4.0"],
    "Sonnet Models (Balanced)": ["claude-sonnet-4.5", "claude-sonnet-4.0", "claude-3.7-sonnet"],
    "Haiku Models (Fast)": ["claude-haiku-4.5", "claude-3.5-haiku"],
    "Quick Aliases": ["best", "balanced", "fast"],
}

CLAUDE_EXPECTED = {
    "claude-opus-4.1": {"min": 35, "max": 45, "typical": 40},
    "claude-sonnet-4.5": {"min": 35, "max": 45, "typical": 40},
    "claude-sonnet-4.0": {"min": 25, "max": 35, "typical": 30},
}

# Codex/OpenAI models
CODEX_MODELS: Dict[str, str] = {
    # GPT-5 Series
    "gpt-5": "gpt-5-2025-08-07",
    "gpt-5-mini": "gpt-5-mini-2025-08-07",
    "gpt-5-pro": "gpt-5-pro",

    # GPT-5 Codex
    "codex-gpt-5": "gpt-5-codex",
    "codex-mini": "codex-mini-latest",

    # GPT-4.1 Series
    "gpt-4.1": "gpt-4.1-2025-04-14",

    # O-Series
    "o3": "o3-2025-04-16",
    "o3-mini": "o3-mini",

    # Aliases
    "codex-latest": "gpt-5-codex",
    "codex": "codex-latest",
    "best": "gpt-5-pro",
    "fast": "gpt-5-mini",
}

CODEX_DESCRIPTIONS = {
    "gpt-5": "GPT-5 - Major flagship release",
    "gpt-5-pro": "GPT-5 Pro - High compute model",
    "codex-gpt-5": "GPT-5 Codex - Specialized for code",
    "o3": "O3 - Reasoning model",
    "gpt-4.1": "GPT-4.1 - Refined GPT-4 architecture",
}

CODEX_CATEGORIES = {
    "GPT-5 Series": ["gpt-5", "gpt-5-pro", "gpt-5-mini"],
    "Codex Models": ["codex-gpt-5", "codex-mini"],
    "O-Series (Reasoning)": ["o3", "o3-mini"],
    "Legacy": ["gpt-4.1"],
    "Quick Aliases": ["best", "codex-latest"],
}

CODEX_EXPECTED = {
    "gpt-5-pro": {"min": 35, "max": 45, "typical": 40},
    "gpt-5": {"min": 30, "max": 40, "typical": 35},
    "codex-gpt-5": {"min": 32, "max": 42, "typical": 38},
}


def _resolve(models: Dict[str, str], alias: str, seen: set = None) -> str:
    if seen is None:
        seen = set()

    if alias in seen:
        # Circular dependency or infinite loop
        return alias

    if alias in models:
        resolved = models[alias]

        # If resolved value maps to itself, return it
        if resolved == alias:
            return resolved

        # If resolved value is in models, recurse
        if resolved in models:
            seen.add(alias)
            return _resolve(models, resolved, seen)

        return resolved
    return alias


def get_model_name(alias: str, backend: str = "claude") -> str:
    """Return the full model name for the given alias and backend."""
    if not alias:
        return None
    backend = backend.lower()
    if backend == "codex":
        models = CODEX_MODELS
    elif backend == "gemini":
        models = GEMINI_MODELS
    else:
        models = CLAUDE_MODELS

    if alias in models:
        return _resolve(models, alias)
    return alias


def list_models(backend: str = "claude") -> str:
    """Generate a formatted list of available models for the backend."""
    backend = backend.lower()
    if backend == "codex":
        categories = CODEX_CATEGORIES
        descriptions = CODEX_DESCRIPTIONS
        title = "Available Codex/OpenAI Models"
    elif backend == "gemini":
        categories = GEMINI_CATEGORIES
        descriptions = GEMINI_DESCRIPTIONS
        title = "Available Gemini Models"
    else:
        categories = CLAUDE_CATEGORIES
        descriptions = CLAUDE_DESCRIPTIONS
        title = "Available Claude Models"

    lines = [title + ":", "=" * 50]
    for category, models in categories.items():
        lines.append(f"\n{category}:")
        for model in models:
            desc = descriptions.get(model, "")
            full_name = get_model_name(model, backend)
            if desc:
                lines.append(f"  {model:<22} - {desc}")
            else:
                lines.append(f"  {model:<22} -> {full_name}")
    return "\n".join(lines)


def validate_model(alias: str) -> bool:
    """Validate that a model alias is non-empty."""
    return bool(alias)


def get_expected_performance(model: str, backend: str = "claude") -> dict:
    """Get expected SWE-bench performance for a model."""
    backend = backend.lower()
    if backend == "codex":
        models = CODEX_MODELS
        expectations = CODEX_EXPECTED
    elif backend == "gemini":
        models = GEMINI_MODELS
        expectations = GEMINI_EXPECTED
    else:
        models = CLAUDE_MODELS
        expectations = CLAUDE_EXPECTED

    full_model = get_model_name(model, backend)

    # Check if alias is directly in expectations
    if model in expectations:
        return expectations[model]

    # Check by full name mapping
    for alias, full in models.items():
        if full == full_model or alias == model:
            if alias in expectations:
                return expectations[alias]

    return {"min": 10, "max": 30, "typical": 20}
