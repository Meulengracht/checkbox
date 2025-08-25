import json

from unittest import TestCase
from unittest.mock import patch, MagicMock, ANY

from checkbox_support.snap_utils.snapd import AsyncException, Snapd


class TestSnapd(TestCase):
    @patch("checkbox_support.snap_utils.snapd.time.sleep")
    @patch("checkbox_support.snap_utils.snapd.time.time")
    def test_poll_change_done(self, mock_time, mock_sleep):
        mock_self = MagicMock()
        mock_self.change.return_value = "Done"
        self.assertTrue(Snapd._poll_change(mock_self, 0))

    @patch("checkbox_support.snap_utils.snapd.time.sleep")
    @patch("checkbox_support.snap_utils.snapd.time.time")
    def test_poll_change_timeout(self, mock_time, mock_sleep):
        mock_time.side_effect = [0, 1]
        mock_self = MagicMock()
        mock_self._task_timeout = 0
        with self.assertRaises(AsyncException):
            Snapd._poll_change(mock_self, 0)

    @patch("checkbox_support.snap_utils.snapd.time.sleep")
    @patch("checkbox_support.snap_utils.snapd.time.time")
    def test_poll_change_doing(self, mock_time, mock_sleep):
        mock_time.return_value = 0
        mock_self = MagicMock()
        mock_self.change.side_effect = ["Doing", "Done"]
        mock_self._task_timeout = 0
        mock_self.tasks.return_value = [
            {
                "summary": "Test",
                "status": "Doing",
                "progress": {"label": "", "done": 1, "total": 1},
            },
        ]
        Snapd._poll_change(mock_self, 0)
        message = "(Doing) Test"
        mock_self._info.assert_called_with(message)
        mock_self.change.side_effect = ["Doing", "Done"]
        mock_self.tasks.return_value = [
            {
                "summary": "Test",
                "status": "Doing",
                "progress": {"label": "Downloading", "done": 1, "total": 2},
            },
        ]
        Snapd._poll_change(mock_self, 0)
        message = "(Doing) Test (50.0%)"
        mock_self._info.assert_called_with(message)

    @patch("checkbox_support.snap_utils.snapd.time.sleep")
    @patch("checkbox_support.snap_utils.snapd.time.time")
    def test_poll_change_wait(self, mock_time, mock_sleep):
        mock_time.return_value = 0
        mock_self = MagicMock()
        mock_self.change.return_value = "Wait"
        mock_self._task_timeout = 0
        mock_self.tasks.return_value = [
            {
                "summary": "Test",
                "status": "Wait",
                "progress": {"label": "", "done": 1, "total": 1},
            },
        ]
        Snapd._poll_change(mock_self, 0)
        message = "(Wait) Test"
        mock_self._info.assert_called_with(message)

    @patch("checkbox_support.snap_utils.snapd.time.sleep")
    @patch("checkbox_support.snap_utils.snapd.time.time")
    def test_poll_change_error(self, mock_time, mock_sleep):
        mock_time.return_value = 0
        mock_self = MagicMock()
        mock_self.change.return_value = "Error"
        mock_self._task_timeout = 0
        mock_self.tasks.return_value = [
            {
                "summary": "Test",
                "status": "Error",
                "progress": {"label": "", "done": 1, "total": 1},
            },
        ]
        message = "(Error) Test"
        with self.assertRaises(AsyncException):
            Snapd._poll_change(mock_self, 0)
        mock_self._info.assert_called_with(message)

    def test_install_accepted(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Accepted",
            "change": "1",
        }
        response = Snapd.install(mock_self, "test")
        self.assertEqual(response, mock_self._post.return_value)
        mock_self._poll_change.assert_called_with("1")

    def test_install_other(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Other",
            "change": "1",
        }
        response = Snapd.install(mock_self, "test")
        self.assertEqual(response, mock_self._post.return_value)
        mock_self._poll_change.assert_not_called()

    def test_install_revision(self):
        mock_self = MagicMock()
        Snapd.install(mock_self, "test", revision="1")
        test_data = {"action": "install", "channel": "stable", "revision": "1"}
        mock_self._post.assert_called_with(ANY, json.dumps(test_data))

    def test_remove_accepted(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Accepted",
            "change": "1",
        }
        response = Snapd.remove(mock_self, "test")
        self.assertEqual(response, mock_self._post.return_value)
        mock_self._poll_change.assert_called_with("1")

    def test_remove_other(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Other",
            "change": "1",
        }
        response = Snapd.remove(mock_self, "test")
        self.assertEqual(response, mock_self._post.return_value)
        mock_self._poll_change.assert_not_called()

    def test_remove_revision(self):
        mock_self = MagicMock()
        Snapd.remove(mock_self, "test", revision="1")
        test_data = {"action": "remove", "revision": "1"}
        mock_self._post.assert_called_with(ANY, json.dumps(test_data))

    def test_connect_success(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Accepted",
            "change": "1",
        }
        slot_snap = "test_slot_snap"
        slot_slot = "test_slot"
        plug_snap = "test_plug_snap"
        plug_plug = "test_plug"

        Snapd.connect_or_disconnect(
            mock_self, slot_snap, slot_slot, plug_snap, plug_plug
        )
        mock_self._post.assert_called_once_with(
            mock_self._interfaces,
            json.dumps(
                {
                    "action": "connect",
                    "slots": [{"snap": slot_snap, "slot": slot_slot}],
                    "plugs": [{"snap": plug_snap, "plug": plug_plug}],
                }
            ),
        )
        mock_self._poll_change.assert_called_with("1")

    def test_connect_fail(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Not_Accepted",
            "change": "1",
        }
        slot_snap = "test_slot_snap"
        slot_slot = "test_slot"
        plug_snap = "test_plug_snap"
        plug_plug = "test_plug"

        Snapd.connect_or_disconnect(
            mock_self, slot_snap, slot_slot, plug_snap, plug_plug
        )
        mock_self._post.assert_called_once_with(
            mock_self._interfaces,
            json.dumps(
                {
                    "action": "connect",
                    "slots": [{"snap": slot_snap, "slot": slot_slot}],
                    "plugs": [{"snap": plug_snap, "plug": plug_plug}],
                }
            ),
        )
        mock_self._poll_change.assert_not_called()

    def test_disconnect_success(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Accepted",
            "change": "1",
        }
        slot_snap = "test_slot_snap"
        slot_slot = "test_slot"
        plug_snap = "test_plug_snap"
        plug_plug = "test_plug"

        Snapd.connect_or_disconnect(
            mock_self,
            slot_snap,
            slot_slot,
            plug_snap,
            plug_plug,
            action="disconnect",
        )
        mock_self._post.assert_called_once_with(
            mock_self._interfaces,
            json.dumps(
                {
                    "action": "disconnect",
                    "slots": [{"snap": slot_snap, "slot": slot_slot}],
                    "plugs": [{"snap": plug_snap, "plug": plug_plug}],
                }
            ),
        )
        mock_self._poll_change.assert_called_with("1")

    def test_disconnect_fail(self):
        mock_self = MagicMock()
        mock_self._poll_change = MagicMock()
        mock_self._post.return_value = {
            "type": "async",
            "status": "Not_Accepted",
            "change": "1",
        }
        slot_snap = "test_slot_snap"
        slot_slot = "test_slot"
        plug_snap = "test_plug_snap"
        plug_plug = "test_plug"

        Snapd.connect_or_disconnect(
            mock_self,
            slot_snap,
            slot_slot,
            plug_snap,
            plug_plug,
            action="disconnect",
        )
        mock_self._post.assert_called_once_with(
            mock_self._interfaces,
            json.dumps(
                {
                    "action": "disconnect",
                    "slots": [{"snap": slot_snap, "slot": slot_slot}],
                    "plugs": [{"snap": plug_snap, "plug": plug_plug}],
                }
            ),
        )
        mock_self._poll_change.assert_not_called()

    @patch.object(Snapd, "connect_or_disconnect")
    def test_connect_called(self, mock_connect_or_disconnect):
        snapd = Snapd()
        slot_snap = "test_slot_snap"
        slot_slot = "test_slot"
        plug_snap = "test_plug_snap"
        plug_plug = "test_plug"
        snapd.connect(slot_snap, slot_slot, plug_snap, plug_plug)

        mock_connect_or_disconnect.assert_called_once_with(
            slot_snap, slot_slot, plug_snap, plug_plug
        )

    @patch.object(Snapd, "connect_or_disconnect")
    def test_disconnect_called(self, mock_connect_or_disconnect):
        snapd = Snapd()
        slot_snap = "test_slot_snap"
        slot_slot = "test_slot"
        plug_snap = "test_plug_snap"
        plug_plug = "test_plug"
        snapd.disconnect(slot_snap, slot_slot, plug_snap, plug_plug)

        mock_connect_or_disconnect.assert_called_once_with(
            slot_snap,
            slot_slot,
            plug_snap,
            plug_plug,
            action="disconnect",
        )
