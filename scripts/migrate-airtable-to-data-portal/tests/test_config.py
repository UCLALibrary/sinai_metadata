from migrate import config
import pytest
import argparse
import os

# Set up a valid path
@pytest.fixture
def config_folder_path(scope="module"):
    cwd = os.getcwd()
    return cwd + "/tests/files/"

# TODO: add a fixture for invalid file path to test error raising and other fail cases

# Default args
@pytest.fixture
def args(config_folder_path, scope="module"):
    return argparse.Namespace(mode="csv", config=config_folder_path)

# Expected ms obj table config
@pytest.fixture
def manuscript_object_table_config(scope="module"):
    return {
        "manuscript_objects": {
            "csv": None,
            "airtable": None,
            "fields": "fields/ms_objs.yml"
        }
    }

@pytest.fixture
def manuscript_object_field_config(scope="module"):
    return {
        "ark": {
            "name": "Item ARK",
            "csv": "text",
            "airtable": "text"
        }
    }

class TestSetConfigs:
    def test_set_mode(self):
        expected = "csv"
        config.set_mode(expected)
        assert config.MODE == expected

    def test_set_table_configs_airtable_base(self, args):
        expected = "appiXmKhPFEVmVQrD"
        config.set_table_configs(dir=args.config, file="table_configs.yml")
        assert config.AIRTABLE_BASE == expected

    def test_set_table_configs_tables(self, args, manuscript_object_table_config):
        config.set_table_configs(dir=args.config, file="table_configs.yml")
        assert config.TABLES == manuscript_object_table_config

    def test_set_field_configs(self, args, manuscript_object_table_config, manuscript_object_field_config):
        config.TABLES = manuscript_object_table_config
        config.set_field_configs(dir=args.config)
        assert config.TABLES["manuscript_objects"]["fields"] == manuscript_object_field_config

    # TODO: this should be repeated for all of the above fields to test that the parent one works correctly
    def test_set_configs_csv(self, args):
        config.set_configs(args)
        assert config.MODE == args.mode