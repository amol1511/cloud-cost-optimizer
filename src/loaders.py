import pandas as pd

def parse_tags(tags):
    if pd.isna(tags):
        return {}
    if isinstance(tags, dict):
        return tags
    d = {}
    # allow key=value;key=value or JSON-like
    try:
        if isinstance(tags, str) and tags.strip().startswith('{'):
            import json
            return json.loads(tags)
    except Exception:
        pass
    if isinstance(tags, str):
        parts = [p.strip() for p in tags.split(';') if p.strip()]
        for p in parts:
            if '=' in p:
                k,v = p.split('=',1)
                d[k.strip()] = v.strip()
    return d

EXPECTED_COLS = [
    'provider','service','resource_id','region','tags','month',
    'hours_running','cpu_avg','mem_avg','cost_usd','last_access_days','storage_gb'
]

def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize expected columns if present in different cases
    lc_map = {c.lower(): c for c in df.columns}
    for col in EXPECTED_COLS:
        if col not in df.columns and col in lc_map:
            df[col] = df[lc_map[col]]
    # Ensure minimal required columns exist
    required = ['provider','service','resource_id','month','cost_usd']
    for r in required:
        if r not in df.columns:
            df[r] = None
    # Fill optional columns if missing
    for c in EXPECTED_COLS:
        if c not in df.columns:
            df[c] = None

    # Coerce types
    for c in ['hours_running','cpu_avg','mem_avg','cost_usd','last_access_days','storage_gb']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df
