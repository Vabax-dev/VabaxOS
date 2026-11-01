#!/usr/bin/env python3
"""Tests for vabaxos-announce: "VabaxOS is ready" when Orca speaks, and
one battery warning at 10 percent. Made-up bus: nothing is spoken.

    python3 tests/announce/test_announce.py
"""

import importlib.machinery
import importlib.util
import os
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(REPO, "packages", "vabaxos-accessibility", "root", "usr", "bin", "vabaxos-announce")
loader = importlib.machinery.SourceFileLoader("vabaxos_announce", PROGRAM)
spec = importlib.util.spec_from_loader("vabaxos_announce", loader)
announce = importlib.util.module_from_spec(spec)
loader.exec_module(announce)

ON_BATTERY, CHARGING = 2, 1


class BatteryTest(unittest.TestCase):

    def walk(self, readings):
        warned, spoken = False, []
        for percent, state in readings:
            speak, warned = announce.battery_step(warned, percent, state)
            if speak:
                spoken.append(percent)
        return spoken

    def test_one_warning_at_ten(self):
        readings = [(p, ON_BATTERY) for p in range(30, 0, -1)]
        self.assertEqual(self.walk(readings), [10])

    def test_again_after_charging(self):
        readings = [(11, ON_BATTERY), (10, ON_BATTERY), (9, ON_BATTERY), (9, CHARGING), (12, CHARGING),
                    (11, ON_BATTERY), (10, ON_BATTERY)]
        self.assertEqual(self.walk(readings), [10, 10])

    def test_not_while_charging(self):
        self.assertEqual(self.walk([(5, CHARGING), (4, CHARGING)]), [])

    def test_starting_already_low(self):
        self.assertEqual(self.walk([(7, ON_BATTERY), (6, ON_BATTERY)]), [7])


class FakeBus:
    def __init__(self, orca_after):
        self.orca_after, self.checks, self.said = orca_after, 0, []

    def has_orca(self):
        self.checks += 1
        return self.orca_after is not None and self.checks > self.orca_after

    def say(self, text):
        self.said.append(text)
        return True


class ReadyTest(unittest.TestCase):

    def test_said_once_orca_runs(self):
        bus = FakeBus(orca_after=4)
        self.assertTrue(announce.ready(bus, sleep=lambda s: None))
        self.assertEqual(bus.said, ["VabaxOS is ready."])

    def test_silent_without_orca(self):
        bus = FakeBus(orca_after=None)
        self.assertFalse(announce.ready(bus, wait=2, sleep=lambda s: None))
        self.assertEqual(bus.said, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
