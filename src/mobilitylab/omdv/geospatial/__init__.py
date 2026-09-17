"""City-universe standardization and transparent name/country matching."""

from .city_matching import match_feeds_to_cities_by_name, normalize_name, summarize_matches
from .external_city_universe import (
    read_external_city_universe,
    standardize_external_city_universe,
)

__all__ = [
    "match_feeds_to_cities_by_name",
    "normalize_name",
    "read_external_city_universe",
    "standardize_external_city_universe",
    "summarize_matches",
]

