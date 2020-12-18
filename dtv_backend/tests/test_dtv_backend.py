#!/usr/bin/env python

"""Tests for `dtv_backend` package."""


import unittest
from click.testing import CliRunner

from dtv_backend import cli


class TestDtv_backend(unittest.TestCase):
    """Tests for `dtv_backend` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        print('output', result.output)
        assert 'simulate' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help' in help_result.output
