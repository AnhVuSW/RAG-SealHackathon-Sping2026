import pandas as pd

df2 = pd.read_csv('C:/Users/ASUS/Downloads/New folder (2)/MARKETING_DataSwamp_VN/MARKETING/phan_hoi_hang_thang/phan_hoi_2023-02.csv')
df3 = pd.read_csv('C:/Users/ASUS/Downloads/New folder (2)/MARKETING_DataSwamp_VN/MARKETING/phan_hoi_hang_thang/phan_hoi_2023-03.csv')

def process(df, name):
    total = len(df)
    print(f'{name} Columns: {df.columns}')
    
    # Check if there is a sentiment column or something similar
    sent_col = None
    for col in df.columns:
        if 'sentiment' in col.lower() or 'loại' in col.lower() or 'phan_an' in col.lower():
            sent_col = col
            break
            
    if sent_col is None:
        print(f"Could not find sentiment column in {name}")
        print(df.head())
        return

    print(f'Using column: {sent_col}')
    pos = len(df[df[sent_col].str.lower().isin(['positive', 'tích cực'])])
    neg = len(df[df[sent_col].str.lower().isin(['negative', 'tiêu cực'])])
    neu = len(df[df[sent_col].str.lower().isin(['neutral', 'trung lập'])])
    
    print(f'{name} Total: {total}')
    if total > 0:
        print(f'{name} Positive: {pos} ({pos/total*100:.1f}%)')
        print(f'{name} Negative: {neg} ({neg/total*100:.1f}%)')
        print(f'{name} Neutral: {neu} ({neu/total*100:.1f}%)')

process(df2, 'Feb 2023')
process(df3, 'Mar 2023')
