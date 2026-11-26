
import re, json

f1 = 'C:/Users/manpe/.gemini/antigravity/brain/f9c79878-1b8c-4f28-ba07-c042a3fe4641/.user_uploaded/media_1795713860862_794fb1c6.html'
f2 = 'C:/Users/manpe/.gemini/antigravity/brain/f9c79878-1b8c-4f28-ba07-c042a3fe4641/.user_uploaded/media_1795713881513_9fe0541f.html'

with open(f1, 'r', encoding='utf-8') as f:
    c1 = f.read()

with open(f2, 'r', encoding='utf-8') as f:
    c2 = f.read()

# Extract Grade 10 ALL_UNITS_DATA
m1 = re.search(r'const ALL_UNITS_DATA\s*=\s*(\{[\s\S]*?\});\s*// Deep copy', c1)
grade10_data_str = m1.group(1)

# Extract Grade 11 RAW_UNITS_2_TO_5 and ALL_UNITS_DATA
idx_raw = c2.find('const RAW_UNITS_2_TO_5 =')
idx_storage_custom = c2.find('const STORAGE_CUSTOM_QUESTIONS_KEY =')
grade11_blocks_str = c2[idx_raw:idx_storage_custom]

# Save extracted blocks
with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/extracted_g10.js', 'w', encoding='utf-8') as f:
    f.write('const GRADE_10_UNITS = ' + grade10_data_str + ';')

with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/extracted_g11.js', 'w', encoding='utf-8') as f:
    f.write(grade11_blocks_str)

print('Extracted JS successfully')
