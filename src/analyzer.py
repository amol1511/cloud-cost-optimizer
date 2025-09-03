import pandas as pd
import numpy as np
from .rules import Thresholds
from .loaders import parse_tags

INSTANCE_DOWNGRADE_MAP = {
    # Very simplified: one step down mapping by family
    'm5.large':'m5.medium',
    'm5.xlarge':'m5.large',
    't3.large':'t3.medium',
    't3.medium':'t3.small',
    'D4s_v5':'D2s_v5',
    'n2-standard-4':'n2-standard-2',
}

def detect_compute_recommendations(df: pd.DataFrame, th: Thresholds) -> pd.DataFrame:
    compute_mask = df['service'].fillna('').str.contains('EC2|VM|Compute Engine', case=False, regex=True)
    cdf = df[compute_mask].copy()
    cdf['util_class'] = np.where(
        (cdf['cpu_avg'] < th.idle_cpu_pct) & (cdf['hours_running'] > th.min_hours_active) & (cdf['cost_usd'] > th.min_cost_consider),
        'idle',
        np.where(
            (cdf['cpu_avg'] >= th.idle_cpu_pct) & (cdf['cpu_avg'] < th.underutil_cpu_pct),
            'underutilized',
            'ok'
        )
    )

    recs = []
    for _, r in cdf.iterrows():
        if r['util_class'] == 'idle':
            est_save = r['cost_usd'] * th.idle_stop_savings_pct
            recs.append({
                'provider': r['provider'],
                'service': r['service'],
                'resource_id': r['resource_id'],
                'region': r.get('region'),
                'month': r['month'],
                'current_cost_usd': r['cost_usd'],
                'recommendation': 'Stop/Terminate if safe',
                'rationale': f'Idle resource: CPU {r.get("cpu_avg", np.nan)}% < {th.idle_cpu_pct}%, hours {r.get("hours_running")}',
                'estimated_monthly_savings_usd': round(est_save,2),
            })
        elif r['util_class'] == 'underutilized':
            # naive rightsizing suggestion based on resource_id pattern
            rid = str(r['resource_id'])
            suggestion = None
            for k,v in INSTANCE_DOWNGRADE_MAP.items():
                if k in rid:
                    suggestion = v
                    break
            suggestion = suggestion or 'Rightsize down one tier'
            est_save = r['cost_usd'] * th.rightsizing_savings_pct
            recs.append({
                'provider': r['provider'],
                'service': r['service'],
                'resource_id': r['resource_id'],
                'region': r.get('region'),
                'month': r['month'],
                'current_cost_usd': r['cost_usd'],
                'recommendation': f'Rightsize → {suggestion}',
                'rationale': f'Underutilized: CPU {r.get("cpu_avg", np.nan)}% < {th.underutil_cpu_pct}%',
                'estimated_monthly_savings_usd': round(est_save,2),
            })
    return pd.DataFrame(recs)

def detect_storage_recommendations(df: pd.DataFrame, th: Thresholds) -> pd.DataFrame:
    storage_mask = df['service'].fillna('').str.contains('S3|Blob|Cloud Storage', case=False, regex=True)
    sdf = df[storage_mask].copy()
    sdf = sdf[(sdf['storage_gb'] > 0) & (sdf['last_access_days'] > th.storage_cold_days)]
    recs = []
    for _, r in sdf.iterrows():
        est_save = r['cost_usd'] * th.storage_savings_pct
        recs.append({
            'provider': r['provider'],
            'service': r['service'],
            'resource_id': r['resource_id'],
            'region': r.get('region'),
            'month': r['month'],
            'current_cost_usd': r['cost_usd'],
            'recommendation': 'Move to colder storage tier',
            'rationale': f'Last accessed {int(r["last_access_days"])} days ago; size ~{int(r["storage_gb"])} GB',
            'estimated_monthly_savings_usd': round(est_save,2),
        })
    return pd.DataFrame(recs)

def summarize_costs(df: pd.DataFrame) -> dict:
    total = df['cost_usd'].sum()
    by_service = df.groupby('service', dropna=False)['cost_usd'].sum().sort_values(ascending=False)
    top_resources = df.sort_values('cost_usd', ascending=False).head(20)
    # tags breakdown if present
    tag_env = []
    if 'tags' in df.columns:
        for _, r in df[['resource_id','cost_usd','tags']].iterrows():
            tags = parse_tags(r['tags'])
            env = tags.get('env','(none)')
            tag_env.append((env, r['cost_usd']))
    tag_df = pd.DataFrame(tag_env, columns=['env','cost_usd'])
    by_env = tag_df.groupby('env')['cost_usd'].sum().sort_values(ascending=False) if not tag_df.empty else None

    return {
        'total_cost': float(round(total,2)),
        'by_service': by_service.reset_index().rename(columns={'cost_usd':'cost_usd_total'}),
        'top_resources': top_resources,
        'by_env': by_env.reset_index().rename(columns={'cost_usd':'cost_usd_total'}) if by_env is not None else None
    }
