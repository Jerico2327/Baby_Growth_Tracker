import os

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, DateField, FloatField
from wtforms.validators import DataRequired
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from google import genai


class UserInput(FlaskForm):
    gender = SelectField("Gender",
                         choices=[("", ""), ("boy", "Male"), ("girl", "Female")],
                         validators=[DataRequired()])
    birthdate = DateField("Birthdate", validators=[DataRequired()])
    weight = FloatField("Weight (kg)", validators=[DataRequired(message="Numeric input is required.")])
    height = FloatField("Height (m)", validators=[DataRequired(message="Numeric input is required.")])
    submit = SubmitField("Get BMI")


class Calculate:

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

    def __init__(self, df):
        self.df = df

    def get_percentile(self, age, bmi):

        lower_percentile = None
        upper_percentile = None
        limits = []
        new_df = self.df.copy().set_index("Month")
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


class AIAnalysis:

    # def __init__(self, bmi, gender, weight, height, age):
    #     self.bmi = bmi
    #     self.gender = gender
    #     self.weight = weight
    #     self.height = height
    #     self.age = age
    #

    @staticmethod
    def analyze(df=None, bmi=None, gender=None, weight=None, height=None, age=None):
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=f"In 2-3 sentence, give a recommendation about a baby {gender} who"
                     f"has a BMI of {bmi} at the age of {age} months"
                     f"in terms of z-score and bmi category."
        )

        return prompt.text
