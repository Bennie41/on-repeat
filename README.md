# On Repeat — deelbare Spotify-analyse

Een Streamlit-dashboard voor vrienden die hun **eigen** uitgebreide Spotify-streaminggeschiedenis willen analyseren. Iedere browsersessie begint leeg. Dit project bevat geen luistergegevens.

## Lokaal testen
Gebruik Python 3.13 en installeer `requirements.txt` in een virtuele omgeving. Start vanuit deze map:

```bash
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

Open http://127.0.0.1:8502. De persoonlijke dashboardversie op poort 8501 staat hier los van.

## Gebruik
- Pak je Spotify-export uit en upload de bestanden `Streaming_History_Audio*.json`.
- Upload meerdere bestanden tegelijk of voeg later bestanden toe.
- Exacte duplicaten worden alleen binnen je eigen sessie uitgesloten.
- Gebruik periode-, artiest- en afspeeltijdfilters, toplijsten, heatmaps en jaarvergelijkingen.
- Met **Mijn sessie wissen** maak je de app-sessie leeg en verwijder je de filters.
- Bij een nieuwe browsersessie of serverherstart moet je opnieuw uploaden. Bewaar je exports zelf.

Ondersteuning: alleen het uitgebreide Spotify-audioformaat; geen ZIP, vereenvoudigde StreamingHistory-export of video. Maximaal 50 MB per bestand, 100 MB / 30 bestanden / 150.000 unieke muziekrecords per sessie. De grenzen helpen het geheugengebruik beperken; capaciteit voor gelijktijdige bezoekers hangt af van de hosting.

## Gegevens en sessies
`SessionLibrary` staat uitsluitend in `st.session_state`. Er is geen globale dataset, gedeelde datacache, database of automatische import uit een lokale map. De app schrijft geen uploads naar schijf. De analysetabel bevat geen IP-adressen uit exports. Voor exacte deduplicatie berekenen we een hash over alle oorspronkelijke recordvelden.

Bestanden worden naar de appserver geüpload en daar verwerkt. Dit is dus geen verwerking uitsluitend op het apparaat van de bezoeker. Streamlit beheert tijdelijke uploadbuffers en sessiegeheugen. Het sluiten van een tabblad garandeert geen onmiddellijke verwijdering uit RAM. De app biedt geen accounts, herstel of blijvende opslag.

## Online publiceren via Streamlit Community Cloud
Publiceer **alleen de inhoud van deze map** als een eigen GitHub-repository. Upload nooit de bovenliggende persoonlijke projectmap, SpotifyData, een DuckDB-database of het oefennotebook.

1. Maak een GitHub-repository met de bestanden uit deze map, inclusief `.streamlit/config.toml` en `.gitignore`.
2. Meld je aan bij Streamlit Community Cloud en koppel GitHub.
3. Maak een app met deze repository en `app.py` als startbestand. Kies Python 3.13 in de geavanceerde instellingen.
4. Deel de uiteindelijke HTTPS-link. Het configuratiebestand bevat bewust geen vast lokaal IP-adres.

Voor publiceren zijn nog accounts en een echte deployment nodig; deze voorbereiding zet de app niet automatisch online.

## Tests

```bash
python -m unittest test_session_data test_app -v
```

De tests gebruiken uitsluitend synthetische records. Ze controleren sessiescheiding, overlap, opnieuw uploaden, ongeldige bestanden, limieten, filters en wissen.
