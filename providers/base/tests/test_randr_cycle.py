#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# Written by:
#   Hanhsuan Lee <hanhsuan.lee@canonical.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from unittest.mock import patch, MagicMock, mock_open
import subprocess
import unittest
import tarfile
import sys
import os

sys.modules["checkbox_support"] = MagicMock()
sys.modules["checkbox_support.helpers"] = MagicMock()
sys.modules["checkbox_support.dbus.gnome_monitor"] = MagicMock()
from randr_cycle import resolution_filter, action, MonitorTest


class GenScreenshotPath(unittest.TestCase):
    """
    This function should generate dictionary such as
    [screenshot_dir]_[keyword]
    """

    @patch("os.makedirs")
    def test_before_suspend_without_keyword(self, mock_mkdir):

        mt = MonitorTest()
        with patch("builtins.open", mock_open(read_data="0")) as mock_file:
            self.assertEqual(
                mt.gen_screenshot_path("", "test"), "test/xrandr_screens"
            )
        mock_file.assert_called_with("/sys/power/suspend_stats/success", "r")
        mock_mkdir.assert_called_with("test/xrandr_screens", exist_ok=True)

    @patch("os.makedirs")
    def test_after_suspend_without_keyword(self, mock_mkdir):

        mt = MonitorTest()
        with patch("builtins.open", mock_open(read_data="1")) as mock_file:
            self.assertEqual(
                mt.gen_screenshot_path(None, "test"),
                "test/xrandr_screens_after_suspend",
            )
        mock_file.assert_called_with("/sys/power/suspend_stats/success", "r")
        mock_mkdir.assert_called_with(
            "test/xrandr_screens_after_suspend", exist_ok=True
        )

    @patch("os.makedirs")
    def test_with_keyword(self, mock_mkdir):

        mt = MonitorTest()
        self.assertEqual(
            mt.gen_screenshot_path("key", "test"), "test/xrandr_screens_key"
        )
        mock_mkdir.assert_called_with("test/xrandr_screens_key", exist_ok=True)


class TestScreenshotTarring(unittest.TestCase):

    @patch('os.listdir')
    @patch('tarfile.open')
    @patch('os.path.join')
    def test_tar_screenshot_dir(self, mock_join, mock_tar_open, mock_listdir):
        # Arrange
        path = "screenshots"
        mock_listdir.return_value = ['screenshot1.png', 'screenshot2.png']

        # Mocking tarfile object
        mock_tar = MagicMock()
        mock_tar_open.return_value.__enter__.return_value = mock_tar

        # Mocking os.path.join to return a proper path
        mock_join.side_effect = lambda *args: "/".join(args)

        # Act
        self.tar_screenshot_dir(path)

        # Assert
        mock_tar_open.assert_called_once_with("screenshots.tgz", "w:gz")
        self.assertEqual(mock_tar.add.call_count, 2)
        mock_tar.add.assert_any_call("screenshots/screenshot1.png", "screenshot1.png")
        mock_tar.add.assert_any_call("screenshots/screenshot2.png", "screenshot2.png")

    @patch('os.listdir')
    @patch('tarfile.open')
    def test_tar_screenshot_dir_io_error(self, mock_tar_open, mock_listdir):
        # Arrange
        path = "screenshots"
        mock_listdir.return_value = ['screenshot1.png']

        # Simulate an IOError when opening the tarfile
        mock_tar_open.side_effect = IOError("Unable to open tar file")

        # Act
        try:
            self.tar_screenshot_dir(path)
            result = True  # If no exception is raised, we consider it successful.
        except Exception:
            result = False

        # Assert
        self.assertTrue(result)  # Ensure it handles IOError without raising an unhandled exception.



class ParseArgsTests(unittest.TestCase):
    def test_success(self):
        mt = MonitorTest()
        # no arguments, load default
        args = []
        rv = mt.parse_args(args)
        self.assertEqual(rv.cycle, "both")
        self.assertEqual(rv.keyword, "")
        self.assertEqual(rv.screenshot_dir, os.environ["HOME"])

        # change cycle type
        args = ["--cycle", "resolution"]
        rv = mt.parse_args(args)
        self.assertEqual(rv.cycle, "resolution")
        self.assertEqual(rv.keyword, "")
        self.assertEqual(rv.screenshot_dir, os.environ["HOME"])

        # change keyword
        args = ["--keyword", "key"]
        rv = mt.parse_args(args)
        self.assertEqual(rv.cycle, "both")
        self.assertEqual(rv.keyword, "key")
        self.assertEqual(rv.screenshot_dir, os.environ["HOME"])

        # change screenshot_dir
        args = ["--screenshot_dir", "dir"]
        rv = mt.parse_args(args)
        self.assertEqual(rv.cycle, "both")
        self.assertEqual(rv.keyword, "")
        self.assertEqual(rv.screenshot_dir, "dir")

        # change all
        args = [
            "-c",
            "transform",
            "--keyword",
            "key",
            "--screenshot_dir",
            "dir",
        ]
        rv = mt.parse_args(args)
        self.assertEqual(rv.cycle, "transform")
        self.assertEqual(rv.keyword, "key")
        self.assertEqual(rv.screenshot_dir, "dir")


class MainTests(unittest.TestCase):
    @patch("randr_cycle.MonitorTest.parse_args")
    @patch("checkbox_support.helpers.display_info.get_monitor_config")
    @patch("randr_cycle.MonitorTest.gen_screenshot_path")
    @patch("randr_cycle.MonitorTest.tar_screenshot_dir")
    def test_cycle_both(
        self, mock_dir, mock_path, mock_config, mock_parse_args
    ):
        args_mock = MagicMock()
        args_mock.cycle = "both"
        args_mock.keyword = ""
        args_mock.screenshot_dir = "test"
        mock_parse_args.return_value = args_mock

        mock_path.return_value = "test"

        monitor_config_mock = MagicMock()
        mock_config.return_value = monitor_config_mock

        self.assertEqual(MonitorTest().main(), None)
        monitor_config_mock.assert_called_with(
            resolution=True,
            resolution_filter=resolution_filter,
            transform=True,
            action=action,
            path="test",
        )

        mock_dir.assert_called_with("test")

    @patch("randr_cycle.MonitorTest.parse_args")
    @patch("checkbox_support.helpers.display_info.get_monitor_config")
    @patch("randr_cycle.MonitorTest.gen_screenshot_path")
    @patch("randr_cycle.MonitorTest.tar_screenshot_dir")
    def test_cycle_resolution(
        self, mock_dir, mock_path, mock_config, mock_parse_args
    ):
        args_mock = MagicMock()
        args_mock.cycle = "resolution"
        args_mock.keyword = ""
        args_mock.screenshot_dir = "test"
        mock_parse_args.return_value = args_mock

        mock_path.return_value = "test"

        monitor_config_mock = MagicMock()
        mock_config.return_value = monitor_config_mock

        self.assertEqual(MonitorTest().main(), None)
        monitor_config_mock.assert_called_with(
            resolution=True,
            resolution_filter=resolution_filter,
            transform=False,
            action=action,
            path="test",
        )

        mock_dir.assert_called_with("test")

    @patch("randr_cycle.MonitorTest.parse_args")
    @patch("checkbox_support.helpers.display_info.get_monitor_config")
    @patch("randr_cycle.MonitorTest.gen_screenshot_path")
    @patch("randr_cycle.MonitorTest.tar_screenshot_dir")
    def test_cycle_transform(
        self, mock_dir, mock_path, mock_config, mock_parse_args
    ):
        args_mock = MagicMock()
        args_mock.cycle = "transform"
        args_mock.keyword = ""
        args_mock.screenshot_dir = "test"
        mock_parse_args.return_value = args_mock

        mock_path.return_value = "test"

        monitor_config_mock = MagicMock()
        mock_config.return_value = monitor_config_mock

        self.assertEqual(MonitorTest().main(), None)
        monitor_config_mock.assert_called_with(
            resolution=False,
            resolution_filter=resolution_filter,
            transform=True,
            action=action,
            path="test",
        )

        mock_dir.assert_called_with("test")
