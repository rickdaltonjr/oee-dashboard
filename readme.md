# OEE Dashboard - Industrial Data Portfolio

<p align="center">
  This repository serves as a technical demonstration of my skills in <b>Data Engineering, Backend Integration (SQLite), and Frontend Visualization (Streamlit)</b>. It simulates a real-world Industry 4.0 scenario: monitoring Overall Equipment Effectiveness (OEE) in a dairy production line.
</p>

<p align="center">
  <a href="https://oee-dashboard-s4qt4tsczhlwshysv779qe.streamlit.app/">
    <img src="https://img.shields.io/badge/🚀_View_Live_Dashboard-Click_Here-blue?style=for-the-badge" alt="Live Demo">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OEE-Real--time-blue" alt="OEE">
  <img src="https://img.shields.io/badge/Python-3.9+-green" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.28+-red" alt="Streamlit">
</p>

---

## 🎯 Project Objective
The goal of this project is to demonstrate a full-cycle data solution:
1. **Data Ingestion**: Handling raw production data.
2. **Data Transformation**: Processing and cleaning data using Python/Pandas.
3. **Storage**: Structuring and querying a local SQLite database.
4. **Insight Delivery**: Building an interactive dashboard for decision-making.

## 🛠️ Tech Stack & Skills Demonstrated
* **Python**: Core logic, data manipulation, and automation.
* **Pandas & NumPy**: Complex data cleaning and KPI calculations (OEE formulas).
* **SQLite**: Database schema design and SQL integration.
* **Streamlit**: Rapid development of a web-based UI for data apps.
* **Plotly**: Creating interactive charts (Pareto, Time-Series, Gauges).

## 📊 Key Insights Provided
* **Real-time KPI Tracking**: Instant visibility of OEE, Availability, Performance, and Quality.
* **Downtime Analysis**: Automatic Pareto charts to identify the main causes of efficiency loss.
* **Production Comparison**: Dynamic filters to compare performance across different shifts and production lines.

## 🖼️ Dashboard Preview

### Live Demo Preview
<p align="center">
  <img src="screenshots/dash.gif" width="850" alt="Main Dashboard GIF">
</p>

### 1. Interactive Filters
<div align="center">

| Filter View 1 | Filter View 2 | Filter View 3 |
| :---: | :---: | :---: |
| ![Filters 1](screenshots/dash_filters1.png) | ![Filters 2](screenshots/dash_filters2.png) | ![Filters 3](screenshots/dash_filters3.png) |

</div>

### 2. Performance & Pareto Analysis
<div align="center">

| Pareto Analysis | Time Series | Quality Metrics |
| :---: | :---: | :---: |
| ![Charts 1](screenshots/dash_chart1.png) | ![Charts 2](screenshots/dash_chart2.png) | ![Charts 3](screenshots/dash_chart3.png) |

</div>

---

## ⚙️ Project Architecture
This project is structured to showcase clean code and modularity:
* `Data_Prep.py` & `Tables_Prep.py`: ETL (Extract, Transform, Load) logic.
* `Data_Insert.py`: Database management and SQL operations.
* `Dashboard.py`: UI/UX design and data visualization layer.

---
**Note:** This is a portfolio project and is not intended for production use. It aims to showcase technical proficiency in the Python data ecosystem.

**Contact:** [Ricardo Serenato Junior](https://www.linkedin.com/in/ricardoserenatojr)  
**Email:** [ricardoserenato@gmail.com](mailto:ricardoserenato@gmail.com)