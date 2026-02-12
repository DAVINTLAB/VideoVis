import os
import json
import glob
from collections import Counter
import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from v1.main import comments_collect_visualization, load_video_metadata
from v1.member_count import get_new_members
from v1.nuvem import gerar_nuvem_palavras, file_to_json
from v1.stats import get_top_authors, get_author_comments
import plotly.graph_objects as go
from v2.app_pages.scream_index.scream_index import scream_index_page
from v2.app_pages.sentiment.sentiment_analysis import sentiment_analysis_page
from v2.app_pages.toxic.toxic_types import toxic_types_page
from v2.output.counts.sentiment_type_counts import count_sentiment_types
from v2.output.counts.toxic_type_counts import count_toxic_types
from text_classification.CustomModelPage import custom_model_classification_page
from text_classification.ClassificationPage import classification_page
from text_classification.ModelComparisonsPage import model_comparisons_page

st.set_page_config(
    page_title='VideoVis',
    page_icon='📊',
    layout='wide'
)

UPLOAD_DIR = 'input'

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def landing_page():
    st.title('VideoVis')

    st.write('Select one of the options on the sidebar to start analyzing the comments')

    json_file = st.file_uploader('Upload comments.json', type='json')

    upload_json(json_file)

    st.button('Refresh', on_click=lambda: upload_json(json_file))

    st.markdown('''
    ## How to Use?
                
    **1. Upload a JSON File**  
    - Click the *Browse Files* button above to upload a JSON file.
                    
    **2. Run Classification (toxicity classification)**  
    - If you haven’t run **Classification** yet, go to the **"Classification"** option in the sidebar.  
    - The model will analyze all comments and classify them according to their toxicity.  
    - This process may take **several minutes**.  
    - Once it’s finished, you can **download the resulting file** to check the new fields added.  
                    
    **3. Custom Model Classification**  
    - Go to the **"Custom Model Classification"** tab in the sidebar.  
    - Choose the column to be analyzed (**`message`**).  
    - Provide a Hugging Face model ID (or leave the default).  
    - Provide a name for the file with the results or leave the default (you dont need to download it).
    OBS: We only support JSON file output for now.
    - Click **Start Classification** to begin. It may take **several minutes**.
    - [Optional] At the end, you’ll be able to **download the classified file** with the results.  
    
    **4. Model Comparisons**  
    - Go to the **"Model Comparisons"** tab in the sidebar.
    - This section allows you to compare the results from Detoxify and your custom model.
    - You must select the label(s) that indicate toxicity in your custom model (e.g. label_1 in the default model used).
    - You can see how many comments each model classified as toxic and where they agree or disagree.
    - You can also download a file with the comments both models classified as toxic.            
    ''')

def most_comments():
    st.title('Top Comments')
    if st.session_state.get('comments_file') is None:
        st.warning('Please upload a comments.json file first in the "Upload Json" page')
        return
    
    comments_data = st.session_state['comments_file']
    
    # Tab 1: Top 10 comentários com mais likes (se existir o campo)
    tab1, tab2, tab3, tab4 = st.tabs(["Top Comments by Likes", "Top Comments by Replies", "Most Used Words", "Top Authors"])
    
    with tab1:
        st.subheader("Top Comments by Likes")
        # Verificar se existe campo de likes/likeCount
        comments_with_likes = [c for c in comments_data if 'likeCount' in c or 'likes' in c]
        if comments_with_likes:
            # Ordenar por likes
            sorted_comments = sorted(comments_with_likes, 
                                   key=lambda x: int(x.get('likeCount', x.get('likes', 0))), 
                                   reverse=True)[:10]
            for idx, comment in enumerate(sorted_comments, 1):
                likes = comment.get('likeCount', comment.get('likes', 0))
                st.write(f"**{idx}. {comment['author']}** ({likes} likes)")
                st.write(f"> {comment['message']}")
                st.divider()
        else:
            st.info("Comments data does not contain likes information")
    
    with tab2:
        st.subheader("Top Comments by Replies")
        # Verificar se existe campo de replies/replyCount
        comments_with_replies = [c for c in comments_data if 'replyCount' in c or 'replies' in c]
        if comments_with_replies:
            # Ordenar por replies
            sorted_comments = sorted(comments_with_replies, 
                                   key=lambda x: int(x.get('replyCount', x.get('replies', 0))), 
                                   reverse=True)[:10]
            for idx, comment in enumerate(sorted_comments, 1):
                replies_count = comment.get('replyCount', 0)
                replies_list = comment.get('replies', [])
                actual_replies = len(replies_list)
                
                # Label mostrando quantos replies estão disponíveis
                if actual_replies < replies_count:
                    label = f"**{idx}. {comment['author']}** ({actual_replies} of {replies_count} replies)"
                else:
                    label = f"**{idx}. {comment['author']}** ({replies_count} replies)"
                
                with st.expander(label):
                    st.write(f"> {comment['message']}")
                    
                    if replies_count > 0:
                        st.subheader("Replies:")
                        if replies_list:
                            for reply in replies_list:
                                st.write(f"**{reply['author']}** 👍 {reply.get('likes', 0)}")
                                st.write(f"> {reply['message']}")
                                st.divider()
                            if actual_replies < replies_count:
                                st.caption(f"Note: Only {actual_replies} of {replies_count} total replies are displayed (API limitation)")
                        else:
                            st.info("No replies data available")
                    else:
                        st.info("No replies yet")
        else:
            st.info("Comments data does not contain replies information")
    
    with tab3:
        st.subheader("Most Used Words in Comments")
        # Contar palavras
        all_words = []
        for comment in comments_data:
            words = comment['message'].lower().split()
            # Remover palavras muito curtas e comuns
            words = [w for w in words if len(w) > 3]
            all_words.extend(words)
        
        # Contar frequência
        word_counts = Counter(all_words)
        top_20_words = word_counts.most_common(20)
        
        if top_20_words:
            # Criar colunas para melhor visualização
            col1, col2 = st.columns(2)
            for idx, (word, count) in enumerate(top_20_words):
                if idx % 2 == 0:
                    col = col1
                else:
                    col = col2
                
                with col:
                    with st.expander(f"**{word}**: {count} occurrences"):
                        # Encontrar comentários que contêm essa palavra (palavra exata)
                        comments_with_word = []
                        for c in comments_data:
                            words_in_comment = c['message'].lower().split()
                            if word in words_in_comment:
                                comments_with_word.append(c)
                        
                        st.write(f"Found in {len(comments_with_word)} comments:")
                        
                        # Key única para cada palavra
                        key = f"show_all_{word}_{idx}"
                        
                        # Inicializar o estado se não existir
                        if key not in st.session_state:
                            st.session_state[key] = False
                        
                        # Mostrar primeiros 5 ou todos
                        if st.session_state[key]:
                            # Mostrar todos
                            for comment in comments_with_word:
                                st.write(f"- **{comment['author']}**: {comment['message']}")
                                st.divider()
                            if st.button("Hide All", key=f"hide_{key}"):
                                st.session_state[key] = False
                                st.rerun()
                        else:
                            # Mostrar primeiros 5
                            for comment in comments_with_word[:5]:
                                st.write(f"- **{comment['author']}**: {comment['message']}")
                                st.divider()
                            
                            # Mostrar botão "See All" se houver mais de 5
                            if len(comments_with_word) > 5:
                                if st.button(f"See All ({len(comments_with_word)} total)", key=f"see_all_{key}"):
                                    st.session_state[key] = True
                                    st.rerun()
            
            # Word Cloud
            st.divider()
            st.subheader("Word Cloud Visualization")
            
            # Criar word cloud
            text = ' '.join(all_words)
            if text:
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
                
                # Plotar com matplotlib
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            else:
                st.info("Not enough words to generate word cloud")
        else:
            st.info("No words found")
    
    with tab4:
        st.subheader("Top Authors")
        n_authors = st.slider('Number of authors to display', 1, 20, 10)
        authors = get_top_authors(comments_data, n=n_authors)
        
        if authors:
            for idx, (author, count) in enumerate(authors, 1):
                with st.expander(f"**{idx}. {author}**: {count} comments"):
                    # Encontrar todos os comentários desse autor
                    author_comments = [c for c in comments_data if c['author'] == author]
                    for comment in author_comments:
                        likes = comment.get('likeCount', 0)
                        replies = comment.get('replyCount', 0)
                        st.write(f"**{comment['message']}**")
                        st.caption(f"{likes} likes | {replies} replies")
                        st.divider()
        else:
            st.info("No authors found")

def show_stats():
    st.title('Key Stats')
    if st.session_state.get('comments_file') is None:
        st.warning('Please upload a comments.json file first in the "Upload Json" page')
        return
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

    sentiment_counts = count_sentiment_types(st.session_state['comments_file'])
    total_positive = sentiment_counts.get('POS', 0)
    total_neutral = sentiment_counts.get('NEU', 0)
    total_negative = sentiment_counts.get('NEG', 0)
    total_toxic = count_toxic_types(st.session_state['comments_file']).get('toxicity', 0)

    # Tenta carregar metadados do vídeo
    video_metadata = None
    video_id = st.session_state.get('VIDEO_ID')
    if video_id:
        video_metadata = load_video_metadata(video_id)
    
    # Se não encontrou por VIDEO_ID, procura por arquivos de metadados existentes
    if not video_metadata:
        metadata_files = glob.glob("video_metadata_*.json")
        if metadata_files:
            try:
                with open(metadata_files[0], 'r', encoding='utf-8') as f:
                    video_metadata = json.load(f)
            except:
                video_metadata = None

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

    # Primeira linha - Video Views, Total Comments, Total Authors
    col1, col2, col3 = st.columns(3)
    with col1:
        if video_metadata and 'viewCount' in video_metadata:
            st.plotly_chart(create_card("Video Views", video_metadata['viewCount'], card_color="plum", text_color="purple"), use_container_width=True)
    with col2:
        st.plotly_chart(create_card("Total Comments", total_comments, card_color="lightblue", text_color="darkblue"), use_container_width=True)
    with col3:
        st.plotly_chart(create_card("Total Authors", total_authors, card_color="lightyellow", text_color="darkorange"), use_container_width=True)

    # Segunda linha - Total Words, Unique Words, Avg Comments/Person
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(create_card("Total Words", total_words, card_color="lightgreen", text_color="darkgreen"), use_container_width=True)
    with col2:
        st.plotly_chart(create_card("Unique Words", unique_words, card_color="lightpink", text_color="darkred"), use_container_width=True)
    with col3:
        st.plotly_chart(create_card("Avg Comments/Person", avg_comments_per_person, card_color="lightgray", text_color="black"), use_container_width=True)

    # Terceira linha - Positive, Neutral, Negative Sentiment Comments
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(create_card("Positive Sentiment Comments %", (total_positive / total_comments) * 100, card_color="lightgreen", text_color="darkgreen"), use_container_width=True)
    with col2:
        st.plotly_chart(create_card("Neutral Sentiment Comments %", (total_neutral / total_comments) * 100, card_color="lightyellow", text_color="darkorange"), use_container_width=True)
    with col3:
        st.plotly_chart(create_card("Negative Sentiment Comments %", (total_negative / total_comments) * 100, card_color="red", text_color="white"), use_container_width=True)

    # Quarta linha - Toxic Comments
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(create_card("Toxic Comments %", (total_toxic / total_comments) * 100, card_color="red", text_color="white"), use_container_width=True)

def upload_json(json_file):
    if json_file is None:
        return
    content = json_file.read().decode("utf-8")
    data = json.loads(content)

    st.session_state['comments_file'] = data

pagina = st.sidebar.selectbox('Page', ['Comments Collection', 'Upload Json','Classification', 'Custom Model Classification', 'Model Comparisons', 'Top Comments', 'Stats', 'Toxic Speech', 'Scream Index', 'Sentiment Analysis'])

if pagina == 'Top Comments':
    most_comments()
elif pagina == 'Stats':
    show_stats()
elif pagina == 'Toxic Speech':
    toxic_types_page()
elif pagina == 'Scream Index':
    scream_index_page()
elif pagina == 'Sentiment Analysis':
    sentiment_analysis_page()
elif pagina == 'Custom Model Classification':
    custom_model_classification_page()
elif pagina == 'Classification':
    classification_page()
elif pagina == 'Model Comparisons':
    model_comparisons_page()
elif pagina == 'Comments Collection':
    comments_collect_visualization()
else:
    landing_page()
