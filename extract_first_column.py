import csv

INPUT_CSV = "sample/All_Comments_Final.csv"
OUTPUT_TXT = "sample/comments_column.txt"

def extract_first_column():
    with open(INPUT_CSV, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # 跳过标题行
        rows = []
        for row in reader:
            if row:  # 确保行非空
                rows.append(row[0])
    
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as out:
        for r in rows:
            out.write(r + '\n')
    
    print(f"提取 {len(rows)} 条记录（第一列）→ {OUTPUT_TXT}")

if __name__ == '__main__':
    extract_first_column()
