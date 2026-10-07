import json
import unittest
from unittest.mock import patch
from session_data import SessionLibrary

def row(**changes):
    data = dict(ts='2024-01-01T23:30:00Z',ms_played=180000,
        master_metadata_track_name='Testtrack',master_metadata_album_artist_name='Testartiest',
        spotify_track_uri='spotify:track:example',skipped=False,ip_addr='192.0.2.1')
    data.update(changes)
    return data

def export(*rows):
    return json.dumps(rows).encode()

NAME='Streaming_History_Audio_2024.json'

class SessionTests(unittest.TestCase):
    def test_isolation(self):
        alice,bob=SessionLibrary(),SessionLibrary()
        alice.add(NAME,export(row()))
        self.assertTrue(bob.dataframe().empty)
        self.assertEqual(bob.uploaded_bytes,0)
        self.assertEqual(bob.imports,[])
        self.assertEqual(bob.add(NAME,export(row()))['added'],1)
        alice.records.clear()
        self.assertEqual(len(bob.records),1)

    def test_overlap_and_reordered_fields(self):
        state=SessionLibrary()
        original=row()
        self.assertEqual(state.add(NAME,export(original,original))['duplicates'],1)
        reordered=dict(reversed(list(original.items())))
        stats=state.add('Streaming_History_Audio_extra.json',export(reordered,row(ts='2024-01-02T12:00:00Z')))
        self.assertEqual((stats['added'],stats['duplicates']),(1,1))
        again=state.add(NAME,export(original,original))
        self.assertEqual((again['added'],again['duplicates']),(0,2))
        frame=state.dataframe()
        self.assertEqual(len(frame),2)
        self.assertNotIn('ip_addr',frame.columns)
        self.assertEqual(str(frame.iloc[0]['date']),'2024-01-02')
        self.assertEqual(frame.iloc[0]['minutes'],3)

    def test_reject_atomically_and_exclude_podcasts(self):
        state=SessionLibrary()
        for invalid in [b'bad',b'{}',export(row(),row(ms_played=-1)),export(row(ts='invalid')),export(row(ts='2400-01-01T00:00:00Z'))]:
            with self.assertRaises(ValueError):state.add(NAME,invalid)
        self.assertEqual(state.records,{})
        self.assertEqual(state.imports,[])
        with self.assertRaises(ValueError):state.add('Streaming_History_Video_2024.json',export(row()))
        result=state.add(NAME,export(row(),row(master_metadata_track_name=None,episode_name='Podcast')))
        self.assertEqual((result['added'],result['ignored']),(1,1))

    def test_limits_are_atomic(self):
        state=SessionLibrary()
        with patch('session_data.MAX_FILE_BYTES',5):
            with self.assertRaises(ValueError):state.add(NAME,export(row()))
        with patch('session_data.MAX_SESSION_BYTES',5):
            with self.assertRaises(ValueError):state.add(NAME,export(row()))
        state.add(NAME,export(row()))
        with patch('session_data.MAX_RECORDS',1):
            with self.assertRaises(ValueError):state.add(NAME,export(row(ts='2024-01-02T00:00:00Z')))
        self.assertEqual(len(state.records),1)
        self.assertEqual(len(state.imports),1)

    def test_same_time_different_original_field_is_not_duplicate(self):
        state=SessionLibrary()
        self.assertEqual(state.add(NAME,export(row(),row(ip_addr='192.0.2.2')))['added'],2)

if __name__=='__main__':unittest.main()
