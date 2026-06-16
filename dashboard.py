# ruff: noqa: E501
import datetime
import os

import plotly.express as px
import polars as pl
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

st.set_page_config(page_title="Dashboard Énergie Hauts-de-France", page_icon="⚡", layout="wide")

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('SUPABASE_USER')}:{os.getenv('SUPABASE_PWD')}@{os.getenv('SUPABASE_HOST')}:{os.getenv('SUPABASE_PORT')}/{os.getenv('SUPABASE_DB')}"


@st.cache_data(ttl=3600)
def load_data_from_supabase():
    if not os.getenv("SUPABASE_HOST"):
        st.warning("Variables d'environnement introuvables. Affichage de données de secours.")
        return get_mock_data()

    engine = create_engine(DATABASE_URL)

    query_cons = (
        "SELECT datetime, consumption_mwh FROM hdf_consumption ORDER BY datetime DESC LIMIT 8640;"
    )
    query_prod = (
        "SELECT datetime, production_source, production_mwh "
        "FROM hdf_production ORDER BY datetime DESC LIMIT 45000;"
    )

    df_cons = pl.read_database(query=query_cons, connection=engine)
    df_prod = pl.read_database(query=query_prod, connection=engine)

    df_cons = df_cons.with_columns(pl.col("datetime").cast(pl.Datetime))
    df_prod = df_prod.with_columns(pl.col("datetime").cast(pl.Datetime))

    df_prod = df_prod.with_columns(pl.col("production_source").str.to_lowercase())

    df_stockage_brut = df_prod.filter(
        pl.col("production_source") == "stockage_batterie"
    ).with_columns(pl.col("production_mwh").abs())

    if df_stockage_brut.height > 0:
        df_stockage = df_stockage_brut.select(
            ["datetime", pl.col("production_mwh").alias("stockage_mwh")]
        )
        df_cons = df_cons.join(df_stockage, on="datetime", how="left")
        df_cons = (
            df_cons.with_columns(pl.col("stockage_mwh").fill_null(0))
            .with_columns(
                (pl.col("consumption_mwh") + pl.col("stockage_mwh")).alias("consumption_mwh")
            )
            .drop("stockage_mwh")
        )

    df_prod = df_prod.filter(pl.col("production_source") != "stockage_batterie").with_columns(
        pl.when(pl.col("production_source") == "destockage_batterie")
        .then(pl.lit("batterie (décharge)"))
        .otherwise(pl.col("production_source"))
        .alias("production_source")
    )

    df_cons = df_cons.sort("datetime")
    df_prod = df_prod.sort("datetime")

    return df_cons, df_prod, df_stockage_brut


def get_mock_data():
    today = datetime.datetime.now()
    dates = [today - datetime.timedelta(minutes=15 * i) for i in range(96 * 14)]
    dates.reverse()

    df_cons = pl.DataFrame(
        {"datetime": dates, "consumption_mwh": [5000 + (i % 50) * 30 for i in range(96 * 14)]}
    )

    sources = [
        "nucleaire",
        "eolien",
        "solaire",
        "thermique",
        "stockage_batterie",
        "destockage_batterie",
    ]
    prod_data = []
    for i, d in enumerate(dates):
        for s in sources:
            if s == "nucleaire":
                base_prod = 4500
            elif s == "stockage_batterie":
                base_prod = 150 if (i % 24) in range(1, 5) else 0
            elif s == "destockage_batterie":
                base_prod = 120 if (i % 24) in range(12, 16) else 0
            else:
                base_prod = 400
            prod_data.append(
                {"datetime": d, "production_source": s, "production_mwh": base_prod + (i % 10) * 5}
            )

    df_prod = pl.DataFrame(prod_data)

    df_stockage_brut = df_prod.filter(pl.col("production_source") == "stockage_batterie")
    df_prod_clean = df_prod.filter(pl.col("production_source") != "stockage_batterie").with_columns(
        pl.when(pl.col("production_source") == "destockage_batterie")
        .then(pl.lit("batterie (décharge)"))
        .otherwise(pl.col("production_source"))
        .alias("production_source")
    )

    return (
        df_cons.sort("datetime"),
        df_prod_clean.sort("datetime"),
        df_stockage_brut.sort("datetime"),
    )


try:
    df_cons, df_prod, df_stockage_brut = load_data_from_supabase()
except Exception as e:
    st.error(f"Erreur Supabase : {e}")
    df_cons, df_prod, df_stockage_brut = get_mock_data()

st.sidebar.header("📅 Période d'analyse")
min_date = df_cons["datetime"].min().date()
max_date = df_cons["datetime"].max().date()
default_start_date = max_date - datetime.timedelta(days=7)  # 1 semaine par défaut

date_range = st.sidebar.date_input(
    label="Sélectionnez une plage de dates :",
    value=(default_start_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

    df_cons_filtered = df_cons.filter(pl.col("datetime").is_between(start_datetime, end_datetime))
    df_prod_filtered = df_prod.filter(pl.col("datetime").is_between(start_datetime, end_datetime))
    df_stock_filtered = df_stockage_brut.filter(
        pl.col("datetime").is_between(start_datetime, end_datetime)
    )

    st.title("⚡ Dashboard Énergétique — Hauts-de-France")
    st.markdown(
        f"Analyse du **{start_date.strftime('%d/%m/%Y')}** au **{end_date.strftime('%d/%m/%Y')}**"
    )
    # Nouvelle petite description textuelle
    st.markdown(
        """
        Bienvenue sur cet outil de Business Intelligence dédié au suivi énergétique de la région **Hauts-de-France**.
        Ce dashboard interroge en continu une base de données Cloud alimentée par les flux temps réel de l'API Éco2mix de RTE disponibles sur l'ODRE (https://opendata.reseaux-energies.fr/).

        * **Onglet 1 (Vue Globale) :** Explorez la consommation régionale, analysez l'indépendance de la région grâce au taux d'autosuffisance et décortiquez la nature du mix électrique (Vert vs Nucléaire vs Fossile).
        * **Onglet 2 (Zoom Stockage) :** Analysez comment les parcs de batteries locaux stabilisent le réseau en absorbant l'énergie excédentaire (Charge) pour la restituer lors des pics de demande (Décharge).
        """
    )
    st.divider()

    tab_global, tab_battery = st.tabs(["📊 Vue Globale & Mix", "🔋 Zoom Stockage & Batteries"])

    with tab_global:
        if df_cons_filtered.height > 0 and df_prod_filtered.height > 0:
            total_cons_mwh = df_cons_filtered["consumption_mwh"].sum() / 4
            total_prod_mwh = df_prod_filtered["production_mwh"].sum() / 4
            autosuffisance_globale = (total_prod_mwh / total_cons_mwh) * 100

            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric(
                    label="⚡ Consommation Totale (Période)",
                    value=f"{int(total_cons_mwh):,} MWh".replace(",", " "),
                )
            with kpi2:
                st.metric(
                    label="🏭 Production Totale (Période)",
                    value=f"{int(total_prod_mwh):,} MWh".replace(",", " "),
                )
            with kpi3:
                help_msg = (
                    "La région produit plus qu'elle ne consomme (Exportatrice)"
                    if autosuffisance_globale >= 100
                    else "La région dépend des importations pour couvrir ses besoins."
                )
                st.metric(
                    label="🔋 Taux d'Autosuffisance Global",
                    value=f"{autosuffisance_globale:.1f} %",
                    delta=f"{autosuffisance_globale - 100:.1f} % vs Équilibre",
                    help=help_msg,
                )

            st.divider()

        st.subheader("🌱 Nature du Mix de Production")

        df_filières_volumes = df_prod_filtered.group_by("production_source").agg(
            (pl.col("production_mwh").sum() / 4).alias("volume")
        )

        vol_nucleaire = df_filières_volumes.filter(pl.col("production_source") == "nucleaire")[
            "volume"
        ].sum()
        vol_thermique = df_filières_volumes.filter(pl.col("production_source") == "thermique")[
            "volume"
        ].sum()

        vol_enr = df_filières_volumes.filter(
            ~pl.col("production_source").is_in(["nucleaire", "thermique", "batterie (décharge)"])
        )["volume"].sum()

        part_enr = (vol_enr / total_prod_mwh) * 100 if total_prod_mwh > 0 else 0
        part_nucleaire = (vol_nucleaire / total_prod_mwh) * 100 if total_prod_mwh > 0 else 0
        part_fossile = (vol_thermique / total_prod_mwh) * 100 if total_prod_mwh > 0 else 0

        kpi_mix1, kpi_mix2, kpi_mix3 = st.columns(3)
        with kpi_mix1:
            st.metric(
                label="🌿 Part Énergie Verte",
                value=f"{part_enr:.1f} %",
                help=f"Soit {int(vol_enr):,} MWh",
            )
        with kpi_mix2:
            st.metric(
                label="⚛️ Part Nucléaire",
                value=f"{part_nucleaire:.1f} %",
                help=f"Soit {int(vol_nucleaire):,} MWh",
            )
        with kpi_mix3:
            st.metric(
                label="🔥 Part Fossile (Thermique)",
                value=f"{part_fossile:.1f} %",
                help=f"Soit {int(vol_thermique):,} MWh",
            )

        st.divider()

        col_gauche, col_droite = st.columns(2)

        with col_gauche:
            st.subheader("📈 Analyse de la Consommation")
            metric_choice = st.selectbox(
                label="Visualisation de la consommation (Axe Y) :",
                options=[
                    "Puissance brute (MWh)",
                    "Variation horaire (%)",
                    "Moyenne mobile (Fenêtre de 2h)",
                ],
                index=0,
            )

            if metric_choice == "Puissance brute (MWh)":
                df_cons_chart = df_cons_filtered.with_columns(
                    pl.col("consumption_mwh").alias("y_axis")
                )
                y_label = "Puissance (MWh)"
            elif metric_choice == "Variation horaire (%)":
                df_cons_chart = df_cons_filtered.with_columns(
                    (
                        (
                            (pl.col("consumption_mwh") - pl.col("consumption_mwh").shift(1))
                            / pl.col("consumption_mwh").shift(1)
                        )
                        * 100
                    ).alias("y_axis")
                )
                y_label = "Variation (%)"
            else:
                df_cons_chart = df_cons_filtered.with_columns(
                    pl.col("consumption_mwh").rolling_mean(window_size=8).alias("y_axis")
                )
                y_label = "Moyenne Mobile 2h (MWh)"

            fig_cons = px.line(
                df_cons_chart.to_pandas(),
                x="datetime",
                y="y_axis",
                labels={"datetime": "Date / Heure", "y_axis": y_label},
                color_discrete_sequence=["#FF4B4B"],
            )
            st.plotly_chart(fig_cons, use_container_width=True)

        with col_droite:
            st.subheader("🏭 Analyse de la Production")
            prod_view_mode = st.radio(
                label="Affichage de la puissance (Axe Y) :",
                options=["Production Régionale Totale", "Détail par source d'énergie"],
                index=0,
                horizontal=True,
            )

            if prod_view_mode == "Production Régionale Totale":
                df_prod_total = (
                    df_prod_filtered.group_by("datetime")
                    .agg(pl.col("production_mwh").sum().alias("total_production_mwh"))
                    .sort("datetime")
                )

                fig_prod = px.line(
                    df_prod_total.to_pandas(),
                    x="datetime",
                    y="total_production_mwh",
                    labels={
                        "datetime": "Date / Heure",
                        "total_production_mwh": "Production Totale (MWh)",
                    },
                    color_discrete_sequence=["#2BD9A5"],
                )
            else:
                available_sources = list(df_prod_filtered["production_source"].unique())
                selected_sources = st.multiselect(
                    label="Sélectionnez les sources à inclure :",
                    options=available_sources,
                    default=available_sources,
                )
                df_prod_chart = df_prod_filtered.filter(
                    pl.col("production_source").is_in(selected_sources)
                )
                chart_type = st.checkbox("Afficher sous forme d'aires cumulées", value=True)

                if chart_type:
                    fig_prod = px.area(
                        df_prod_chart.to_pandas(),
                        x="datetime",
                        y="production_mwh",
                        color="production_source",
                        labels={
                            "datetime": "Date / Heure",
                            "production_mwh": "Puissance (MWh)",
                            "production_source": "Filière",
                        },
                        color_discrete_sequence=px.colors.qualitative.Safe,
                    )
                else:
                    fig_prod = px.line(
                        df_prod_chart.to_pandas(),
                        x="datetime",
                        y="production_mwh",
                        color="production_source",
                        labels={
                            "datetime": "Date / Heure",
                            "production_mwh": "Puissance (MWh)",
                            "production_source": "Filière",
                        },
                        color_discrete_sequence=px.colors.qualitative.Safe,
                    )
            st.plotly_chart(fig_prod, use_container_width=True)

    with tab_battery:
        st.subheader("🔋 Analyse de la Flexibilité Réseau (Systèmes de Batteries)")
        st.markdown(
            "Cet espace permet d'analyser le comportement des "
            "actifs de stockage de la région (Périodes de charge vs décharge)."
        )

        df_batt_charge = df_stock_filtered.select(
            ["datetime", pl.col("production_mwh").alias("Charge (Stockage réseau)")]
        )
        df_batt_decharge = df_prod_filtered.filter(
            pl.col("production_source") == "batterie (décharge)"
        ).select(["datetime", pl.col("production_mwh").alias("Décharge (Injection réseau)")])

        df_battery_analytique = df_batt_charge.join(
            df_batt_decharge, on="datetime", how="full"
        ).sort("datetime")

        if df_battery_analytique.height == 0:
            st.info("Aucune donnée de batterie enregistrée sur cette période.")
        else:
            total_charge_mwh = df_battery_analytique["Charge (Stockage réseau)"].sum() / 4
            total_decharge_mwh = df_battery_analytique["Décharge (Injection réseau)"].sum() / 4

            rendement = (total_decharge_mwh / total_charge_mwh * 100) if total_charge_mwh > 0 else 0

            bat_kpi1, bat_kpi2, bat_kpi3 = st.columns(3)
            with bat_kpi1:
                st.metric(
                    label="📥 Énergie totale stockée (Charge)", value=f"{total_charge_mwh:.1f} MWh"
                )
            with bat_kpi2:
                st.metric(
                    label="📤 Énergie totale restituée (Décharge)",
                    value=f"{total_decharge_mwh:.1f} MWh",
                )
            with bat_kpi3:
                st.metric(
                    label="🔄 Rendement de Restitution Restreint",
                    value=f"{rendement:.1f} %" if rendement <= 100 else "N/A",
                    help="Rapport entre l'énergie restituée et "
                    "stockée sur la période sélectionnée.",
                )

            st.divider()

            st.subheader("⏱️ Chronologie des mouvements de charge/décharge")

            df_plotly_bat = df_battery_analytique.to_pandas()
            df_plotly_bat["Charge (Stockage réseau)"] = (
                df_plotly_bat["Charge (Stockage réseau)"] * -1
            )

            df_plotly_bat = df_plotly_bat.melt(
                id_vars=["datetime"],
                value_vars=["Charge (Stockage réseau)", "Décharge (Injection réseau)"],
                var_name="Flux de la Batterie",
                value_name="Puissance (MWh)",
            )

            fig_bat_flux = px.line(
                df_plotly_bat,
                x="datetime",
                y="Puissance (MWh)",
                color="Flux de la Batterie",
                labels={"datetime": "Date / Heure"},
                color_discrete_map={
                    "Charge (Stockage réseau)": "#FF9F43",
                    "Décharge (Injection réseau)": "#10AC84",
                },
            )
            st.plotly_chart(fig_bat_flux, use_container_width=True)

            st.info(
                "💡 **Analyse Data** : Observez les pics d'injection (Décharge) : "
                "ils coïncident généralement avec les pointes de consommation régionales "
                "ou les baisses de production des énergies renouvelables intermittentes."
            )

else:
    st.info(
        "Veuillez sélectionner une date de fin dans le calendrier (Barre latérale)"
        " pour afficher les graphiques."
    )
