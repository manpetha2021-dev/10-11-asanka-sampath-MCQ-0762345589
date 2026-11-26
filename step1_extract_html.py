import os

f1 = 'C:/Users/manpe/.gemini/antigravity/brain/f9c79878-1b8c-4f28-ba07-c042a3fe4641/.user_uploaded/media_1795713860862_794fb1c6.html'

with open(f1, 'r', encoding='utf-8') as f:
    c1 = f.read()

# The HTML part is everything before the question bank <script>
idx_script = c1.find('<!-- COMPLETE QUESTION BANK (UNITS 1 TO 10')
print('HTML template cut index in f1:', idx_script)
with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/html_part.txt', 'w', encoding='utf-8') as out:
    out.write(c1[:idx_script])
print('Saved html_part.txt')
