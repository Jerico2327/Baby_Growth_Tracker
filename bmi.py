import os

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField, FloatField
from wtforms.validators import DataRequired
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from google import genai


class UserInput(FlaskForm):

    """ Generates the form to be filled by the user """

    gender = SelectField("",
                         choices=[("", "Gender"), ("boy", "Boy"), ("girl", "Girl")],
                         validators=[DataRequired()])
    birthdate = DateField("",
                          render_kw={"placeholder": "dd/mm/yyyy"},
                          validators=[DataRequired()])
    weight = FloatField("",
                        render_kw={"placeholder": "Weight (kg)"},
                        validators=[DataRequired(message="Numeric input is required.")])
    height = FloatField("",
                        render_kw={"placeholder": "Height (m)"},
                        validators=[DataRequired(message="Numeric input is required.")])
    submit = SubmitField("Calculate", render_kw={"class": "w-75"})


class Calculate:

    """ Performs the calculations needed to get the BMI. """

    @staticmethod
    def bmi(weight, height):
        bmi = round(float(weight) / (float(height)**2), 2)
        return bmi

    @staticmethod
    def age(bdate):

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

    def get_percentile(self, age, bmi):

        """ Returns the boundaries where the calculated BMI lies. """

        lower_percentile = None
        upper_percentile = None
        limits = []
        new_df = self.percentile_df.copy().set_index("Month")
        row = new_df.loc[age['month'], new_df.columns[3:]]

        for key, value in row.items():
            value = float(value)
            if bmi >= value:
                lower_percentile = key

            if bmi <= value:
                upper_percentile = key

        if lower_percentile is not None:
            limits.append(lower_percentile)
        if upper_percentile is not None:
            limits.append(upper_percentile)

        return limits

    def get_zscore(self, age, bmi):

        """ The z-score will be provided to the AI for a more reliable evaluation. """

        zscore_df = self.zscore_df.copy().set_index("Month")
        z_columns = zscore_df.columns[3:]
        row = zscore_df.loc[age['month'], z_columns]

        for key, val in row.items():
            if bmi >= val:
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
    def analyze(df=None, bmi=None, gender=None, weight=None, height=None, age=None, z_score=0):
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        try:
            prompt = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"In 2-3 sentences, give a brief recommendation/evaluation about a baby {gender} who"
                         f"has a BMI of {bmi} at the age of {age} months"
                         f"in terms of z-score {z_score}."
            )
        except Exception as e:
            print(f"Exception error: {e}")
            return "Recommendation is currently unavailable."
        else:
            print("AI API Called")
            return prompt.text
