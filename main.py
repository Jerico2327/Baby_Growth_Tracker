import os

from flask import Flask, render_template, redirect, url_for, session
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

""" Excel files containing the WHO Data """
BOY_PERCENTILE_DF = pd.read_csv("data/tab_bmi_boys_p_0_2.csv")
BOY_ZSCORE_DF = pd.read_excel("data/bmi_boys_0-to-2-years_zcores.xlsx", engine="openpyxl")
GIRL_PERCENTILE_DF = pd.read_csv("data/tab_bmi_girls_p_0_2.csv")
GIRL_ZSCORE_DF = pd.read_excel("data/bmi_girls_0-to-2-years_zscores.xlsx", engine="openpyxl")


@app.route('/', methods=['GET', 'POST'])
def home():

    """ Calculate the BMI based on the input data by the user. """

    form = UserInput()

    if form.validate_on_submit():
        age = Calculate.age(form.birthdate.data)
        print(f'age: {age["month"]}')
        if age['month'] > 24:
            return render_template("error.html")

        gender = form.gender.data
        weight = form.weight.data
        height = form.height.data
        bmi = Calculate.bmi(weight, height)

        if gender == "boy":
            bmi_ref = BMIReference(BOY_PERCENTILE_DF, BOY_ZSCORE_DF)
        else:
            bmi_ref = BMIReference(GIRL_PERCENTILE_DF, GIRL_ZSCORE_DF)

        new_data = {"gender": gender, "age": age, "weight": weight, "height": height, "bmi": bmi}

        new_data['percentile'] = bmi_ref.get_percentile(age=new_data['age'], bmi=new_data['bmi'])
        new_data['zscore'] = bmi_ref.get_zscore(age=new_data['age'], bmi=new_data['bmi'])

        """ This will call the Gemini model from the custom class to get evaluation of the BMI. """
        ai_output = AIAnalysis.analyze(
            bmi=new_data['bmi'],
            age=new_data['age']['month'],
            z_score=new_data['zscore']
        )

        new_data['ai_output'] = ai_output

        """ Store the session data to avoid multiple calls to Gemini AI if already called once. """
        session['session_data'] = new_data

        return redirect(url_for('result'))

    return render_template("index.html", form=form)


@app.route("/result", methods=['GET', 'POST'])
def result():

    data = session.get("session_data")

    """ 
        Instead of passing the whole BMI dataframe to this router, 
        Initialize another object bmi_ref to get a dataframe and plot the figure using create_figure()
    """

    if data['gender'] == "boy":
        bmi_ref = BMIReference(BOY_PERCENTILE_DF, BOY_ZSCORE_DF)
    else:
        bmi_ref = BMIReference(GIRL_PERCENTILE_DF, GIRL_ZSCORE_DF)
    #
    # data['percentile'] = bmi_ref.get_percentile(age=data['age'], bmi=data['bmi'])
    # data['zscore'] = bmi_ref.get_zscore(age=data['age'], bmi=data['bmi'])
    # pprint(data)

    fig = create_figure(data, bmi_ref.percentile_df)

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
        y=[data['bmi']],
        name="Calculated BMI",
        hovertemplate=(
            "BMI: %{y:.2f} <br>"
        )
    )
    fig.update_layout(
        yaxis_title="Percentile"
    )
    fig.layout.legend.title.text = "Percentiles"
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(dtick=1)

    """ Update the hover data of each line trace """
    fig.for_each_trace(
        lambda trace: trace.update(
            hovertemplate=(
                f"Percentile: {trace.name}<br>"
                "Month: %{x}<br>"
                "BMI: %{y:.2f}<extra></extra>"
            )
        ),
        selector=lambda trace: trace.name.startswith("P")
    )
    fig.update_layout(
        plot_bgcolor="#E3F5E1"
    )
    fig_div = fig.to_html(full_html=False)
    return fig_div


if __name__ == "__main__":
    app.run(port=5002, debug=True)
