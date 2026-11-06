"""
Test Suite: Hazard Decision Tree Validation
Verifies all 3 hazard trees (Flood, Earthquake, Landslide) adhere to schema,
multilingual requirements, source mappings, reachability, and dead-end freedom.
"""

import os
import pytest
from engine.validator import validate_all_trees, validate_tree_file, load_sources

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TREES_DIR = os.path.join(BASE_DIR, "data", "trees")
SOURCES_PATH = os.path.join(BASE_DIR, "data", "sources.json")


def test_sources_file_exists_and_valid():
    """Verify sources.json exists and contains required authoritative disaster sources."""
    assert os.path.exists(SOURCES_PATH), "sources.json must exist"
    sources = load_sources(SOURCES_PATH)
    assert "ndma_flood" in sources
    assert "ndma_quake" in sources
    assert "ndma_landslide" in sources
    assert "ksdma_monsoon" in sources
    assert "mha_erss_112" in sources


def test_all_trees_structural_validity():
    """Validates that all trees in data/trees pass comprehensive graph and schema validation."""
    results = validate_all_trees(TREES_DIR, SOURCES_PATH)
    assert len(results) >= 3, "Must have at least 3 hazard trees (Flood, Earthquake, Landslide)"

    for hazard_id, errors in results.items():
        assert len(errors) == 0, f"Tree '{hazard_id}' had validation errors:\n" + "\n".join(errors)


@pytest.mark.parametrize("hazard_id", ["flood", "earthquake", "landslide"])
def test_individual_hazard_tree(hazard_id):
    """Deep check on each hazard tree individually."""
    tree_file = os.path.join(TREES_DIR, f"{hazard_id}.json")
    assert os.path.exists(tree_file), f"{hazard_id}.json must exist"
    errors = validate_tree_file(tree_file, SOURCES_PATH)
    assert errors == [], f"Validation failed for {hazard_id}: {errors}"

