from flask import Flask, render_template
from dashboard import dashboard

app = Flask(__name__)
app.register_blueprint(dashboard)


@app.route("/", methods=["get", "post"])
def dashboard():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)