import pandas as pd
import numpy as np

csv_path = r'c:\Users\haiju\OneDrive\Documents\antigravity\parallel_guided_beam\comparison\preset_data\PARALLOGRAM_ALL_MODELS_master.csv'
df = pd.read_csv(csv_path)

cases = [
    {'name': 'Case 1', 'Ax': 0, 'B': 0},
    {'name': 'Case 2', 'Ax': -5, 'B': 0},
    {'name': 'Case 3', 'Ax': 0, 'B': 3},
]

ranges = [
    {'name': 'R1', 'min': 0.1, 'max': 4.9}, # |Ay| < 5
    {'name': 'R2', 'min': 5.0, 'max': 20.0}, # |Ay| in [5, 20]
]

models = [
    {'id': 'L1', 'prefix': 'linear'},
    {'id': 'L2', 'prefix': 'bcm'},
    {'id': 'L3', 'prefix': 'guided'},
    {'id': 'L4', 'prefix': 'euler'},
    {'id': 'L5', 'prefix': 'prb'},
    {'id': 'L6', 'prefix': 'prb_opt'},
    {'id': 'L7', 'prefix': 'fea2d'},
]

metrics = ['ux', 'uy', 'phi']

results = []

for case in cases:
    case_df = df[(df['Ax'] == case['Ax']) & (df['B'] == case['B'])]
    
    for r in ranges:
        range_df = case_df[(case_df['Ay'].abs() >= r['min']) & (case_df['Ay'].abs() <= r['max'])]
        
        row_res = {'Case': case['name'], 'Range': r['name']}
        
        for model in models:
            for metric in metrics:
                ref_col = f'{metric}_fea3d'
                val_col = f'{metric}_{model["prefix"]}'
                
                # Filter out non-finite and zero references
                valid_mask = range_df[ref_col].notna() & range_df[val_col].notna() & (range_df[ref_col] != 0)
                valid_data = range_df[valid_mask]
                
                if not valid_data.empty:
                    mape = (np.abs((valid_data[val_col] - valid_data[ref_col]) / valid_data[ref_col]) * 100).mean()
                    row_res[f'{model["id"]}_{metric}'] = mape
                else:
                    row_res[f'{model["id"]}_{metric}'] = np.nan
        
        results.append(row_res)

# Convert to a format easy to copy/paste into LaTeX
res_df = pd.DataFrame(results)

with open(r'c:\Users\haiju\OneDrive\Documents\antigravity\parallel_guided_beam\results_mape.txt', 'w') as f:
    f.write(res_df.to_string())
    f.write("\n\nLaTeX lines:\n")
    # Also print in a LaTeX-friendly way
    for model in models:
        line = f"{model['id']}: {model['prefix']} & "
        parts = []
        for case in ['Case 1', 'Case 2', 'Case 3']:
            for r in ['R1', 'R2']:
                metrics_parts = []
                for m in ['uy', 'ux', 'phi']:
                    val = res_df[(res_df['Case'] == case) & (res_df['Range'] == r)][f'{model["id"]}_{m}'].values[0]
                    metrics_parts.append(f"{val:.1f}" if not np.isnan(val) else "---")
                parts.append(" / ".join(metrics_parts))
        f.write(line + " & ".join(parts) + " \\\\\n")

