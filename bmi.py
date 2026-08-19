from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, DateField, FloatField
from wtforms.validators import DataRequired
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt


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

        new_df = self.df.copy().set_index("Month")
        row = new_df.loc[age['month'], new_df.columns[3:]]

        for key, value in row.items():
            value = float(value)
            if bmi >= value:
                lower_percentile = key
            if bmi <= value:
                upper_percentile = key

        limits = [lower_percentile, upper_percentile]
        print(limits)
        return limits


