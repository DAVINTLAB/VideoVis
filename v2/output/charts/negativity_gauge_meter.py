import plotly.graph_objects as go
from datetime import timedelta
import re

def time_str_to_seconds(time_str):
    """
    Converts a time string like '1:23:45', '12:34', or '2 days, 1:23:45' to seconds.
    """
    if not time_str or not isinstance(time_str, str):
        return 0

    days = 0
    match = re.match(r'(?:(\d+) days?, )?(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})', time_str)
    if match:
        if match.group(1):
            days = int(match.group(1))
        time_part = match.group(2)
    else:
        time_part = time_str

    parts = list(map(int, time_part.split(':')))
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        return 0

    total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total_seconds

def seconds_to_time_str(seconds: int) -> str:
    """Converts seconds to a time string 'HH:MM:SS'."""
    return str(timedelta(seconds=seconds))

def create_negativity_gauge(percentage: float):
    """Creates a gauge meter."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        title={'text': "Level of Negativity (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#d62728"}, # Cor vermelha para negatividade
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 75], 'color': "gray"}
            ],
        }
    ))
    fig.update_layout(height=400)
    return fig