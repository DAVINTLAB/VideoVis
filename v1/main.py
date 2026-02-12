import requests
from dateutil import parser
import json
import time
import os
import streamlit as st

WAIT_TIME = 20  # Tempo de espera em segundos

def get_comments_file_path():
    """Retorna o caminho do arquivo de comentários específico para o vídeo atual.
    Usa `comments_<VIDEO_ID>.json` quando houver `VIDEO_ID` na sessão;
    caso contrário, utiliza `comments.json` como padrão.
    """
    video_id = st.session_state.get('VIDEO_ID')
    if video_id:
        return f"comments_{video_id}.json"
    return "comments.json"

def comments_collect_visualization():
    st.title('Comment Collection')
    st.text(" If you already have a JSON file with comments, go to page 'Upload JSON' to upload it and skip this step.")
    st.text(" Tutorial video to register and save the GOOGLE_API_KEY: https://youtu.be/d4gPrwpzTkc ")
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

    # Opção para iniciar do zero para este vídeo
    start_fresh = True

    if st.button("Start Collection", type = "secondary"):
        if not api_key or not video_id:
            st.error("Please provide both API Key and Video ID")
        else:
            st.session_state['GOOGLE_API_KEY'] = api_key
            st.session_state['VIDEO_ID'] = video_id
            
            video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
            video_response = requests.get(video_url)
            video_data = video_response.json()
            
            if "items" in video_data and len(video_data["items"]) > 0:
                live_broadcast_content = video_data["items"][0]["snippet"].get("liveBroadcastContent", "none")
                
                if live_broadcast_content == "live":
                    st.error("Live videos are not supported. Please use a regular video or a finished live stream.")
                    st.markdown("### For live stream analysis, visit:")
                    st.markdown("[**StreamVis Live - Live Stream Analytics**](https://streamvis21.streamlit.app/)", unsafe_allow_html=True)
                    st.markdown("*This tool supports real-time live stream comment collection and analysis.*")
                    new_count = 0
                else:
                    if start_fresh:
                        # Limpa o arquivo de comentários específico deste vídeo
                        save_comments([])
            
                    with st.spinner("Collecting comments..."):
                        st.info("Detected: Regular video (or finished live)")
                        new_comments = get_video_comments()
                        if new_comments is not None:
                            new_count = append_new_comments(new_comments)
                            st.success(f" Collected and added {new_count} new comments from video")
                        else:
                            st.error(" Could not retrieve comments. Check API Key and Video ID.")
                            new_count = 0
            
            else:
                st.error("Video not found. Check API Key and Video ID.")
                new_count = 0
        
        # Adicionar botão de download
        comments = load_existing_comments()
        if comments:
            json_string = json.dumps(comments, indent=2, ensure_ascii=False)
            # Define o nome do arquivo de download específico por vídeo
            download_name = f"comments_{st.session_state.get('VIDEO_ID','')}.json" if st.session_state.get('VIDEO_ID') else "comments.json"
            st.download_button(
                label=" Download Collected Comments",
                data=json_string,
                file_name=download_name,
                mime="application/json"
            )

def get_video_metadata(video_id, api_key):
    """Coleta metadados do vídeo (visualizações, likes, etc)"""
    video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={api_key}"
    video_response = requests.get(video_url)
    video_data = video_response.json()
    
    if "items" not in video_data or len(video_data["items"]) == 0:
        return None
    
    video_item = video_data["items"][0]
    metadata = {
        "video_id": video_id,
        "title": video_item.get("snippet", {}).get("title", ""),
        "viewCount": int(video_item.get("statistics", {}).get("viewCount", 0)),
        "likeCount": int(video_item.get("statistics", {}).get("likeCount", 0)),
        "commentCount": int(video_item.get("statistics", {}).get("commentCount", 0)),
    }
    return metadata

def save_video_metadata(metadata):
    """Salva metadados do vídeo em arquivo"""
    if metadata:
        metadata_file = f"video_metadata_{metadata['video_id']}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

def get_video_comments():
    """Coleta comentários de vídeos regulares do YouTube"""
    comments_list = []
    api_key = st.session_state.get('GOOGLE_API_KEY')
    video_id = st.session_state.get('VIDEO_ID')
    
    video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={api_key}"
    video_response = requests.get(video_url)
    video_data = video_response.json()
    
    if "items" not in video_data or len(video_data["items"]) == 0:
        return None
    
    # Salvar metadados do vídeo
    video_item = video_data["items"][0]
    metadata = {
        "video_id": video_id,
        "title": video_item.get("snippet", {}).get("title", ""),
        "viewCount": int(video_item.get("statistics", {}).get("viewCount", 0)),
        "likeCount": int(video_item.get("statistics", {}).get("likeCount", 0)),
        "commentCount": int(video_item.get("statistics", {}).get("commentCount", 0)),
    }
    save_video_metadata(metadata)
    
    video_publish_time = video_item["snippet"]["publishedAt"]
    video_start_time_utc = parser.isoparse(video_publish_time)
    
    next_page_token = None
    
    while True:
        comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet,replies&videoId={video_id}&maxResults=100&key={api_key}"
        
        if next_page_token:
            comments_url += f"&pageToken={next_page_token}"
        
        comments_response = requests.get(comments_url)
        comments_data = comments_response.json()
        
        if "items" not in comments_data:
            break
        
        for item in comments_data["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comment_id = item["snippet"]["topLevelComment"]["id"]
            author = comment["authorDisplayName"]
            message = comment["textDisplay"]
            timestamp = comment["publishedAt"]
            likes = comment.get("likeCount", 0)
            replies_count = item["snippet"].get("totalReplyCount", 0)
            
            comment_time_utc = parser.isoparse(timestamp)
            time_elapsed = comment_time_utc - video_start_time_utc
            time_elapsed_str = str(time_elapsed).split('.')[0]
            
            # Coletar respostas (replies)
            replies_list = []
            if "replies" in item and replies_count > 0:
                for reply in item["replies"]["comments"]:
                    reply_snippet = reply["snippet"]
                    replies_list.append({
                        "author": reply_snippet["authorDisplayName"],
                        "message": reply_snippet["textDisplay"],
                        "likes": reply_snippet.get("likeCount", 0)
                    })
            
            comment_entry = {
                "id": comment_id,
                "time_elapsed": time_elapsed_str,
                "author": author,
                "message": message,
                "likeCount": likes,
                "replyCount": replies_count,
                "replies": replies_list
            }
            comments_list.append(comment_entry)
        
        next_page_token = comments_data.get("nextPageToken")
        if not next_page_token:
            break
    
    return comments_list

def load_video_metadata(video_id):
    """Carrega metadados do vídeo do arquivo"""
    metadata_file = f"video_metadata_{video_id}.json"
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def load_existing_comments():
    try:
        file_path = get_comments_file_path()
        with open(file_path, 'r', encoding='utf-8') as f:
            if f.read(1):
                f.seek(0)  # Volta para o início do arquivo
                return json.load(f)
            else:
                return []  # Arquivo vazio
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Arquivo não encontrado ou corrompido

def save_comments(comments_list):
    file_path = get_comments_file_path()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(comments_list, f, ensure_ascii=False, indent=4)

def append_new_comments(new_comments):
    existing_comments = load_existing_comments()
    existing_ids = {comment.get('id') for comment in existing_comments if 'id' in comment}
    
    new_comments_filtered = [comment for comment in new_comments if comment['id'] not in existing_ids]
    
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