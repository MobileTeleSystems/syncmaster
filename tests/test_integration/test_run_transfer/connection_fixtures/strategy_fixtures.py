import pytest


@pytest.fixture
def full_strategy():
    return {
        "type": "full",
    }


@pytest.fixture
def incremental_strategy_by_file_modified_since():
    return {
        "type": "incremental",
        "increment_by": "file_modified_since",
    }


@pytest.fixture
def incremental_strategy_by_file_name():
    return {
        "type": "incremental",
        "increment_by": "file_name",
    }


@pytest.fixture
def incremental_strategy_by_number_column():
    return {
        "type": "incremental",
        "increment_by": "NUMBER",
    }
