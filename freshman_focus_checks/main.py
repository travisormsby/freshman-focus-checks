from io import StringIO
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import csv
import requests
import sys


# Standard url for accessing Google Sheets as csv
def get_url(key, sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{key}/gviz/tq?tqx=out:csv&sheet={sheet_name}"  # noqa


# Access csv as nested list
def access_data(url, header_row):
    response = requests.get(url)
    f = StringIO(response.text)
    reader = csv.reader(f)
    if header_row:
        next(reader)
    return [row for row in reader]


# Calculate paycheck values from submitted score
def calculations(row, points_per_day, pay_rate, deduction_rates):
    date = datetime.now().strftime("%x")
    name = row[2]
    score = float(row[3])
    response = {
        "date": date,
        "name": name,
        "payrate": pay_rate,
        "hours": round(score / points_per_day, 2),
    }
    response["gross"] = round(response["hours"] * pay_rate, 2)
    response["deductions"] = {}
    for deduction, rate in deduction_rates.items():
        response["deductions"][deduction] = round(response["gross"] * rate, 2)
    response["total_deductions"] = sum(response["deductions"].values())
    response["net"] = response["gross"] - response["total_deductions"]

    return response


# Write data to the html template
def write_checks(jinja_context):
    environment = Environment(loader=FileSystemLoader("templates/"))
    results_filename = "checks/checks.html"
    results_template = environment.get_template("check_template.html")
    with open(results_filename, mode="w", encoding="utf-8") as results:
        results.write(results_template.render(jinja_context))


if __name__ == "__main__":

    # Input values. These are changeable.
    key = sys.argv[1]
    sheet_name = sys.argv[2]
    points_per_day = 20
    pay_rate = 18.50
    deduction_rates = {
        "Federal Income Tax": 0.12,
        "Medicare": 0.0145,
        "Social Security": 0.062,
        "Minnesota State Income Tax": 0.0535,
        "Insurance": 0.0961,
        "401(k)": 0.035,
        "Union Dues": 0.015,
    }

    url = get_url(key, sheet_name)
    data = access_data(url, header_row=True)
    jinja_context = {
        "students": [
            calculations(row, points_per_day, pay_rate, deduction_rates) for row in data
        ]
    }
    write_checks(jinja_context)
