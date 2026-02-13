import json
from v2.output.counts.scream_index_counts import scream_index_mean
import streamlit as st
import plotly.graph_objects as go

def scream_index_page():
    """ Streamlit page to display the Scream Index.
    This function creates a Streamlit page that displays the mean Scream Index
    and a card with the Scream Index value.
    """
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
    
    def create_gauge_chart(title, value):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title, "font": {"size": 24}},
            gauge={
                'axis': {'range': [0, 1]},
                'bar': {'color': "red"},
                'steps': [
                    {'range': [0, 0.7], 'color': "lightgray"},
                    {'range': [0.7, 1], 'color': "red"}
                ]
            }
        ))
        return fig

    st.title('Scream Index Analysis')
    st.plotly_chart(create_gauge_chart(
        "Scream Index Mean",
        scream_index_mean(st.session_state['comments_file'])
    ), use_container_width=True)
    
    with st.expander("Messages above 0.7 on Scream Index", expanded=True):
        data = st.session_state['comments_file']
        scream_indices = [obj for obj in data if obj.get('scream_index', 0) > 0.70]
        st.dataframe(
            data=scream_indices,
            use_container_width=True
        )

    st.title('Top Authors by Scream Index')

    data = st.session_state['comments_file']
    commenters = {}
    scream_indices = [obj for obj in data if obj.get('scream_index', 0) > 0.70]
    for obj in scream_indices:
        commenter = obj.get('author', 'Unknown')
        if commenter not in commenters:
            commenters[commenter] = []
        commenters[commenter].append(obj)
    sorted_commenters = sorted(commenters.items(), key=lambda x: len(x[1]), reverse=True)
    top_commenters = sorted_commenters[:10]
    for commenter, comments in top_commenters:
        st.write(f"{commenter}: {len(comments)} comments")
        with st.expander(f"Comments by {commenter}", expanded=False):
            for comment in comments:
                st.write(f"- {comment.get('message', 'No content')} (Scream Index: {comment.get('scream_index', 0)})")
    
    