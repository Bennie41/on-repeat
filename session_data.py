"""Bezoekersdata leeft alleen in een SessionLibrary in st.session_state.

Geen bestanden, database, globale datasets of gedeelde caches.
"""
from dataclasses import dataclass, field
import hashlib
import json
import math
import re
import pandas as pd

MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_SESSION_BYTES = 100 * 1024 * 1024
MAX_RECORDS = 150_000
MAX_FILES = 30
AUDIO_NAME = re.compile(r"^Streaming_History_Audio.*\.json$", re.I)

@dataclass
class SessionLibrary:
    records: dict = field(default_factory=dict)
    imports: list = field(default_factory=list)
    seen_files: dict = field(default_factory=dict)
    uploaded_bytes: int = 0

    def add(self, filename, payload):
        if not AUDIO_NAME.fullmatch(filename):
            raise ValueError("Kies een originele Streaming_History_Audio…json-export. Video-exports worden niet ondersteund.")
        if len(payload) > MAX_FILE_BYTES:
            raise ValueError("Dit bestand is groter dan 50 MB. Upload de afzonderlijke JSON-bestanden uit je export.")
        checksum = hashlib.sha256(payload).hexdigest()
        if checksum in self.seen_files:
            previous = self.seen_files[checksum]
            return dict(filename=filename, total=previous['total'], added=0,
                        duplicates=previous['eligible'], ignored=previous['ignored'])
        if len(self.seen_files) >= MAX_FILES or self.uploaded_bytes + len(payload) > MAX_SESSION_BYTES:
            raise ValueError("Deze sessie ondersteunt maximaal 30 bestanden en 100 MB. Begin een nieuwe sessie om een andere selectie te bekijken.")
        try:
            rows = json.loads(payload)
        except (ValueError, UnicodeDecodeError, RecursionError) as exc:
            raise ValueError("Dit bestand bevat geen geldige JSON.") from exc
        if not isinstance(rows, list):
            raise ValueError("Gebruik de uitgebreide Spotify-streaminggeschiedenis: een JSON-lijst met afspeelregistraties.")
        if len(rows) > MAX_RECORDS:
            raise ValueError("Dit bestand bevat meer dan 150.000 records. Kies een kleinere export.")
        prepared = {}
        eligible = ignored = 0
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict) or 'ts' not in row or 'ms_played' not in row:
                raise ValueError(f"Record {index} mist de vereiste velden. Gebruik de uitgebreide streaminggeschiedenis van Spotify.")
            if not row.get('master_metadata_track_name') or row.get('episode_name') or row.get('audiobook_title'):
                ignored += 1
                continue
            try:
                stamp = pd.Timestamp(row['ts'])
                if pd.isna(stamp) or stamp.tzinfo is None:
                    raise ValueError()
                stamp = stamp.tz_convert('UTC')
                # Begrens datums voor veilige resampling en nanosecondetabellen.
                if not pd.Timestamp('2000-01-01',tz='UTC') <= stamp <= pd.Timestamp.now(tz='UTC') + pd.Timedelta(days=2):
                    raise ValueError()
                duration = row['ms_played']
                if isinstance(duration, bool) or not isinstance(duration,(int,float)) or not math.isfinite(duration) or duration < 0 or duration != int(duration) or duration > 2**63-1:
                    raise ValueError()
                for key in ['master_metadata_track_name','master_metadata_album_artist_name','master_metadata_album_album_name','spotify_track_uri','platform']:
                    if row.get(key) is not None and not isinstance(row[key],str):
                        raise ValueError()
                for key in ['skipped','shuffle']:
                    if row.get(key) is not None and not isinstance(row[key],bool):
                        raise ValueError()
                canonical = json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
                identity = hashlib.sha256(canonical.encode()).hexdigest()
            except (ValueError,TypeError,OverflowError,RecursionError) as exc:
                raise ValueError(f"Record {index} bevat een ongeldige datum, afspeeltijd of veldwaarde. Het bestand is niet toegevoegd.") from exc
            eligible += 1
            if identity not in self.records:
                prepared[identity] = dict(record_hash=identity,played_at=stamp,ms_played=int(duration),
                    track=row['master_metadata_track_name'],artist=row.get('master_metadata_album_artist_name') or 'Onbekende artiest',
                    album=row.get('master_metadata_album_album_name') or 'Onbekend album',track_id=row.get('spotify_track_uri') or None,
                    platform=row.get('platform') or 'Onbekend',skipped=row.get('skipped'),shuffle=row.get('shuffle'))
        if len(self.records) + len(prepared) > MAX_RECORDS:
            raise ValueError("Deze sessie ondersteunt maximaal 150.000 unieke muziekrecords. Het bestand is niet toegevoegd.")
        # Wijzig de sessie pas nadat het hele bestand geldig is bevonden.
        report = dict(filename=filename,total=len(rows),added=len(prepared),duplicates=eligible-len(prepared),ignored=ignored)
        self.records.update(prepared)
        self.seen_files[checksum] = dict(total=len(rows),eligible=eligible,ignored=ignored)
        self.uploaded_bytes += len(payload)
        self.imports.append(dict(report,imported_at=pd.Timestamp.now(tz='UTC')))
        return report

    def dataframe(self):
        frame = pd.DataFrame(self.records.values())
        if not frame.empty:
            frame['local_time'] = pd.to_datetime(frame['played_at'],utc=True).dt.tz_convert('Europe/Amsterdam')
            frame['date'] = frame['local_time'].dt.date
            frame['minutes'] = frame['ms_played']/60_000
            frame['track_key'] = frame['track_id'].fillna(frame['artist']+' · '+frame['track'])
        return frame
