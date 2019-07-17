import unittest

from .main import generate_status_msg, get_horizon_sync_status


class TestHealthCheck(unittest.TestCase):
    def test_generate_status_msg(self):
        is_horizon_synced, is_core_synced = True, True
        test_msg = 'Core, Horizon status is: (synced, synced)'
        self.assertEquals(generate_status_msg(is_core_synced, is_core_synced), test_msg)

    def test_get_horizon_sync_status(self):
        # Horizon not synced with internal DB
        core_info = {'info': {'ledger': {'num': 50}}}
        horizon_info = {'core_latest_ledger': 30, 'history_latest_ledger': 50}
        self.assertFalse(get_horizon_sync_status(core_info, horizon_info))

        # Horizon not synced with internal DB
        core_info = {'info': {'ledger': {'num': 50}}}
        horizon_info = {'core_latest_ledger': 50, 'history_latest_ledger': 30}
        self.assertFalse(get_horizon_sync_status(core_info, horizon_info))

        # Horizon not synced with Core DB
        core_info = {'info': {'ledger': {'num': 30}}}
        horizon_info = {'core_latest_ledger': 50, 'history_latest_ledger': 50}
        self.assertFalse(get_horizon_sync_status(core_info, horizon_info))

        # Horizon synced with internal DB
        core_info = {'info': {'ledger': {'num': 50}}}
        horizon_info = {'core_latest_ledger': 41, 'history_latest_ledger': 47}
        self.assertTrue(get_horizon_sync_status(core_info, horizon_info))

        # Horizon synced with internal DB
        core_info = {'info': {'ledger': {'num': 50}}}
        horizon_info = {'core_latest_ledger': 45, 'history_latest_ledger': 54}
        self.assertTrue(get_horizon_sync_status(core_info, horizon_info))
