from flask import Flask
from flask import render_template

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
    )


@app.route("/questionnaire", methods=["GET"])
def questionnaire():
    """
    问卷主页
    """
    return render_template("questionnaire.html")


if __name__ in "__main__":
    app.run(
        host="0.0.0.0",
        port="8080",
        debug=True
    )