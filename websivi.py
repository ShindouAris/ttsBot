from flask import Flask
app = Flask(__name__)

@app.route('/')
def getapp() -> str:
    return "Hello World!"

def run_application(port=10000) -> None:
    app.run(port=port)