#!/usr/bin/env python

import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kvutil import kv


class DataDirectoryTests(unittest.TestCase):
    """
    Ensure that the directory used to store the database is XDG Base Directory
    Specification compliant.

    More info here:
    https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """

    XDG_DATA_DIR_ENV_VAR = "XDG_DATA_DIR"

    def test_xdg_data_dir(self):
        test_directory = "/path/to/test/directory"

        # set environment
        os.environ[self.XDG_DATA_DIR_ENV_VAR] = test_directory

        # get data directory
        result = kv.get_data_file_path()
        if not result.startswith(test_directory):
            self.fail(
                "Expected data direcory to start with '%s', actual: %s"
                % (test_directory, result)
            )

        # cleanup environment
        del os.environ[self.XDG_DATA_DIR_ENV_VAR]

    def test_default_data_dir(self):
        # ensure env is clean
        try:
            del os.environ[self.XDG_DATA_DIR_ENV_VAR]
        except KeyError:
            pass

        expected = os.path.join(Path.home(), ".local", "share")
        result = kv.get_data_file_path()

        if not expected in result:
            self.fail(
                "Expected data directory to start with '%s', actual: %s"
                % (expected, result)
            )


class ReadTests(unittest.TestCase):
    def test_successful_read(self):
        # setup db
        db = {"test_key": b"test_value"}

        with tempfile.TemporaryFile() as lockfile:
            # patch stdout
            with patch("sys.stdout", new=io.StringIO()) as out:
                kv.execute_read(db, "test_key", lockfile)
                self.assertEqual(out.getvalue().strip(), "test_value")

    def test_failed_read(self):
        # setup db
        db = {}

        with tempfile.TemporaryFile() as lockfile:
            # patch stdout
            with patch("sys.stdout", new=io.StringIO()) as out:
                kv.execute_read(db, "doesn't matter", lockfile)
                self.assertEqual(out.getvalue().strip(), "")


class WriteTests(unittest.TestCase):
    def test_successful_write(self):
        # setup db
        db = {}

        with tempfile.TemporaryFile() as lockfile:
            kv.execute_write(db, "test_key", "test_value", lockfile)
            self.assertIn("test_key", db)
            self.assertEqual(db["test_key"], "test_value")


class DeleteTests(unittest.TestCase):
    def test_successful_delete(self):
        # setup db
        db = {"test_key": b"test_value"}

        with tempfile.TemporaryFile() as lockfile:
            kv.execute_delete(db, "test_key", lockfile)
            self.assertNotIn("test_key", db)

    def test_unsuccessful_delete(self):
        # setup db
        db = {"test_key": b"test_value"}

        with tempfile.TemporaryFile() as lockfile:
            kv.execute_delete(db, "not_test_key", lockfile)
            self.assertIn("test_key", db)
            self.assertEqual(len(db), 1)


class ListTests(unittest.TestCase):
    def test_list_keys(self):
        # setup db
        num_keys = 50
        db = {}
        for i in range(num_keys):
            db[b"key%d" % i] = "value%d" % i

        with tempfile.TemporaryFile() as lockfile:
            # patch stdout
            with patch("sys.stdout", new=io.StringIO()) as out:
                kv.execute_list(db, lockfile)
                lines = out.getvalue().split("\n")
                for i in range(num_keys):
                    self.assertEqual(lines[i], "key%d" % i)


if __name__ == "__main__":
    unittest.main()
