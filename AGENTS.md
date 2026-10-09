# Afspraken voor deze repository

De gebruiker wil versie 1 online houden terwijl wij versie 2 ontwikkelen.

- Werk standaard op de branch `version-2`.
- `main` hoort bij de bestaande live Streamlit-app. Wijzig of merge niet naar `main` en wijzig de bestaande deployment niet, tenzij de gebruiker expliciet vraagt versie 2 te promoveren of versie 1 te wijzigen.
- Gebruik lokaal poort 8503 voor de v2-preview. De persoonlijke app (8501) en eerdere deelbare preview (8502) zijn andere versies.
- Deze repository bevat uitsluitend deelbare code. Neem geen persoonlijke Spotify-exports, notebooks met luisterdata of lokale databases op.
- Behoud sessiescheiding: bezoekersdata hoort alleen in de eigen Streamlit-sessie, niet in gedeelde caches, bestanden of databases.
- Uitvoerbare checks: `../.venv/bin/python -m unittest test_session_data test_app -v` vanuit deze checkout.
