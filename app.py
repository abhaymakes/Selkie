from flask import Flask, render_template
from dashboard import dashboard
from task import task

app = Flask(__name__)
app.register_blueprint(dashboard)
app.register_blueprint(task)


@app.route("/", methods=["get", "post"])
def home():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)