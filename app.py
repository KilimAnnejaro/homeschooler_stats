from flask import Flask, render_template
import json
import plotly
import plotly.express as px
import pandas as pd
import sqlite3

app = Flask(__name__,template_folder=".")

def helper():
    con = sqlite3.connect("tutorial.db")

    cur = con.cursor()

    cur.execute("drop table if exists states")
    cur.execute("CREATE TABLE if not exists states(abbreviation,name type unique)")
    cur.execute("drop table if exists homeschoolers")
    cur.execute("create table if not exists homeschoolers(state,year,homeschool_students)")
    cur.execute("drop table if exists public_schoolers")
    cur.execute("create table if not exists public_schoolers(state,year,public_school_students)")

    con.commit()

    data = pd.read_csv(
        'https://raw.githubusercontent.com/washingtonpost/data_home_schooling/refs/heads/main/home_school_state.csv')
    other_data = pd.read_excel('https://nces.ed.gov/programs/digest/d23/tables/xls/tabn203.20.xlsx', header=2)
    # other_data = other_data[5:]
    other_data = other_data.drop([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72])
    other_data = other_data.drop(['Projected percent change in total enrollment, 2022 to 2031',
                                  'Percent change in total enrollment, 2017 to 2022'], axis=1)
    other_data = pd.melt(other_data, value_vars=other_data.columns, id_vars=['Region, state, and jurisdiction'])

    other_data['variable'] = other_data['variable'].apply(
        lambda x: str(x)[5:].strip() + '-' + str(int(str(x)[7:9].strip()) + 1))
    other_data['Region, state, and jurisdiction'] = other_data['Region, state, and jurisdiction'].apply(
        lambda x: str(x).upper().strip())
    other_data.rename(
        columns={'Region, state, and jurisdiction': 'state', 'variable': 'year', 'value': 'public_school_students'},
        inplace=True)
    states = [("AL", "ALABAMA"), ("AK", "ALASKA"), ("AZ", "ARIZONA"), ("AR", "ARKANSAS"), ("CA", "CALIFORNIA"),
              ("CO", "COLORADO"), (
                  "CT", "CONNECTICUT"), ("DE", "DELAWARE"), ("FL", "FLORIDA"), ("GA", "GEORGIA"), ("HI", "HAWAII"),
              ("ID", "IDAHO"), (
                  "IL", "ILLINOIS"), ("IN", "INDIANA"), ("IA", "IOWA"), ("KS", "KANSAS"), ("KY", "KENTUCKY"),
              ("LA", "LOUISIANA"), (
                  "ME", "MAINE"), ("MD", "MARYLAND"), ("MA", "MASSACHUSETTS"), ("MI", "MICHIGAN"), ("MN", "MINNESOTA"),
              (
                  "MS", "MISSISSIPPI"), ("MO", "MISSOURI"), ("MT", "MONTANA"), ("NE", "NEBRASKA"), ("NV", "NEVADA"), (
                  "NH", "NEW HAMPSHIRE"), ("NJ", "NEW JERSEY"), ("NM", "NEW MEXICO"), ("NY", "NEW YORK"),
              ("NC", "NORTH CAROLINA"), (
                  "ND", "NORTH DAKOTA"), ("OH", "OHIO"), ("OK", "OKLAHOMA"), ("OR", "OREGON"), ("PA", "PENNSYLVANIA"), (
                  "RI", "RHODE ISLAND"), ("SC", "SOUTH CAROLINA"), ("SD", "SOUTH DAKOTA"), ("TN", "TENNESSEE"),
              ("TX", "TEXAS"), (
                  "UT", "UTAH"), ("VT", "VERMONT"), ("VA", "VIRGINIA"), ("WA", "WASHINGTON"), ("WV", "WEST VIRGINIA"), (
                  "WI", "WISCONSIN"), (
                  "WY", "WYOMING"), ("DC", "DISTRICT OF COLUMBIA")]
    cur.executemany("INSERT INTO states VALUES(?,?)", states)
    data.to_sql('homeschoolers', con, if_exists='replace', index=False)
    other_data.to_sql('public_schoolers', con, if_exists='replace', index=False)
    con.commit()  # Remember to commit the transaction after executing INSERT.
    cur.execute("drop view if exists student_percentages")
    cur.execute(
        "create view if not exists student_percentages as SELECT states.name,abbreviation,homeschoolers.year,homeschool_students,public_school_students,homeschool_students/(homeschool_students+public_school_students) as percent_homeschooled from homeschoolers join states on homeschoolers.state=states.name inner join public_schoolers on public_schoolers.state=homeschoolers.state and public_schoolers.year=homeschoolers.year")

    return pd.read_sql_query("select * from student_percentages", con)



@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/homeschoolers")
def display_homeschoolers_map():

    # Import data from GitHub
    data = pd.read_csv(
        'https://raw.githubusercontent.com/washingtonpost/data_home_schooling/refs/heads/main/home_school_state.csv')

    # Transform data converting state names to states
    states = {"AL": "ALABAMA", "AK": "ALASKA", "AZ": "ARIZONA", "AR": "ARKANSAS", "CA": "CALIFORNIA", "CO": "COLORADO",
              "CT": "CONNECTICUT", "DE": "DELAWARE", "FL": "FLORIDA", "GA": "GEORGIA", "HI": "HAWAII", "ID": "IDAHO",
              "IL": "ILLINOIS", "IN": "INDIANA", "IA": "IOWA", "KS": "KANSAS", "KY": "KENTUCKY", "LA": "LOUISIANA",
              "ME": "MAINE", "MD": "MARYLAND", "MA": "MASSACHUSETTS", "MI": "MICHIGAN", "MN": "MINNESOTA",
              "MS": "MISSISSIPPI", "MO": "MISSOURI", "MT": "MONTANA", "NE": "NEBRASKA", "NV": "NEVADA",
              "NH": "NEW HAMPSHIRE", "NJ": "NEW JERSEY", "NM": "NEW MEXICO", "NY": "NEW YORK", "NC": "NORTH CAROLINA",
              "ND": "NORTH DAKOTA", "OH": "OHIO", "OK": "OKLAHOMA", "OR": "OREGON", "PA": "PENNSYLVANIA",
              "RI": "RHODE ISLAND", "SC": "SOUTH CAROLINA", "SD": "SOUTH DAKOTA", "TN": "TENNESSEE", "TX": "TEXAS",
              "UT": "UTAH", "VT": "VERMONT", "VA": "VIRGINIA", "WA": "WASHINGTON", "WV": "WEST VIRGINIA",
              "WI": "WISCONSIN",
              "WY": "WYOMING", "DC": "DISTRICT OF COLUMBIA"}

    states_inv = {v: k for k, v in states.items()}

    data['state'] = data['state'].apply(lambda abbrev: states_inv[abbrev])
    other_data = helper()
    # Create basic choropleth map
    fig = px.choropleth(other_data, locations='abbreviation', locationmode='USA-states', color='percent_homeschooled',
                        hover_name='name',
                        projection='albers usa', animation_frame='year',
                        title='Homeschooled Student Percentage By State')

    # Convert the figure to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', graphJSON=graphJSON)

if __name__ == "__main__":
    app.run(debug=True)