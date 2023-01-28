from app.app import app, server
from app.layout import layout

app.layout = layout

if __name__ == "__main__":
    app.run_server(debug=True)