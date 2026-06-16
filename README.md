# ⚡ Dashboard Énergétique — Hauts-de-France

Un tableau de bord interactif de Business Intelligence et d'analyse de données énergétiques pour la région Hauts-de-France. Ce projet extrait, traite et visualise en temps réel la consommation et la production d'électricité, avec un focus avancé sur les systèmes de stockage par batterie.

L'application est déployée en ligne et accessible ici : **https://energie-hdf-france-apq4ag4r2cgsyyxdmsbrwc.streamlit.app/**

---

## 🚀 Fonctionnalités Clés

### 📊 Onglet 1 : Vue Globale & Mix Énergétique
* **Sélecteur de Période Dynamique :** Filtrage de l'historique temporel précis (axe X) via un calendrier interactif.
* **KPIs Macro-économiques :** Calcul en temps réel de la consommation totale, de la production totale et du **taux d'autosuffisance global** de la région (indicateur importateur/exportateur).
* **Analyse de la Consommation (Axe Y flexible) :** Visualisation de la puissance brute (MWh), des variations horaires (%) ou d'une moyenne mobile (fenêtre glissante de 2h pour lisser les pics).
* **Mix de Production Répartition Fine :** Rendu visuel interactif (courbes ou aires cumulées) de la production régionale.
* **Indicateurs du Mix de Production :** Répartition chiffrée automatique de la part d'**Énergie Verte (EnR)**, de la part **Nucléaire** et de la part **Fossile (Thermique)** sur la période sélectionnée.

### 🔋 Onglet 2 : Zoom Stockage & Batteries (Flexibilité Réseau)
* **Retraitement Intelligent de la Charge :** Re-qualification physique de la puissance appelée par les batteries (`stockage_batterie`) pour l'isoler de la production et l'additionner à la consommation globale du réseau.
* **Superposition Temporelle des Flux :** Graphique comparatif mettant en opposition les phases de Charge (Consommation la nuit) et de Décharge (Injection le jour).
* **KPI Métier de Performance :** Calcul dynamique du **Rendement de Restitution Restreint** (Round-Trip Efficiency) du parc de stockage de la région sur la fenêtre temporelle choisie.

---

## 🛠️ Stack Technique

* **Framework Front-End :** [Streamlit](https://streamlit.io/) — pour une interface web UI/UX réactive et moderne.
* **Data Processing & Pipeline :** [Polars](https://pola.rs/) — utilisé pour son moteur de calcul ultra-rapide (C++) et ses expressions optimisées (`.is_between()`, `.group_by()`, `.join()`, `.rolling_mean()`).
* **Visualisation :** [Plotly Express](https://plotly.com/python/) — pour les graphiques interactifs (Time-series, Area charts, Donut charts).
* **Base de Données Cloud :** [Supabase](https://supabase.com/) (PostgreSQL) — hébergement distant des données de production et consommation extraites de l'API ODRÉ / Éco2mix de RTE.
* **ORM & Driver BDD :** SQLAlchemy & Psycopg2 — pour des requêtes de lecture sécurisées et performantes vers le Cloud.

# How to run

Setup database with init_db.sql then run :

```
docker build -t energy-pipeline .  
docker run --rm --env-file .env --network=host energy-pipeline 
streamlit run dashboard.py
```

.env structure can be found in .env.exemple