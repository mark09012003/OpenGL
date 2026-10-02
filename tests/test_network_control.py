import threading
import unittest

from network_control import MasterClient, SlaveControlServer, normalize_endpoint


class NetworkControlTests(unittest.TestCase):
    def setUp(self):
        self.commands = []
        self.command_event = threading.Event()

        def command_callback(command):
            self.commands.append(command)
            self.command_event.set()

        self.server = SlaveControlServer(
            0, "a-secure-shared-key",
            lambda: {"state": "stopped", "name": "test-slave"},
            command_callback, host="127.0.0.1",
        )
        self.server.start()
        self.endpoint = f"127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()

    def test_master_reads_status_and_sends_command(self):
        client = MasterClient("a-secure-shared-key", timeout=1)
        self.assertEqual(client.status(self.endpoint)["state"], "stopped")
        self.assertTrue(client.command(self.endpoint, "start")["ok"])
        self.assertTrue(self.command_event.wait(1))
        self.assertEqual(self.commands, ["start"])

    def test_wrong_key_is_rejected(self):
        with self.assertRaisesRegex(ConnectionError, "共享密鑰"):
            MasterClient("wrong-key", timeout=1).status(self.endpoint)

    def test_endpoint_adds_scheme_and_default_port(self):
        self.assertEqual(normalize_endpoint("192.168.1.8", 9000),
                         "http://192.168.1.8:9000")


if __name__ == "__main__":
    unittest.main()
