# Final assembler to create history_exam_unified.html

with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/html_header_body.txt', 'r', encoding='utf-8') as f:
    html_top = f.read()

with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/extracted_g10.js', 'r', encoding='utf-8') as f:
    g10_data = f.read()

with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/extracted_g11_renamed.js', 'r', encoding='utf-8') as f:
    g11_data = f.read()

with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/unified_logic.js', 'r', encoding='utf-8') as f:
    unified_logic = f.read()

html_bottom = """
    </script>
</body>
</html>
"""

final_html_path = 'C:/Users/manpe/.gemini/antigravity/scratch/history_exam/history_exam_unified.html'

with open(final_html_path, 'w', encoding='utf-8') as f_out:
    f_out.write(html_top)
    f_out.write("\n\n        // =========================================================================\n")
    f_out.write("        // GRADE 10 COMPLETE QUESTION BANK (UNITS 01 - 10)\n")
    f_out.write("        // =========================================================================\n")
    f_out.write(g10_data)
    f_out.write("\n\n        // =========================================================================\n")
    f_out.write("        // GRADE 11 COMPLETE QUESTION BANK (UNITS 01 - 08)\n")
    f_out.write("        // =========================================================================\n")
    f_out.write(g11_data)
    f_out.write("\n\n        // =========================================================================\n")
    f_out.write("        // UNIFIED SYSTEM LOGIC & SECURE AUTHENTICATION\n")
    f_out.write("        // =========================================================================\n")
    f_out.write(unified_logic)
    f_out.write(html_bottom)

print("SUCCESS: Combined final HTML assembled at:", final_html_path)
