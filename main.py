import os
from pprint import pprint

from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5
import plotly.express as px
from google import genai

from bmi import UserInput, Calculate, BMIReference, AIAnalysis

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
bootstrap = Bootstrap5(app)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

BOY_DF = pd.read_csv("data/tab_bmi_boys_p_0_2.csv")
GIRL_DF = pd.read_csv("data/tab_bmi_girls_p_0_2.csv")


@app.route('/', methods=['GET', 'POST'])
def home():
    """ Created this form object just to render in the index.html """
    form = UserInput()
    if form.validate_on_submit():
        age = Calculate.age(form.birthdate.data)
        gender = form.gender.data
        weight = form.weight.data
        height = form.height.data
        bmi = Calculate.bmi(weight, height)

        if gender == "boy":
            bmi_ref = BMIReference(BOY_DF)
        else:
            bmi_ref = BMIReference(GIRL_DF)

        new_data = {"gender": gender, "age": age, "weight": weight, "height": height, "bmi": bmi,
                    "percentile": bmi_ref.get_percentile(age, bmi)}

        ai_output = AIAnalysis.analyze(
            bmi=new_data['bmi'],
            age=new_data['age']['month']
        )

        new_data['ai_output'] = ai_output

        session['session_data'] = new_data
        return redirect(url_for('result'))
    return render_template("index.html", form=form)


@app.route("/result", methods=['GET', 'POST'])
def result():

    data = session.get("session_data")

    if data['gender'] == "boy":
        bmi_ref = BMIReference(BOY_DF)
    else:
        bmi_ref = BMIReference(GIRL_DF)

    data['percentile'] = bmi_ref.get_percentile(data['age'], data['bmi'])
    pprint(data)

    fig = create_figure(data, bmi_ref.df)

    return render_template('result.html', new_data=data, fig=fig)



def handle_excel_file_as_input(file):
    # user_input = None
    # if file.filename.endswith("csv"):
    #     user_input = pd.read_csv(file)
    # elif file.filename.endswith((".xlsm", ".xls", ".ods", ".xlsb")):
    #     user_input = pd.read_excel(file)
    #
    # if "month" in user_input.columns:
    #     print("month")
    pass


def create_figure(data, df):
    fig = px.line(
        df,
        title=f"BMI Percentile for 0-to-2-year-old-{data['gender']} ",
        x="Month",
        y=data['percentile']
    )
    fig.add_scatter(
        x=[data['age']['month']],
        y=[data['bmi']]
    )
    fig.update_layout(
        yaxis_title="Percentile"
    )
    fig.layout.legend.title.text = "Percentiles"
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(dtick=1)
    fig_div = fig.to_html(full_html=False)
    return fig_div


if __name__ == "__main__":
    app.run(port=5002, debug=True)
