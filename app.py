"""Start met: .venv/bin/python -m streamlit run app.py"""
import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from session_data import SessionLibrary
import uuid

st.set_page_config(page_title="On Repeat v2 · testversie", page_icon="🎧", layout="wide")
st.markdown("""<style>
.block-container {max-width:1500px;padding-top:2.2rem;padding-bottom:3rem}
[data-testid="stSidebar"] {border-right:1px solid #2b322d}
h1,h2,h3 {letter-spacing:-.045em}
h1 {font-size:3.4rem!important;line-height:1.1!important}
[data-testid="stMetric"] {background:#191d1a;border:1px solid #2a342d;border-radius:16px;padding:18px 20px}
[data-testid="stMetricLabel"] {color:#a9b5ad}
[data-testid="stMetricValue"] {font-size:2rem;font-weight:650}
.eyebrow {color:#1ed760;font-size:11px;font-weight:750;letter-spacing:.19em;text-transform:uppercase;margin-bottom:12px}
.hero {padding:28px 32px;border:1px solid #304b38;border-radius:22px;background:linear-gradient(110deg,#193623,#151b17 72%);margin-bottom:22px}
.hero h1 {margin:0;padding:0}.hero p {color:#b8c5bc;margin:12px 0 0;font-size:15px}
.note {color:#97a69b;font-size:13px}
.insight {background:#191d1a;border:1px solid #2a342d;border-radius:16px;padding:20px;min-height:155px}
.insight strong {font-size:22px;display:block;color:#f2f5f2;margin:8px 0;line-height:1.25}
.insight span {color:#a9b5ad;font-size:13px}
[data-testid="stTabs"] button {font-size:15px}
</style>""", unsafe_allow_html=True)

GREEN = "#1ED760"
COLORS = [GREEN, "#86efac", "#59b99f", "#c4da92", "#69a1aa", "#b0c9be"]
def number(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")

def chart(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=0,r=10,t=15,b=5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b8c5bc", family="sans-serif"),
        legend=dict(orientation="h", y=1.12, x=0), hoverlabel=dict(bgcolor="#26372c"))
    fig.update_xaxes(gridcolor="#273029", zeroline=False)
    fig.update_yaxes(gridcolor="#273029", zeroline=False)
    st.plotly_chart(fig, width="stretch", config={"displaylogo":False})

def card(label, value, detail):
    st.markdown(f'<div class="insight"><div class="eyebrow">{html.escape(label)}</div><strong>{html.escape(str(value))}</strong><span>{html.escape(detail)}</span></div>', unsafe_allow_html=True)

# Alle bezoekersdata blijft in de state van deze ene browsersessie.
if "library" not in st.session_state:
    st.session_state.library = SessionLibrary()
if "upload_token" not in st.session_state:
    st.session_state.upload_token = uuid.uuid4().hex
library = st.session_state.library
df = library.dataframe()
history = pd.DataFrame(library.imports)

def reset_session():
    st.session_state.clear()
    st.session_state.upload_token = uuid.uuid4().hex

with st.sidebar:
    st.markdown("### ◉ ON REPEAT")
    st.caption("Jouw muziek. Van dichtbij.")
    st.divider()
    st.markdown("**JE LUISTERFILTERS**")
    if not df.empty:
        first, last = df["date"].min(), df["date"].max()
        years = sorted(df["local_time"].dt.year.unique(), reverse=True)
        period = st.selectbox("Periode", ["Alles", *[str(y) for y in years]], key="period")
        bounds = (first,last) if period == "Alles" else (max(first,pd.Timestamp(f"{period}-01-01").date()), min(last,pd.Timestamp(f"{period}-12-31").date()))
        date_range = st.date_input("Van / tot", value=bounds, min_value=first, max_value=last, format="DD-MM-YYYY", key=f"dates_{period}")
        minimum = st.slider("Minimale afspeeltijd (seconden)", 0, 240, 30, 5,
            help="Standaard tellen starts korter dan 30 seconden niet mee. Dit is een eigen analysefilter, geen officiële Spotify-telling.")
        artist_names = df.groupby("artist")["minutes"].sum().sort_values(ascending=False).index.tolist()
        artists = st.multiselect("Artiesten", artist_names, placeholder="Alle artiesten")
        skip_mode = st.selectbox("Overgeslagen", ["Alles", "Alleen overgeslagen", "Niet overgeslagen"])
        metric = st.radio("Rangschikken op", ["Luistertijd", "Afspeelbeurten"], horizontal=False)
    st.divider()
    st.caption("Alleen jouw uploads in deze sessie. Tijden in Nederland. Geen account nodig.")
    st.caption("Je bestanden worden op de server verwerkt, zonder blijvende opslag door deze app. Bewaar je eigen exports.")
    if library.records or library.imports:
        st.button("Mijn sessie wissen", on_click=reset_session, width="stretch")

st.markdown('<div class="hero"><div class="eyebrow">VERSIE 2 · TESTOMGEVING</div><h1>On Repeat<span style="color:#1ed760">.</span></h1><p>Ontdek de nummers die blijven hangen. En de patronen erachter.</p></div>', unsafe_allow_html=True)

with st.expander("Jouw Spotify-bestanden toevoegen", expanded=df.empty):
    st.write("Upload de JSON-bestanden uit je uitgebreide Spotify-streaminggeschiedenis. Meerdere bestanden worden samengevoegd; exacte duplicaten tellen één keer mee.")
    st.caption("Alleen audio · maximaal 50 MB per bestand, 100 MB en 150.000 muziekrecords per sessie. Pak een ZIP-bestand eerst uit.")
    files = st.file_uploader("Kies je audio-exports", type="json", accept_multiple_files=True,
        max_upload_size=50, key="upload_" + st.session_state.upload_token,
        help="Originele bestandsnamen beginnen met Streaming_History_Audio. Andere exportformaten en videobestanden worden niet ondersteund.")
    if files:
        messages = []
        for uploaded in files:
            try:
                report = library.add(uploaded.name, uploaded.getvalue())
                messages.append((True, f"{uploaded.name}: {number(report['added'])} toegevoegd · {number(report['duplicates'])} duplicaten overgeslagen · {number(report['ignored'])} overige records uitgesloten"))
            except ValueError as exc:
                messages.append((False, f"{uploaded.name}: {exc}"))
        st.session_state.upload_messages = messages
        # Nieuwe uploader laat de oorspronkelijke uploadbuffers los; afgeleide data blijft in de sessie.
        st.session_state.upload_token = uuid.uuid4().hex
        st.rerun()
    for success, message in st.session_state.get("upload_messages", []):
        (st.success if success else st.error)(message)
    st.caption("Elke bezoeker begint met een lege sessie. Je uploads worden niet met andere bezoekers gedeeld. Een nieuwe browsersessie of serverherstart kan je analyse wissen.")

if df.empty:
    st.subheader("Jouw luisterwereld begint hier")
    a,b,c = st.columns(3)
    with a: card("01 · Upload", "Jouw geschiedenis", "Voeg je eigen Spotify-audio-exports toe. Er staan geen gegevens van iemand anders klaar.")
    with b: card("02 · Ontdek", "Wat staat op repeat?", "Bekijk favoriete artiesten, albums en nummers, en je luisterritme door de jaren heen.")
    with c: card("03 · Duik dieper", "Speel met je filters", "Verken periodes, pas de minimale afspeeltijd aan en vergelijk je muzieksmaak.")
    if library.imports:
        st.info("Deze bestanden bevatten geen muziekrecords. Voeg een audio-export met muzieknummers toe.")
    st.stop()

overview, artists_tab, patterns, compare_tab, uploads = st.tabs(["Overzicht", "Artiesten & tracks", "Luisterritme", "Vergelijken", "Mijn sessie"])
with uploads:
    st.subheader("Jouw tijdelijke bibliotheek")
    a,b,c = st.columns(3)
    a.metric("Muziekrecords in sessie", number(len(df)))
    b.metric("Unieke audio-imports", number(len(history)))
    c.metric("Opslag", "Deze sessie")
    st.caption("Deze totalen gelden voor al je uploads in deze sessie, onafhankelijk van je filters.")
    if not history.empty:
        view = history.rename(columns={"filename":"Bestand","imported_at":"Geïmporteerd","total":"Records","added":"Toegevoegd","duplicates":"Duplicaten","ignored":"Geen muziek"})
        view["Geïmporteerd"] = pd.to_datetime(view["Geïmporteerd"],utc=True).dt.tz_convert("Europe/Amsterdam").dt.strftime("%d-%m-%Y %H:%M")
        st.dataframe(view, hide_index=True, width="stretch")
    with st.expander("Over je gegevens en de berekeningen"):
        st.markdown("""- Je uploads worden verwerkt op de server en gekoppeld aan jouw browsersessie. De app maakt geen bestanden of database met je luistergeschiedenis en gebruikt geen gedeelde datacache.
- Je kunt de sessie wissen met de knop links. Bij een nieuwe sessie of serverherstart moet je opnieuw uploaden. Sluiten van een tabblad betekent niet gegarandeerd onmiddellijke verwijdering uit het servergeheugen.
- IP-adressen uit je export worden niet opgenomen in de analysetabel. De hash voor exacte duplicaten wordt berekend over alle originele velden.
- Afspeelbeurten zijn registraties die door je filters komen; dit zijn niet noodzakelijk volledig afgespeelde nummers. Standaard geldt een minimum van 30 seconden.
- Podcasts, luisterboeken en video-exports worden uitgesloten. Lege periodes kunnen ontbreken in je export.
- Unieke nummers gebruiken de Spotify-track-ID; zonder ID gebruiken we artiest en titel.""")

if len(date_range) != 2:
    with overview:
        st.info("Kies ook een einddatum om je selectie te bekijken.")
    st.stop()
start, end = date_range
filtered = df[(df["date"] >= start) & (df["date"] <= end) & (df["ms_played"] >= minimum * 1000)].copy()
if artists:
    filtered = filtered[filtered["artist"].isin(artists)]
if skip_mode == "Alleen overgeslagen":
    filtered = filtered[filtered["skipped"].eq(True).fillna(False)]
elif skip_mode == "Niet overgeslagen":
    filtered = filtered[filtered["skipped"].eq(False).fillna(False)]
if filtered.empty:
    with overview:
        st.info("Geen muziek binnen deze filters. Vergroot je periode of verlaag de minimale afspeeltijd.")
    st.stop()

measure = "hours" if metric == "Luistertijd" else "plays"
measure_label = "Luisteruren" if measure == "hours" else "Afspeelbeurten"
def rankings(data, keys):
    grouped = data.groupby(keys, dropna=False).agg(hours=("minutes",lambda s:s.sum()/60), plays=("record_hash","size")).reset_index()
    return grouped.sort_values(measure, ascending=False)

ranked_artists = rankings(filtered,["artist"])
ranked_tracks = rankings(filtered,["track_key","track","artist"])

with overview:
    st.caption(f"{start:%d-%m-%Y} — {end:%d-%m-%Y} · minimaal {minimum} seconden · {len(artists) if artists else 'alle'} artiesten")
    cols = st.columns(4)
    cols[0].metric("Luisteruren", number(filtered["minutes"].sum()/60,1))
    cols[1].metric("Afspeelbeurten", number(len(filtered)))
    cols[2].metric("Unieke nummers", number(filtered["track_key"].nunique()))
    cols[3].metric("Verschillende artiesten", number(filtered["artist"].nunique()))
    st.markdown("### De soundtrack van je tijd")
    granularity = st.segmented_control("Groeperen per", ["Dag", "Week", "Maand"], default="Maand") or "Maand"
    freq = {"Dag":"D","Week":"W-MON","Maand":"MS"}[granularity]
    time_data = filtered.set_index("local_time").resample(freq, label="left", closed="left").agg(hours=("minutes", lambda s:s.sum()/60), plays=("record_hash","size")).reset_index()
    fig = px.area(time_data,x="local_time",y=measure,color_discrete_sequence=[GREEN],labels={"local_time":"",measure:measure_label})
    fig.update_traces(line=dict(width=2),fillcolor="rgba(30,215,96,.12)",hovertemplate="%{x|%d %b %Y}<br>%{y:,.1f}<extra></extra>")
    chart(fig,300)
    left,right = st.columns([1.3,1], gap="large")
    with left:
        st.markdown("### Jouw vaste favorieten")
        top = ranked_artists.head(8).sort_values(measure)
        fig=px.bar(top,x=measure,y="artist",orientation="h",color_discrete_sequence=[GREEN],labels={measure:measure_label,"artist":""})
        fig.update_traces(marker_cornerradius=5)
        chart(fig,340)
    with right:
        st.markdown("### Op repeat")
        for i,row in ranked_tracks.head(5).reset_index(drop=True).iterrows():
            value = f"{number(row['hours'],1)} uur" if measure == "hours" else f"{number(row['plays'])} keer"
            st.markdown(f'<div style="display:flex;gap:16px;padding:13px 0;border-bottom:1px solid #29312b"><span style="color:#1ed760;font-size:19px">{i+1:02}</span><div style="flex:1"><b>{html.escape(row["track"])}</b><div class="note">{html.escape(row["artist"])}</div></div><span class="note" style="white-space:nowrap">{value}</span></div>',unsafe_allow_html=True)
    st.markdown("### Een paar dingen die opvallen")
    a,b,c=st.columns(3)
    favorite=ranked_artists.iloc[0]
    share=100*favorite[measure]/ranked_artists[measure].sum() if ranked_artists[measure].sum() else 0
    daily=filtered.groupby("date")["minutes"].sum()
    with a: card("Jouw nummer één",favorite["artist"],f"{number(share,1)}% van je geselecteerde {'luistertijd' if measure=='hours' else 'afspeelbeurten'}")
    with b: card("Drukste luisterdag",daily.idxmax().strftime("%d-%m-%Y"),f"{number(daily.max()/60,1)} geregistreerde luisteruren")
    with c: card("Dagen met muziek",number(len(daily)),f"Gemiddeld {number(daily.mean(),0)} minuten per dag met registraties")

with artists_tab:
    st.subheader("Duik in je favorieten")
    category=st.segmented_control("Toplijsten",["Artiesten","Albums","Nummers"],default="Artiesten") or "Artiesten"
    amount=st.slider("Lengte van je toplijst",5,50,15,5)
    keys={"Artiesten":["artist"],"Albums":["album","artist"],"Nummers":["track_key","track","artist"]}[category]
    table=rankings(filtered,keys).head(amount)
    if category == "Artiesten": table["label"]=table["artist"]
    else:
        title="album" if category=="Albums" else "track"
        table["label"]=table[title]+" · "+table["artist"]
    fig=px.bar(table.sort_values(measure),x=measure,y="label",orientation="h",color_discrete_sequence=[GREEN],labels={measure:measure_label,"label":""})
    chart(fig,max(350,amount*27))
    display=table.drop(columns=["label","track_key"],errors="ignore").rename(columns={"artist":"Artiest","album":"Album","track":"Nummer","hours":"Luisteruren","plays":"Afspeelbeurten"})
    st.dataframe(display,hide_index=True,width="stretch",column_config={"Luisteruren":st.column_config.NumberColumn(format="%.1f")})
    st.download_button("Download deze toplijst (CSV)",display.to_csv(index=False).encode("utf-8-sig"),"spotify_toplijst.csv","text/csv")
    st.markdown("### Eén artiest door de tijd")
    artist=st.selectbox("Kies een artiest voor de detailgrafiek",ranked_artists["artist"].tolist())
    artist_data=filtered[filtered["artist"]==artist]
    monthly=artist_data.set_index("local_time").resample("MS").agg(hours=("minutes",lambda s:s.sum()/60),plays=("record_hash","size")).reset_index()
    chart(px.bar(monthly,x="local_time",y=measure,color_discrete_sequence=[GREEN],labels={"local_time":"",measure:measure_label}),260)

with patterns:
    st.subheader("Wanneer gaat jouw muziek aan?")
    st.caption("Registraties zijn ingedeeld op het tijdstip in de export, omgerekend naar Nederland. Een lange afspeelbeurt wordt niet over meerdere uren verdeeld.")
    rhythm=filtered.assign(weekday=filtered["local_time"].dt.weekday,hour=filtered["local_time"].dt.hour)
    rhythm["value"] = rhythm["minutes"]/60 if measure=="hours" else 1
    grid=rhythm.pivot_table(index="weekday",columns="hour",values="value",aggfunc="sum",fill_value=0).reindex(index=range(7),columns=range(24),fill_value=0)
    days=["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]
    fig=go.Figure(go.Heatmap(z=grid.values,x=list(range(24)),y=days,colorscale=[[0,"#19241c"],[.3,"#246238"],[1,GREEN]],colorbar=dict(title=measure_label),hovertemplate="%{y} · %{x}:00<br>%{z:.1f}<extra></extra>",xgap=3,ygap=4))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickmode="linear",dtick=2,title="Uur van de dag")
    chart(fig,360)
    left,right=st.columns(2,gap="large")
    with left:
        st.markdown("### Je week in muziek")
        week=rhythm.groupby("weekday")["value"].sum().reindex(range(7),fill_value=0)
        chart(px.bar(x=[d[:2] for d in days],y=week.values,color_discrete_sequence=[GREEN],labels={"x":"","y":measure_label}),280)
    with right:
        st.markdown("### Waar luister je?")
        platforms=rankings(filtered,["platform"]).head(8)
        chart(px.pie(platforms,names="platform",values=measure,hole=.65,color_discrete_sequence=COLORS),280)
    skipped_known=filtered["skipped"].notna()
    known_count=int(skipped_known.sum())
    skip_percentage=filtered.loc[skipped_known,"skipped"].astype(bool).mean()*100 if known_count else None
    st.caption(f"Overgeslagen: {number(skip_percentage,1)+'%' if skip_percentage is not None else 'onbekend'} van {number(known_count)} records met bekende skipstatus, binnen je huidige filters. Het minimum van {minimum} seconden beïnvloedt dit percentage.")

with compare_tab:
    st.subheader("Hoe veranderde jouw muzieksmaak?")
    st.caption("Vergelijk kalenderjaren. Artiest-, skip- en afspeeltijdfilters blijven actief; de datumselectie links geldt hier niet. Onvolledige jaren zijn niet rechtstreeks vergelijkbaar.")
    if len(years)<2:
        st.info("Voeg audio uit een tweede jaar toe om te vergelijken.")
    else:
        a,b=st.columns(2)
        coverage = df.groupby(df["local_time"].dt.year)["date"].nunique()
        substantial = [year for year in years if coverage[year] >= 30]
        defaults = substantial[:2] if len(substantial) >= 2 else years[:2]
        year_a=a.selectbox("Periode A",years,index=years.index(defaults[1]))
        year_b=b.selectbox("Periode B",years,index=years.index(defaults[0]))
        compare=df[df["ms_played"]>=minimum*1000].copy()
        if artists: compare=compare[compare["artist"].isin(artists)]
        if skip_mode!="Alles": compare=compare[compare["skipped"].eq(skip_mode=="Alleen overgeslagen").fillna(False)]
        compare["year"]=compare["local_time"].dt.year
        for col,year in [(a,year_a),(b,year_b)]:
            subset=compare[compare["year"]==year]
            with col:
                st.metric(f"Luisteruren in {year}",number(subset["minutes"].sum()/60,1))
                st.caption(f"{number(len(subset))} afspeelbeurten · {number(subset['artist'].nunique())} artiesten · {number(subset['date'].nunique())} dagen met registraties")
        if year_a==year_b:
            st.info("Kies twee verschillende jaren voor de vergelijking.")
        else:
            compare=compare[compare["year"].isin([year_a,year_b])]
            if compare.empty:
                st.info("Geen registraties in deze jaren met je huidige filters.")
            else:
                chosen=rankings(compare,["artist"]).head(10)["artist"]
                grouped=rankings(compare[compare["artist"].isin(chosen)],["artist","year"])
                complete=pd.MultiIndex.from_product([chosen,[year_a,year_b]],names=["artist","year"])
                grouped=grouped.set_index(["artist","year"]).reindex(complete,fill_value=0).reset_index()
                grouped["year"]=grouped["year"].astype(str)
                chart(px.bar(grouped,x=measure,y="artist",color="year",orientation="h",barmode="group",color_discrete_sequence=["#1ed760","#789886"],labels={measure:measure_label,"artist":"","year":"Jaar"}),500)
                st.caption("Top 10 artiesten over beide gekozen jaren samen. Ontbrekende registraties tellen als 0, maar bewijzen niet dat je toen niet luisterde.")

st.divider()
st.caption("ON REPEAT · Gebouwd met jouw Spotify-export · Geen verbinding met je Spotify-account")
