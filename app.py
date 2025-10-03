import os
import json
import streamlit as st
from v1.member_count import get_new_members
from v1.nuvem import gerar_nuvem_palavras, file_to_json
from v1.stats import get_top_authors, get_author_comments
from v1.particoes import get_partitions
from v1.peaks import get_peaks, get_top_words, get_word_context
import plotly.graph_objects as go
from v2.app_pages.scream_index.scream_index import scream_index_page
from v2.app_pages.sentiment.sentiment_analysis import sentiment_analysis_page
from v2.app_pages.toxic.toxic_types import toxic_types_page
from v2.output.counts.sentiment_type_counts import count_sentiment_types
from v2.output.counts.toxic_type_counts import count_toxic_types
from text_classification.CustomModelPage import custom_model_classification_page
from text_classification.DetoxifyPage import detoxify_page
from text_classification.ModelComparisonsPage import model_comparisons_page

st.set_page_config(
    page_title='StreamVis',
    page_icon='📊',
    layout='wide'
)

if st.session_state.get('comments_file') is None:
    with open('input/comments.json', encoding='utf-8') as json_file:
        st.session_state['comments_file'] = json.load(json_file)

if st.session_state.get('partitions') is None:
    st.session_state['partitions'] = get_partitions(st.session_state['comments_file'])

UPLOAD_DIR = 'input'

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def landing_page():
    st.title('StreamVis')

    st.write('Select one of the options on the sidebar to start analyzing the comments')

    json_file = st.file_uploader('Upload comments.json', type='json')

    upload_json(json_file)

    st.button('Refresh', on_click=lambda: upload_json(json_file))

    st.markdown('''
    ## How to Use?
                
    **1. Upload a JSON File**  
    - Click the *Browse Files* button above to upload a JSON file.
                    
    **2. Run Detoxify (toxicity classification)**  
    - If you haven’t run **Detoxify** yet, go to the **"Detoxify Classification"** option in the sidebar.  
    - The model will analyze all comments and classify them according to their toxicity.  
    - This process may take **several minutes**.  
    - Once it’s finished, you can **download the resulting file** to check the new fields added.  
                    
    **3. Custom Model Classification**  
    - Go to the **"Custom Model Classification"** tab in the sidebar.  
    - Choose the column to be analyzed (**`message`**).  
    - Provide a Hugging Face model ID (or leave the default).  
    - Provide a name for the file with the results or leave the default (you dont need to download it).
    OBS: We only support JSON file output for now.
    - Click **Start Classification** to begin.  
    - [Optional] At the end, you’ll be able to **download the classified file** with the results.  
    
    **4. Model Comparisons**  
    - Go to the **"Model Comparisons"** tab in the sidebar.
    - This section allows you to compare the results from Detoxify and your custom model.
    - You must select the label(s) that indicate toxicity in your custom model (e.g. label_1 in the default model used).
    - You can see how many comments each model classified as toxic and where they agree or disagree.
    - You can also download a file with the agreed toxic comments from both models.            
    ''')

def comments_peak():
    st.title('Comments Peak')
    num_peaks = st.slider('Number of peaks on display', 1, 15, 5)
    peaks, image_path = get_peaks(st.session_state['comments_file'], top=num_peaks)
    st.image(image_path)
    for index, peak in enumerate(peaks):
        with st.expander(f'Peak {index+1}: {peak["comments"]} comments'):
            st.write(f'Start: {peak["start"]}')
            st.write(f'End: {peak["end"]}')
            st.image(gerar_nuvem_palavras(peak['messages'], complemento=f'_pico_{index}'))
            top_words_count = get_top_words(peak['messages'], n = 50)
            top_words = top_words_count.index.to_list()
            word = st.selectbox('Top words', top_words)

            st.write(get_word_context(peak['messages'], word))

def most_comments():
    st.title('Top commenters')
    n_authors = st.slider('Number of commenters on display', 1, 10, 5)
    if st.session_state['comments_file'] is not None:
        authors = get_top_authors(st.session_state['comments_file'], n=n_authors)
        for author, count in authors:
            with st.expander(f'{author}: {count} comments'):
                path, comments = get_author_comments(author, st.session_state['comments_file'])
                st.image(path)
                for comment in comments:
                    st.write(f"{comment['time_elapsed']} - {comment['message']}")

def show_partitions():
    st.title('Partitions')
    num_part = st.slider('Number of partitions on display', 1, 10, 5)
    st.session_state['partitions'] = get_partitions(st.session_state['comments_file'], n=num_part)
    for index, partition in st.session_state['partitions'].items():
        with st.expander(f'Partition {index+1}'):
            st.write(f'Comments: {len(partition["comments"])}')
            st.write(f'Start: {partition["start"]}')
            st.write(f'End: {partition["end"]}')
            st.image(gerar_nuvem_palavras(partition['comments'], complemento=f'_particao_{index}'))
            top_words_count = get_top_words(partition['comments'])
            top_words = top_words_count.index.to_list()
            word = st.selectbox('Top words', top_words)

            st.write(get_word_context(partition['comments'], word))

def show_stats():
    st.title('Key Stats')

    comments_data = st.session_state['comments_file']

    total_comments = len(comments_data)
    total_authors = len(set([comment["author"] for comment in comments_data]))
    avg_comments_per_person = total_comments / total_authors
    total_words = sum([len(comment["message"].split()) for comment in comments_data])
    unique_words = len(set([word for comment in comments_data for word in comment["message"].split()]))
    avg_words_per_comment = total_words / total_comments
    _, new_mem = get_new_members(comments_data)
    if new_mem is not None:
        new_members_count = len(new_mem)
    else:
        new_members_count = 0

    total_positive, total_neutral, total_negative = count_sentiment_types(st.session_state['comments_file']).values()
    total_toxic = count_toxic_types(st.session_state['comments_file']).get('toxicity', 0)

    def create_card(title, value, card_color="lightgray", text_color="black"):
        fig = go.Figure(go.Indicator(
            mode="number",
            value=value,
            title={"text": title, "font": {"size": 24, "color": text_color}},
            number={"font": {"size": 40, "color": text_color}},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))

        fig.update_layout(
            paper_bgcolor=card_color,
            margin=dict(l=20, r=20, t=50, b=50),
            height=200
        )
        return fig

    col1, col2, col3 = st.columns(3)

    with col1:
        st.plotly_chart(create_card("Total Comments", total_comments, card_color="lightblue", text_color="darkblue"), use_container_width=True)
        st.plotly_chart(create_card("Total Words", total_words, card_color="lightgreen", text_color="darkgreen"), use_container_width=True)
        st.plotly_chart(create_card("Positive Sentiment Comments %", (total_positive / total_comments) * 100, card_color="lightgreen", text_color="darkgreen"), use_container_width=True)
        st.plotly_chart(create_card("Toxic Comments %", (total_toxic / total_comments) * 100, card_color="red", text_color="white"), use_container_width=True)

    with col2:
        st.plotly_chart(create_card("Total Authors", total_authors, card_color="lightyellow", text_color="darkorange"), use_container_width=True)
        st.plotly_chart(create_card("Unique Words", unique_words, card_color="lightpink", text_color="darkred"), use_container_width=True)
        st.plotly_chart(create_card("Neutral Sentiment Comments %", (total_neutral / total_comments) * 100, card_color="lightyellow", text_color="darkorange"), use_container_width=True)

    with col3:
        st.plotly_chart(create_card("Avg Comments/Person", avg_comments_per_person, card_color="lightgray", text_color="black"), use_container_width=True)
        st.plotly_chart(create_card("New Members", new_members_count, card_color="lightgray", text_color="black"), use_container_width=True)
        st.plotly_chart(create_card("Negative Sentiment Comments %", (total_negative / total_comments) * 100, card_color="red", text_color="white"), use_container_width=True)

def show_new_members():
    st.title('Members')
    member_data = st.session_state['comments_file']
    path, members = get_new_members(member_data)
    if path is not None:
        st.image(path)
        with st.expander('New members', expanded=True):
            for member in members:
                st.write(f'{member["author"]} - {member["time_elapsed"]}')
    else:
        st.write('No new members found')

def upload_json(json_file):
    if json_file is None:
        return
    content = json_file.read().decode("utf-8")
    data = json.loads(content)

    st.session_state['comments_file'] = data

pagina = st.sidebar.selectbox('Page', ['Upload Json','Detoxify Classification', 'Custom Model Classification', 'Model Comparisons', 'Comments peak', 'Top comment authors', 'Partitions', 'Stats', 'New members', 'Toxic Speech', 'Scream Index', 'Sentiment Analysis'])

if pagina == 'Comments peak':
    comments_peak()
elif pagina == 'Top comment authors':
    most_comments()
elif pagina == 'Partitions':
    show_partitions()
elif pagina == 'Stats':
    show_stats()
elif pagina == 'New members':
    show_new_members()
elif pagina == 'Toxic Speech':
    toxic_types_page()
elif pagina == 'Scream Index':
    scream_index_page()
elif pagina == 'Sentiment Analysis':
    sentiment_analysis_page()
elif pagina == 'Custom Model Classification':
    custom_model_classification_page()
elif pagina == 'Detoxify Classification':
    detoxify_page()
elif pagina == 'Model Comparisons':
    model_comparisons_page()
else:
    landing_page()
