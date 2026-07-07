import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def slot_to_time(slot):
    hours = 8 + (slot // 2)
    mins = "30" if slot % 2 != 0 else "00"
    return f"{hours:02d}:{mins}"

def time_to_slot(time_str):
    h, m = map(int, time_str.split(':'))
    return (h - 8) * 2 + (1 if m == 30 else 0)

def generate_gantt_html(schedule_data):
    if not schedule_data:
        return "<h2>Gösterilecek plan bulunamadı.</h2>"

    df_list = []
    dummy_date = "2026-01-01 " 
    
    for item in schedule_data:
        
        start_time_str = slot_to_time(item['start_slot'])
        end_time_str = slot_to_time(item['start_slot'] + item['duration'])
        
        start_time = datetime.strptime(dummy_date + start_time_str, "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(dummy_date + end_time_str, "%Y-%m-%d %H:%M")
        
        df_list.append({
            "Ameliyathane": item['room'],
            "Başlangıç": start_time,
            "Bitiş": end_time,
            "Operasyon": f"{item['patient']} - {item['operation']}",
            "Cerrah": item['surgeon'],
            "Ekip": item['team']
        })
        
    df = pd.DataFrame(df_list)
    fig = px.timeline(df, x_start="Başlangıç", x_end="Bitiş", y="Ameliyathane", 
                      color="Cerrah", hover_name="Operasyon", hover_data=["Ekip"],
                      title="Günlük Ameliyathane Gantt Çizelgesi")
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis=dict(tickformat='%H:%M', title='Saat'), font=dict(family="Arial", size=12))
    return fig.to_html(full_html=False)

def generate_heatmap_html(schedule_data):
    if not schedule_data:
        return "<h2>Gösterilecek plan bulunamadı.</h2>"

    slots_labels = [slot_to_time(i) for i in range(20)]
    unique_rooms = sorted(list(set([item['room'] for item in schedule_data])))

    matrix = {room: [0] * 20 for room in unique_rooms}
    hover_text = {room: ["Boş"] * 20 for room in unique_rooms}

    for item in schedule_data:
        room = item['room']
        
        start_slot = item['start_slot']
        end_slot = item['start_slot'] + item['duration']
        
        for t in range(start_slot, end_slot):
            if t < 20:
                matrix[room][t] = 1
                hover_text[room][t] = f"Dolu: {item['patient']}<br>Cerrah: {item['surgeon']}"

    # heatmap grafiğini oluşturur
    fig = go.Figure(data=go.Heatmap(
        z=[matrix[room] for room in unique_rooms],
        x=slots_labels,
        y=unique_rooms,
        colorscale=[[0, 'rgb(46, 204, 113)'], [1, 'rgb(231, 76, 60)']],
        showscale=False, 
        xgap=3,
        ygap=3,
        hoverinfo='text',
        text=[hover_text[room] for room in unique_rooms]
    ))
    
    fig.update_layout(
        title="Ameliyathane Kullanım Yoğunluğu (Heatmap)",
        xaxis_title="Mesai Saatleri",
        yaxis_title="Ameliyathaneler",
        font=dict(family="Arial", size=12),
        xaxis=dict(tickangle=-45) 
    )
    
    return fig.to_html(full_html=False)