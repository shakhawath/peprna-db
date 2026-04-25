import pandas as pd

NONCANONICAL = ["ORN", "DAB", "BETAALA", "AIB", "NLE", "ORNITHINE"]  # extend as needed
NONCANONICAL = sorted(NONCANONICAL, key=len, reverse=True)

def tokenize_backbone(seq):
    if pd.isna(seq):
        return None
    seq = str(seq).strip().upper().replace(" ", "")
    tokens = []
    i = 0
    while i < len(seq):
        matched = False
        for token in NONCANONICAL:
            if seq.startswith(token, i):
                tokens.append(token)
                i += len(token)
                matched = True
                break
        if matched:
            continue
        tokens.append(seq[i])
        i += 1
    return "-".join(tokens)

df = pd.read_excel("test_run.xlsx")
df["peptide_backbone_tokenized"] = df["peptide_backbone_clean"].apply(tokenize_backbone)
df.to_excel("test_run_tokenized.xlsx", index=False)