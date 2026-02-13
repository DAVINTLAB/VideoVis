import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

def model_comparisons_page():
    st.title("Model Comparisons")
    st.markdown("Compare results between Detoxify (pre-analyzed) and Custom Model classifications")
    st.markdown("---")

    if 'comments_file' not in st.session_state or st.session_state['comments_file'] is None:
        st.warning('⚠️ Please upload a comments.json file first in the "Upload Json" page')
        return

    comments_list = st.session_state['comments_file']
    
    if 'selectedTextColumn' not in st.session_state or st.session_state['selectedTextColumn'] is None:
        selected_column = "message"
    else:
        selected_column = st.session_state['selectedTextColumn']

    st.success(f"✅ Comparing results using column: **{selected_column}**")
    
    if 'model_labels' in st.session_state and st.session_state['model_labels']:
        st.markdown("### Select Toxic Labels for Custom Model")
        selected_labels = st.multiselect(
            "Select toxic labels:",
            options=st.session_state['model_labels'],
            default=[],
            help="Choose which labels to include in the comparison"
        )
        st.session_state['selected_toxic_labels'] = selected_labels
    else:
        st.warning("⚠️ No labels found for the custom model. Please ensure the model provides label information.")
        selected_labels = []
        st.session_state['selected_toxic_labels'] = selected_labels

    # Ensure processing and charts occur only after labels are selected
    if selected_labels:
        st.markdown("### 📊 Data Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Comments", len(comments_list))

        with col2:
            detoxify_toxic = sum(1 for c in comments_list if c.get('toxicity', 0) >= 0.5)
            st.metric("Detoxify Toxic (≥0.5)", detoxify_toxic)

        with col3:
            custom_model_toxic = sum(1 for c in comments_list if c.get('predicted_label') in selected_labels)
            st.metric("Custom Model Toxic", custom_model_toxic)

        st.markdown("### 📈 Agreement Statistics")

        json_data = []
        agreements = 0
        total_compared = len(comments_list)

        for i, comment in enumerate(comments_list):
            detoxify_result = "TOXIC" if comment.get('toxicity', 0) >= 0.5 else "NON-TOXIC"
            custom_result = comment.get('predicted_label', 'N/A').upper()

            models_agree = False
            if (custom_result in selected_labels and detoxify_result == "TOXIC") or \
               (custom_result not in selected_labels and detoxify_result == "NON-TOXIC"):
                models_agree = True
                agreements += 1

                comment_dict = {
                    "id": comment.get('id', f'comment_{i}'),
                    "author": comment.get('author', 'Unknown'),
                    "message": comment.get('message', ''),
                    "detoxify_toxicity": comment.get('toxicity', 0),
                    "sentiment": comment.get('sentiment', 'N/A'),
                    "custom_predicted_label": custom_result,
                    "detoxify_result": detoxify_result,
                    "custom_result": custom_result,
                    "models_agree": models_agree,
                }
                json_data.append(comment_dict)

        if json_data:
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download Toxic Comments Agreed on Both Models JSON",
                data=json_string,
                file_name=f"toxic_comments_{len(json_data)}_items.json",
                mime="application/json"
            )

        if total_compared > 0:  
            st.markdown("### 📊 Comparison Charts")
        
            disagreements = total_compared - agreements
            
            agreement_labels = ['Models Agree', 'Models Disagree'] 
            agreement_values = [agreements, disagreements]
            agreement_colors = ['#2ecc71', '#e74c3c']
            
            fig_agreement = go.Figure(data=[go.Pie(
                labels=agreement_labels,
                values=agreement_values,
                hole=0.4,
                marker_colors=agreement_colors,
                textinfo='label+percent+value',
                textfont_size=12,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            
            fig_agreement.update_layout(
                title={
                    'text': 'Model Agreement vs Disagreement',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16}
                },
                font=dict(size=14),
                showlegend=True,
                height=400,
                margin=dict(t=60, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_agreement, use_container_width=True)
            
            
            agreement_rate = (agreements / total_compared) * 100
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Compared", total_compared)
            
            with col2:
                st.metric("Agreements", agreements)
            
            with col3:
                st.metric("Agreement Rate", f"{agreement_rate:.1f}%")
            
            if agreement_rate >= 80:
                st.success(f"High agreement rate: {agreement_rate:.1f}%")
            elif agreement_rate >= 60:
                st.warning(f"Moderate agreement rate: {agreement_rate:.1f}%")
            else:
                st.error(f"Low agreement rate: {agreement_rate:.1f}%")
                

    st.markdown("---")
    st.markdown("### 💡 Tips for Comparison")
    st.info("""
    • **High Agreement**: Models are consistent in their classifications
    • **Low Agreement**: Consider reviewing model parameters or training data
    • **Detoxify**: Specialized for toxicity detection with multiple categories
    • **Custom Model**: General-purpose sentiment/classification model
    """)