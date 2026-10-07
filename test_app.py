import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from test_session_data import row,export,NAME

APP=str(Path(__file__).with_name('app.py'))

class AppTests(unittest.TestCase):
    def test_empty_sessions_upload_data_filters_and_clear(self):
        alice=AppTest.from_file(APP,default_timeout=30).run()
        bob=AppTest.from_file(APP,default_timeout=30).run()
        self.assertFalse(alice.exception)
        self.assertFalse(bob.exception)
        self.assertEqual(len(alice.metric),0)
        alice.session_state.library.add(NAME,export(row(),row(ts='2025-04-01T12:00:00Z')))
        alice.run()
        self.assertFalse(alice.exception,[e.message for e in alice.exception])
        self.assertTrue(alice.metric)
        self.assertEqual(len(bob.session_state.library.records),0)
        self.assertEqual(len(bob.metric),0)
        alice.sidebar.slider[0].set_value(240).run()
        self.assertFalse(alice.exception)
        self.assertTrue(any('Geen muziek' in x.value for x in alice.info))
        alice.sidebar.button[0].click().run()
        self.assertFalse(alice.exception)
        self.assertEqual(len(alice.session_state.library.records),0)
        self.assertEqual(len(alice.metric),0)

if __name__=='__main__':unittest.main()
