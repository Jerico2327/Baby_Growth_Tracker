import os

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField, FloatField
from wtforms.validators import DataRequired, Optional
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from google import genai
import json
import time

class UserInput(FlaskForm):

    """ Generates the form to be filled by the user """

    gender = SelectField("",
                         choices=[("", "Gender"), ("boy", "Boy"), ("girl", "Girl")],
                         validators=[DataRequired()])
    birthdate = DateField("",
                          render_kw={"placeholder": "dd/mm/yyyy"},
                          validators=[DataRequired()])
    birth_weight = FloatField("",
                              render_kw={"placeholder": "Birth weight (kg)"},
                              validators=[Optional()]
                              )
    birth_height = FloatField("",
                              render_kw={"placeholder": "Birth height (m)"},
                              validators=[Optional()]
                              )
    weight = FloatField("",
                        render_kw={"placeholder": "Current weight (kg)"},
                        validators=[DataRequired(message="Numeric input is required.")])
    height = FloatField("",
                        render_kw={"placeholder": "Current height (m)"},
                        validators=[DataRequired(message="Numeric input is required.")])
    submit = SubmitField("Calculate", render_kw={"class": "w-75"})


class Calculate:

    """ Perform the calculations needed to get the BMI. """

    @staticmethod
    def bmi(age, weight, height, birth_weight, birth_height) -> dict:

        bmi_collections = {}

        if birth_height and birth_weight:
            birth_bmi = round(float(birth_weight)/(float(birth_height)**2), 2)
            bmi_collections = {
                0: birth_bmi
            }
        bmi = round(float(weight) / (float(height) ** 2), 2)
        bmi_collections[age['month']] = bmi

        return bmi_collections

    @staticmethod
    def age(bdate) -> dict:

        diff = relativedelta(dt.now(), bdate)
        age = {
            "year": diff.years,
            "month": diff.years * 12 + diff.months,
            "day": diff.days
        }
        return age


class BMIReference:

    """
        Serves as the reference for WHO data.
        This class uses the Dataframes downloaded from the WHO website, mainly the percentile and z-score.
        https://www.who.int/toolkits/child-growth-standards/standards/body-mass-index-for-age-bmi-for-age
    """

    def __init__(self, percentile_df, zscore_df):
        self.percentile_df = percentile_df
        self.zscore_df = zscore_df

    def get_percentile(self, age, bmi) -> list:

        """ Returns the boundaries where the calculated BMI lies. """
        # print(bmi)
        lower_percentile = None
        upper_percentile = None
        limits = []
        new_df = self.percentile_df.copy().set_index("Month")
        row = new_df.loc[age['month'], new_df.columns[3:]]

        for key, value in row.items():
            value = float(value)
            for m, b in bmi.items():
                if bmi[m] >= value:
                    lower_percentile = key

                if bmi[m] <= value:
                    upper_percentile = key

        if lower_percentile is not None:
            limits.append(lower_percentile)
        if upper_percentile is not None:
            limits.append(upper_percentile)

        return limits

    def get_zscore(self, age, bmi) -> int:

        """ The z-score will be provided to the AI for a more reliable evaluation. """

        zscore_df = self.zscore_df.copy().set_index("Month")
        z_columns = zscore_df.columns[3:]
        row = zscore_df.loc[age['month'], z_columns]

        for key, val in row.items():
            for m, b in bmi.items():
                if bmi[m] >= val:
                    if key == "SD3neg":
                        zscore = -3
                    elif key == "SD2neg":
                        zscore = -2
                    elif key == "SD1neg":
                        zscore = -1
                    elif key == "SD0":
                        zscore = 0
                    elif key == "SD1":
                        zscore = 1
                    elif key == "SD2":
                        zscore = 2
                    elif key == "SD3":
                        zscore = 3
        return zscore


class AIAnalysis:

    """ Handles the AI interaction using the baby's input and calculated data. """

    @staticmethod
    def analyze(percentile, bmi, gender, age, z_score) -> str:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        for attempt in range(3):
            try:
                bmi = json.dumps(bmi)
                prompt = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"Gender: {gender}"
                             # f"Age: {age}"
                             f"BMI pattern (month: bmi): {bmi}"
                             f"WHO percentile: {percentile}"
                             f"WHO Z-score: {z_score}"
                             f"Give a brief 2 sentence-evaluation of bmi vs the WHO data"
                )
            except Exception as e:
                print(f"Exception error: {e}")
                print(f"attempt: {attempt}")
                if attempt < 2:
                    time.sleep(2 ** attempt + 1)
                    continue
                return "Currently unavailable"
            else:
                print("AI API Called")
                return prompt.text
