"""
Claude Model Registry for September 2025
Defines available models and their aliases
"""

# September 2025 Claude Models
MODELS = {
    # Opus models (most capable, highest accuracy)
    'opus-4.1': 'claude-opus-4-1-20250805',      # Latest Opus 4.1
    'opus-4.0': 'claude-opus-4-0-20250620',      # Opus 4.0  
    'opus-4': 'opus-4.0',                        # Alias for 4.0
    'opus': 'opus-4.1',                          # Default to latest
    
    # Sonnet models (balanced performance)
    'sonnet-4': 'claude-sonnet-4-20250815',      # Sonnet 4
    'sonnet-3.7': 'claude-3-7-sonnet-20250901',  # Latest 3.x series
    'sonnet-3.6': 'claude-3-6-sonnet-20250715',  # Sonnet 3.6
    'sonnet-3.5': 'claude-3-5-sonnet-20241022',  # Sonnet 3.5
    'sonnet': 'sonnet-3.7',                      # Default to 3.7
    
    # Quick aliases for common use cases
    'best': 'opus-4.1',                          # Best performance
    'balanced': 'sonnet-3.7',                    # Good balance
    'fast': 'sonnet-3.5',                        # Fastest/cheapest
    'latest': 'opus-4.1',                        # Latest model
    
    # Legacy/compatibility aliases
    'claude-code': 'sonnet-3.7',                 # Default Claude Code model
}

# Model descriptions for help text
MODEL_DESCRIPTIONS = {
    'opus-4.1': 'Opus 4.1 - Latest and most capable (30-40% SWE-bench)',
    'opus-4.0': 'Opus 4.0 - Very strong performance (25-35% SWE-bench)',
    'sonnet-4': 'Sonnet 4 - New generation balanced model (20-30% SWE-bench)',
    'sonnet-3.7': 'Sonnet 3.7 - Latest 3.x series (18-25% SWE-bench)',
    'sonnet-3.6': 'Sonnet 3.6 - Solid performance (15-22% SWE-bench)',
    'sonnet-3.5': 'Sonnet 3.5 - Fast and efficient (12-20% SWE-bench)',
}

# Model categories for grouping
MODEL_CATEGORIES = {
    'Opus Models (Most Capable)': ['opus-4.1', 'opus-4.0'],
    'Sonnet Models (Balanced)': ['sonnet-4', 'sonnet-3.7', 'sonnet-3.6', 'sonnet-3.5'],
    'Quick Aliases': ['best', 'balanced', 'fast'],
}

def get_model_name(alias: str) -> str:
    """
    Get the full model name from an alias.
    Accepts both registered aliases and any custom model name.
    
    Args:
        alias: Model alias, full name, or any custom model identifier
        
    Returns:
        Model name to pass to Claude CLI
    """
    if not alias:
        return None
    
    # If it's already a full model name (starts with 'claude-'), return as-is
    if alias.startswith('claude-'):
        return alias
    
    # Look up in registry
    if alias in MODELS:
        # Recursively resolve aliases
        resolved = MODELS[alias]
        if resolved in MODELS:
            return get_model_name(resolved)
        return resolved
    
    # If not found in registry, return as-is
    # This allows any model name that Claude CLI accepts, including:
    # - Future models not yet in our registry
    # - Custom model identifiers
    # - Any valid /model command argument
    return alias

def list_models() -> str:
    """
    Generate a formatted list of available models.
    
    Returns:
        Formatted string listing all models
    """
    lines = []
    lines.append("Available Claude Models (September 2025):")
    lines.append("="*50)
    
    for category, models in MODEL_CATEGORIES.items():
        lines.append(f"\n{category}:")
        for model in models:
            desc = MODEL_DESCRIPTIONS.get(model, "")
            full_name = get_model_name(model)
            if desc:
                lines.append(f"  {model:<12} - {desc}")
            else:
                lines.append(f"  {model:<12} -> {full_name}")
    
    lines.append("\nUsage:")
    lines.append("  python swe_bench.py run --model opus-4.1 --quick")
    lines.append("  python swe_bench.py run --model sonnet-3.6 --limit 20")
    lines.append("\nNote: You can also use any model name accepted by Claude's /model command,")
    lines.append("      even if not listed above (e.g., experimental or future models).")
    
    return "\n".join(lines)

def validate_model(alias: str) -> bool:
    """
    Check if a model alias is valid.
    Always returns True since we accept any model name that Claude CLI might accept.
    
    Args:
        alias: Model alias to check
        
    Returns:
        True if alias is provided, False if None/empty
    """
    # We accept any non-empty model name, letting Claude CLI validate it
    return bool(alias)

# Performance expectations for reference
EXPECTED_PERFORMANCE = {
    'opus-4.1': {'min': 30, 'max': 40, 'typical': 35},
    'opus-4.0': {'min': 25, 'max': 35, 'typical': 30},
    'sonnet-4': {'min': 20, 'max': 30, 'typical': 25},
    'sonnet-3.7': {'min': 18, 'max': 25, 'typical': 21},
    'sonnet-3.6': {'min': 15, 'max': 22, 'typical': 18},
    'sonnet-3.5': {'min': 12, 'max': 20, 'typical': 15},
}

def get_expected_performance(model: str) -> dict:
    """Get expected SWE-bench performance for a model."""
    # Resolve alias first
    full_model = get_model_name(model)
    
    # Find which model this maps to
    for alias, full_name in MODELS.items():
        if full_name == full_model or alias == model:
            if alias in EXPECTED_PERFORMANCE:
                return EXPECTED_PERFORMANCE[alias]
    
    return {'min': 10, 'max': 30, 'typical': 20}  # Default estimate