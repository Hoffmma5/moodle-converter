import streamlit as st
import pandas as pd
import io

def convert_csv_to_xml(df):
    # Strip whitespace z názvů sloupců
    df.columns = df.columns.str.strip()
    
    if 'Category' in df.columns:
        df['Category'] = df['Category'].fillna('Default')
        df = df.sort_values(by='Category')
    
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']
    current_category = None

    for index, row in df.iterrows():
        # --- 1. CATEGORY HANDLING ---
        row_category = str(row.get('Category', 'Default')).strip()
        if row_category != current_category:
            current_category = row_category
            category_xml = f"""
  <question type="category">
    <category>
      <text>top/{current_category}</text>
    </category>
  </question>"""
            xml_content.append(category_xml)

        # --- 2. DATA EXTRACTION ---
        q_name = str(row.get('QuestionName', f'Question {index+1}'))
        q_text = str(row.get('Question', ''))
        g_feedback = str(row.get('Feedback', ''))
        if g_feedback == 'nan': g_feedback = ''
        correct_letter = str(row.get('Answer', '')).strip().upper()

        # --- 3. TAGS ---
        tags_list = []
        for col in ['Year', 'Topic', 'SubTopic']:
            val = row.get(col)
            if pd.notna(val) and str(val).strip() != '':
                tags_list.append(str(int(val) if isinstance(val, float) and val.is_integer() else val).strip())

        tags_xml = ""
        if tags_list:
            tags_xml = "    <tags>\n" + "\n".join([f"      <tag><text>{t}</text></tag>" for t in tags_list]) + "\n    </tags>"

        # --- 4. ANSWERS ---
        def create_ans(opt_col, letter):
            fraction = "100" if letter == correct_letter else "0"
            opt_text = row.get(opt_col, '')
            return f"""    <answer fraction="{fraction}" format="html">
      <text><![CDATA[<p>{opt_text}</p>]]></text>
      <feedback format="html"><text></text></feedback>
    </answer>"""

        # --- 5. BUILD XML ---
        question_xml = f"""
  <question type="multichoice">
    <name><text>{q_name}</text></name>
    <questiontext format="html"><text><![CDATA[<p>{q_text}</p>]]></text></questiontext>
    <generalfeedback format="html"><text><![CDATA[<p>{g_feedback}</p>]]></text></generalfeedback>
    <defaultgrade>1.0000000</defaultgrade>
    <shuffleanswers>true</shuffleanswers>
    <answernumbering>ABCD</answernumbering>
{create_ans('OptionA', 'A')}
{create_ans('OptionB', 'B')}
{create_ans('OptionC', 'C')}
{create_ans('OptionD', 'D')}
{tags_xml}
  </question>"""
        xml_content.append(question_xml)

    xml_content.append('</quiz>')
    return "\n".join(xml_content)

# --- STREAMLIT UI ---
st.title("📊 Moodle XML Převodník")
st.write("Nahraj CSV a stáhni si hotový XML soubor pro Moodle.")

uploaded_file = st.file_uploader("Vyber CSV soubor", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("Soubor úspěšně nahrán!")
    
    output_filename = st.text_input("Název výsledného souboru (bez přípony)", "questions")
    
    if st.button("Vygenerovat XML"):
        result_xml = convert_csv_to_xml(df)
        
        st.download_button(
            label="⬇️ Stáhnout XML",
            data=result_xml,
            file_name=f"{output_filename}.xml",
            mime="application/xml"
        )
