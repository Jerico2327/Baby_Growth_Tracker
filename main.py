import os
from flask import Flask, render_template,request
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

from pprint import pprint
@app.route('/', methods=['GET', 'POST'])
def home():
    form = UserInput()

    if form.validate_on_submit():

        if form.gender.data == "boy":
            bmi_ref = BMIReference(BOY_DF)
        else:
            bmi_ref = BMIReference(GIRL_DF)

        age = Calculate.age(form.birthdate.data)
        bmi = Calculate.bmi(form.weight.data, form.height.data)
        new_data = {
            "gender": form.gender.data,
            "age": age,
            "weight": form.weight.data,
            "height": form.height.data,
            "bmi": bmi,
            "df": bmi_ref.df,
            "percentile": bmi_ref.get_percentile(age, bmi)
        }
        ai_output = AIAnalysis.analyze(
            bmi=new_data['bmi'],
            age=new_data['age']['month'])
        new_data['ai_text'] = ai_output
        fig = create_figure(new_data)

        return render_template("result.html", new_data=new_data, fig=fig)
    elif request.method == "POST":

        handle_excel_file_as_input(request.files.get('excel_file'))

    return render_template("index.html", form=form)


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





def create_figure(data):

    fig = px.line(
        data['df'],
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
