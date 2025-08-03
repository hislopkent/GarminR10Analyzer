import pandas as pd
import io

def load_sessions(files):
    dfs = []
    for file in files:
        try:
            content = file.getvalue().decode("utf-8")
            df = pd.read_csv(io.StringIO(content))
            df["Session Name"] = file.name
            # Normalise club column name
            if "Club" not in df.columns and "Club Type" in df.columns:
                df["Club"] = df["Club Type"]
            dfs.append(df)
        except Exception as e:
            print(f"Failed to load {file.name}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()
