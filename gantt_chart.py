import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import threading
from database import get_review_schedule
from review_handler import update_review_date, adjust_future_tasks, delete_review_task

# ✅ Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# ✅ Function to fetch review schedule dynamically
def load_review_schedule(project_id, cycle_id):
    """Fetch review schedule dynamically based on selected project and review option."""
    
    df, project_name, review_option = get_review_schedule(project_id, cycle_id)

    print(f"📌 Raw Data from Database for Project {project_id}, Cycle {cycle_id}:")
    print(df)  # Print raw SQL output

    if df.empty:
        print(f"⚠️ No review schedule data found for Project {project_id}, Cycle {cycle_id}")
        return pd.DataFrame(columns=["schedule_id", "cycle_id", "review_date", "task_name", "end_date"]), [], "", ""

    # ✅ Ensure dates are correctly converted
    date_cols = [
        'review_date',
        'planned_start_date',
        'planned_completion_date',
        'actual_start_date',
        'actual_completion_date',
        'hold_date',
        'resume_date',
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # ✅ Print converted dates
    print(
        f"🔍 Converted Dates:\n{df[['schedule_id', 'review_date', 'planned_start_date', 'actual_start_date']].head()}"
    )

    # ✅ Generate meaningful task names
    df['task_name'] = [f"Review {review_option}-{i+1}" for i in range(len(df))]

    # ✅ Add an end date for each task
    df['end_date'] = df['review_date'] + pd.Timedelta(days=1)

    print(
        f"✅ Processed Data for Gantt Chart:\n{df[['task_name', 'review_date', 'end_date', 'planned_start_date', 'planned_completion_date']]}"
    )

    # ✅ Ensure dropdown options for deletion
    dropdown_options = [{"label": task, "value": schedule_id} for task, schedule_id in zip(df['task_name'], df['schedule_id'])]

    return df, dropdown_options, project_name, review_option

# ✅ Generate Gantt Chart
def generate_gantt_chart(df, project_name, review_option):
    """Create and return a Gantt chart figure with project name and cycle ID in the title."""
    if df.empty:
        print("⚠️ No data available for Gantt chart.")
        return {}

    print("📊 Data used to generate Gantt chart:")
    print(df[['task_name', 'review_date', 'end_date']])  # Ensure all dates exist

    fig = px.timeline(
        df, 
        x_start='review_date', 
        x_end='end_date', 
        y='task_name', 
        title=f"{project_name} - Cycle {review_option} Review Schedule",
        labels={"task_name": "Review Tasks", "review_date": "Review Dates"},
        color_discrete_sequence=["#1f77b4"]
    )

    # ✅ Ensure X-axis is formatted correctly
    fig.update_layout(
        xaxis=dict(
            title="Date",
            type="date",
            tickformat="%Y-%m-%d"
        ),
        yaxis=dict(
            title="Review Tasks",
            categoryorder="total ascending"
        )
    )

    return fig


# ✅ Define Dash layout
app.layout = html.Div([
    html.H2(id="chart-title"),
    dcc.Graph(id='gantt-chart'),
    
    dcc.Dropdown(id="delete-review-dropdown", options=[], placeholder="Select a review to delete"),
    html.Button("Delete Task", id="delete-button", n_clicks=0),
    
    html.Div(id="output-message"),
])

# ✅ Callback to update Gantt chart when receiving project & cycle from UI
@app.callback(
    Output("gantt-chart", "figure"),
    Output("chart-title", "children"),
    Output("delete-review-dropdown", "options"),
    Input("delete-button", "n_clicks")  # Refresh chart when button is clicked
)
def update_gantt_chart(n_clicks):
    project_id = DASH_PROJECT_ID
    cycle_id = DASH_CYCLE_ID
    
    print(f"📌 Updating Gantt Chart for Project {project_id}, Cycle {cycle_id}")

    if not project_id or not cycle_id:
        return {}, "Select a project and review option to view schedule", []

    df, dropdown_options, project_name, review_option = load_review_schedule(project_id, cycle_id)

    print(f"📊 Gantt Chart Data Sent to Dash:\n{df}")

    return generate_gantt_chart(df, project_name, review_option), f"{project_name} - Cycle {review_option} Review Schedule", dropdown_options


# ✅ Callback to update review date when clicking on the Gantt chart
@app.callback(
    Output("output-message", "children"),
    Input("gantt-chart", "clickData"),
    State("project-dropdown", "value"),
    State("cycle-dropdown", "value")
)
def update_review(click_data, project_id, cycle_id):
    if click_data and "points" in click_data:
        point = click_data["points"][0]
        df, _, _, _ = load_review_schedule(project_id, cycle_id)
        schedule_id = df.iloc[point["pointIndex"]]["schedule_id"]
        new_date = df.iloc[point["pointIndex"]]["review_date"]

        update_review_date(schedule_id, new_date)
        adjust_future_tasks(schedule_id, new_date, project_id, cycle_id)

        return f"Updated Review {schedule_id} to {new_date}, and adjusted future reviews!"
    return "Click a review task to update review dates!"

# ✅ Callback to delete a review task
@app.callback(
    Output("output-message", "children"),
    Input("delete-button", "n_clicks"),
    State("delete-review-dropdown", "value")
)
def delete_review(n_clicks, schedule_id):
    if n_clicks > 0 and schedule_id:
        delete_review_task(schedule_id)
        return f"Review {schedule_id} deleted successfully!"
    return ""

# ✅ Function to launch the Gantt chart in a pop-up
def launch_gantt_chart(project_id, cycle_id):
    """Run Dash in a separate thread and open in a web pop-up with selected project and cycle."""

    def run_dash():
        print(f"Launching Gantt Chart for Project {project_id}, Cycle {cycle_id}")  # Debugging
        app.run_server(debug=False, use_reloader=False, port=8050)

    # ✅ Set global variables to pass project/cycle ID
    global DASH_PROJECT_ID, DASH_CYCLE_ID
    DASH_PROJECT_ID = project_id
    DASH_CYCLE_ID = cycle_id

    # ✅ Start only ONE Dash thread if not already running
    if not hasattr(launch_gantt_chart, "thread") or not launch_gantt_chart.thread.is_alive():
        launch_gantt_chart.thread = threading.Thread(target=run_dash, daemon=True)
        launch_gantt_chart.thread.start()



# ✅ Ensure this runs only when the script is executed directly
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
