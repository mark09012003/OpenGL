import threading
import unittest

from network_control import (MasterClient, SlaveControlServer, normalize_endpoint,
                             parse_arp_neighbors)


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

    def test_master_discovers_slave_and_slave_records_master(self):
        found = MasterClient("a-secure-shared-key", timeout=1).discover(
            self.server.port, timeout=0.4, include_arp=False,
            broadcast_addresses=("127.0.0.1",),
        )
        self.assertIn(self.endpoint, found)
        self.assertEqual(self.server.last_master, "127.0.0.1")

    def test_endpoint_adds_scheme_and_default_port(self):
        self.assertEqual(normalize_endpoint("192.168.1.8", 9000),
                         "http://192.168.1.8:9000")

    def test_parses_windows_arp_table(self):
        output = """
Interface: 192.168.1.10 --- 0x8
  Internet Address      Physical Address      Type
  192.168.1.1           aa-bb-cc-dd-ee-ff     dynamic
  192.168.1.25          11-22-33-44-55-66     dynamic
"""
        self.assertEqual(parse_arp_neighbors(output),
                         ["192.168.1.10", "192.168.1.1", "192.168.1.25"])


if __name__ == "__main__":
    unittest.main()
