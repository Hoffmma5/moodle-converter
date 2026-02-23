import streamlit as st
import pandas as pd
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Moodle XML Converter",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. TEMPLATE GENERATOR ---
@st.cache_data
def get_template_excel():
    """Generates a sample Excel template on the fly."""
    # Create a dataframe with the sample data
    data = {
        'Category': ['LF3-Bio-2015', 'LF3-Bio-2015'],
        'QuestionName': ['LF3-Bio-2015 | Q01', 'LF3-Bio-2015 | Q02'],
        'Year': [2015, 2015],
        'Topic': ['B1', 'B1'],
        'SubTopic': ['B1.1', 'B1.1'],
        'Question': ['In atmosphere there is … of oxygen', 'Which sequence of the pyramid of life in an ecosystem is correct?'],
        'OptionA': ['21%', 'solar energy - herbivores - plants - carnivores'],
        'OptionB': ['78%', 'solar energy - carnivores - herbivores - plants'],
        'OptionC': ['2%', 'solar energy - plants - carnivores - herbivores'],
        'OptionD': ['36%', 'solar energy - plants - herbivores - carnivores'],
        'Answer': ['A', 'D'],
        'Feedback': [
            '21% is the correct atmospheric O2 concentration. Earth’s atmosphere is composed of ~78% nitrogen, ~21% oxygen...', 
            'The correct trophic sequence is solar energy -> plants -> herbivores -> carnivores.'
        ]
    }
    df = pd.DataFrame(data)
    
    # Convert DataFrame to an Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Questions')
    
    return output.getvalue()

# --- 3. CONVERTER LOGIC ---
def convert_df_to_xml(df):
    # Ensure all column names are stripped of accidental spaces
    df.columns = df.columns.str.strip()
    
    if 'Category' in df.columns:
        df['Category'] = df['Category'].fillna('Default')
        df = df.sort_values(by='Category')
    
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>\n<quiz>']
    current_category = None

    for index, row in df.iterrows():
        # Category Handling
        row_category = str(row.get('Category', 'Default')).strip()
        if row_category != current_category:
            current_category = row_category
            xml_content.append(f"""
  <question type="category">
    <category>
      <text>top/{current_category}</text>
    </category>
  </question>""")

        # Data Extraction
        q_name = str(row.get('QuestionName', f'Question {index+1}'))
        q_text = str(row.get('Question', ''))
        g_feedback = str(row.get('Feedback', ''))
        if g_feedback == 'nan': g_feedback = ''
        correct_letter = str(row.get('Answer', '')).strip().upper()

        # Tags
        tags_list = []
        for col in ['Year', 'Topic', 'SubTopic']:
            val = row.get(col)
            if pd.notna(val) and str(val).strip() != '':
                tags_list.append(str(int(val) if isinstance(val, float) and val.is_integer() else val).strip())

        tags_xml = ""
        if tags_list:
            tags_xml = "    <tags>\n" + "\n".join([f"      <tag><text>{t}</text></tag>" for t in tags_list]) + "\n    </tags>"

        # Answers Helper
        def create_ans(opt_col, letter):
            fraction = "100" if letter == correct_letter else "0"
            opt_text = row.get(opt_col, '')
            if pd.isna(opt_text): opt_text = ""
            return f"""    <answer fraction="{fraction}" format="html">
      <text><![CDATA[<p>{opt_text}</p>]]></text>
      <feedback format="html"><text></text></feedback>
    </answer>"""

        # Build Question XML
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

# --- 4. APP UI ---
st.title("📝 Excel to Moodle XML")
st.markdown("A simple tool to convert your multiple-choice questions into Moodle-compatible XML format.")

st.divider()

# Step 1: Template Download
st.subheader("1. Download Template")
st.markdown("Ensure your data matches the required format. Download the Excel template below.")
st.download_button(
    label="⬇️ Download template.xlsx",
    data=get_template_excel(),
    file_name="moodle_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.divider()

# Step 2: File Upload
st.subheader("2. Upload Your Data")
# Now accepts both Excel and CSV!
uploaded_file = st.file_uploader("Upload your filled Excel or CSV file here:", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Check file type and read accordingly
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success(f"File uploaded successfully! ({len(df)} questions detected)")
        
        # Step 3: Convert and Download
        st.subheader("3. Convert & Download")
        output_filename = st.text_input("Name your output file:", "moodle_questions")
        
        if st.button("Generate XML", type="primary"):
            with st.spinner('Converting...'):
                result_xml = convert_df_to_xml(df)
            
            st.download_button(
                label="⬇️ Download XML File",
                data=result_xml,
                file_name=f"{output_filename}.xml",
                mime="application/xml"
            )
            st.balloons()
            
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
