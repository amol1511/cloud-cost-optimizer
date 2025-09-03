# Cloud Cost Optimization Tool

A lightweight **Streamlit** app that analyzes multi-cloud cost & usage data (AWS, Azure, GCP or custom)
and generates **rightsizing and waste-reduction recommendations** with estimated savings.

## ✨ Features

- Upload a CSV (or use the provided sample) with costs and utilization metrics.
- Visualize **total spend**, **service breakdown**, and **top costly resources**.
- Detect **idle** and **underutilized** compute resources (e.g., EC2/VMs) with clear thresholds.
- **Rightsizing suggestions** (e.g., m5.large → m5.medium) with estimated monthly savings.
- Tag-aware insights (e.g., costs by `env`, `owner`, `project` if tags are present).
- Exportable recommendations as CSV.

> Works offline on CSVs—no cloud credentials required. You can later hook it to AWS/Azure/GCP SDKs if desired.

## 📦 Project Structure

```
cloud-cost-optimizer/
├── README.md
├── requirements.txt
├── sample_data.csv
├── streamlit_app.py
└── src/
    ├── __init__.py
    ├── rules.py
    ├── loaders.py
    └── analyzer.py
```

## 🧪 Sample Data

`sample_data.csv` includes synthetic entries across AWS, Azure, and GCP with columns:

- `provider` – one of `aws|azure|gcp|other`
- `service` – e.g., `EC2`, `RDS`, `S3`, `VM`, `Compute Engine`
- `resource_id` – unique name or ARN/ID
- `region` – region/zone name
- `tags` – json-like string or `key=value;key=value`
- `month` – ISO month like `2025-08`
- `hours_running` – hours used / provisioned in the month
- `cpu_avg` – average CPU % (0–100)
- `mem_avg` – average memory % (0–100) if available
- `cost_usd` – monthly blended cost in USD
- `last_access_days` – for storage objects (optional), days since last access
- `storage_gb` – for storage services (optional)

You can add your own columns; unknown columns are ignored.

## 🚀 Quickstart

1. **Install deps** (Python 3.9+ recommended):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Upload your CSV** or click **Use sample dataset**.

## 🧠 How recommendations work (high level)

- **Idle compute**: `cpu_avg < 5%` and `hours_running > 100` and `cost_usd > 5` → **Stop/Terminate** suggestion.
- **Underutilized compute**: `5% ≤ cpu_avg < 20%` → **Rightsize down one tier**.
- **Storage**: If `last_access_days > 30` and `storage_gb > 0` → suggest colder tier (e.g., S3 IA / Archive).
- **High-cost outliers**: Top 10% most expensive resources flagged for review.

Savings estimates are conservative:
- Rightsizing: assumes ~35% cost reduction for one-size down.
- Idle stop: assumes 90% savings (retain minimal costs).
- Storage tiering: assumes 40% reduction on flagged storage.

Thresholds are configurable in the sidebar.

## 🔌 Bring your own exports

Export cost & usage from:
- **AWS** Cost Explorer / CUR + CloudWatch metrics
- **Azure** Cost Management + Insights / Metrics
- **GCP** Billing Export + Monitoring metrics

Map your columns to the tool's expected names or rename headers.

## 🧯 Notes & Limitations

- This tool uses heuristics; validate before acting in production.
- Streamlit charts use **matplotlib** to keep dependencies minimal.
- No cloud API calls by default. Safe to run locally/offline.

## 📄 License

MIT
