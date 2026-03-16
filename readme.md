# OEE Dashboard - Industrial Data Portfolio

This repository serves as a technical demonstration of my skills in **Data Engineering, Backend Integration (SQLite), and Frontend Visualization (Streamlit)**. It simulates a real-world Industry 4.0 scenario: monitoring Overall Equipment Effectiveness (OEE) in a dairy production line.

![OEE Dashboard](https://img.shields.io/badge/OEE-Real--time-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)

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
### 1. Main Overview & KPIs
Displaying the core metrics: OEE, Availability, Performance, and Quality.
![Main Dashboard](dash_main.png)

### 2. Interactive Filters
The dashboard allows dynamic analysis by date, production line, and shift.
![Filters Preview](dash_filters1.png)
![Filters Preview](dash_filters2.png)
![Filters Preview](dash_filters3.png)

### 3. Performance & Pareto Analysis
Visualizing downtime causes and efficiency trends over time.
![Analysis Preview](dash_charts1.png) 
![Analysis Preview](dash_charts2.png)
![Analysis Preview](dash_charts3.png)

---

## ⚙️ Project Architecture
This project is structured to showcase clean code and modularity:
* `Data_Prep.py` & `Tables_Prep.py`: ETL (Extract, Transform, Load) logic.
* `Data_Insert.py`: Database management and SQL operations.
* `Dashboard.py`: UI/UX design and data visualization layer.

---
**Note:** This is a portfolio project and is not intended for production use. It aims to showcase technical proficiency in the Python data ecosystem.

**Contact:** www.linkedin.com/in/ricardoserenatojr
**Contact:** ricardoserenato@gmail.com