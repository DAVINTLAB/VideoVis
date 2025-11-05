import requests
from dateutil import parser
import json
import time
import os
import streamlit as st

WAIT_TIME = 20  # Tempo de espera em segundos

def comments_collect_visualization():
    st.title('Comment Collection')
    
    api_key = st.text_input("API Key (Google)", type= "password", key= "google_api_key")
    if api_key:
        st.session_state['GOOGLE_API_KEY'] = api_key
        
    video_input = st.text_input("Youtube Video URL or ID", placeholder="https://youtube.com/watch?v=...")
    
    if "youtube.com" in video_input or "youtu.be" in video_input:
        if "watch?v=" in video_input:
            video_id = video_input.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in video_input:
            video_id = video_input.split("youtu.be/")[1].split("?")[0]
    else:
        video_id = video_input
    
    if video_id:
        st.session_state['VIDEO_ID'] = video_id
        
    if st.button("Start Collection", type = "secondary"):
        if not api_key or not video_id:
            st.error("Pleas provide both API Key and Video ID")
        else:
            st.session_state['GOOGLE_API_KEY'] = api_key
            st.session_state['VIDEO_ID'] = video_id
            
            with st.spinner("Collecting comments..."):
                live_chat_id, live_start_time_utc = get_live_details()
                if live_chat_id and live_start_time_utc:
                    new_comments = get_chat_messages(live_chat_id, live_start_time_utc)
                    new_count = append_new_comments(new_comments)
                    st.success(f" Collected and added {new_count} new comments")
                else:
                    st.error(" Could not get live details. Check if video is live.")
                    
        st.success(f" Collected {new_count} comments")
        
        # Adicionar botão de download
        comments = load_existing_comments()
        if comments:
            json_string = json.dumps(comments, indent=2, ensure_ascii=False)
            st.download_button(
                label=" Download Collected Comments",
                data=json_string,
                file_name="comments.json",
                mime="application/json"
            )
            

def get_live_details():
    api_key = st.session_state.get('GOOGLE_API_KEY')
    video_id = st.session_state.get('VIDEO_ID')
    
    url = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if "items" in data and len(data["items"]) > 0:
        live_details = data["items"][0]["liveStreamingDetails"]
        if "actualStartTime" in live_details:
            live_start_time = live_details["actualStartTime"]
            return live_details.get("activeLiveChatId"), parser.isoparse(live_start_time)
    return None, None

def get_chat_messages(live_chat_id, live_start_time_utc):
    comments_list = []
    api_key = st.session_state.get('GOOGLE_API_KEY')
    chat_url = f"https://www.googleapis.com/youtube/v3/liveChat/messages?liveChatId={live_chat_id}&part=snippet,authorDetails&maxResults=200&key={api_key}"
    chat_response = requests.get(chat_url)
    chat_data = chat_response.json()

    if "items" in chat_data:
        for item in chat_data["items"]:
            comment_id = item.get("id")
            author = item["authorDetails"]["displayName"]
            try:
                message = item["snippet"]["displayMessage"]
            except:
                message = ""
            timestamp = item["snippet"].get("publishedAt")
            
            if not timestamp or not comment_id:
                continue # Ignora comentários sem timestamp ou ID - Podia dar problema sem

            # Calcula o tempo decorrido desde o início da live, convertendo e tirando após a vírgula
            message_time_utc = parser.isoparse(timestamp)
            
            time_elapsed = message_time_utc - live_start_time_utc
            
            time_elapsed_str = str(time_elapsed).split('.')[0]
            
            comment_entry = {
                "id": comment_id,
                "time_elapsed": time_elapsed_str,
                "author": author,
                "message": message
            }
            comments_list.append(comment_entry)
    return comments_list

def load_existing_comments():
    try:
        with open('comments.json', 'r', encoding='utf-8') as f:
            # Verifica se o arquivo está vazio
            if f.read(1):
                f.seek(0)  # Volta para o início do arquivo
                return json.load(f)
            else:
                return []  # Arquivo vazio
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Arquivo não encontrado ou corrompido

def save_comments(comments_list):
    with open('comments.json', 'w', encoding='utf-8') as f:
        json.dump(comments_list, f, ensure_ascii=False, indent=4)

def append_new_comments(new_comments):
    existing_comments = load_existing_comments()
    existing_ids = {comment.get('id') for comment in existing_comments if 'id' in comment}
    
    # Filtra apenas os novos comentários
    new_comments_filtered = [comment for comment in new_comments if comment['id'] not in existing_ids]
    
    # Adiciona novos comentários ao arquivo existente
    existing_comments.extend(new_comments_filtered)
    save_comments(existing_comments)
    
    return len(new_comments_filtered)  # Retorna a quantidade de novos comentários

# Loop para coletar e salvar comentários
#if __name__ == "__main__":
#    try:
#        while True:
#            live_chat_id, live_start_time_utc = get_live_details()
#            if live_chat_id and live_start_time_utc:
#                new_comments = get_chat_messages(live_chat_id, live_start_time_utc)
#                new_count = append_new_comments(new_comments)
#                print(f"Coletado e adicionado {new_count} novos comentários.")
#            else:
#                print("Não foi possível obter os detalhes da live ou o chat ao vivo. Verifique se o vídeo está ao vivo e se os detalhes estão disponíveis.")
            
#            time.sleep(WAIT_TIME)
#    except KeyboardInterrupt:
#        print("\n Collection stopped by user")