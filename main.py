import os
from app import create_app, db

app = create_app()

# This is the "Secret Sauce" for Railway
with app.app_context():
    db.create_all() # This creates your tables automatically on the cloud

if __name__ == '__main__':
    # Use the PORT variable Railway gives you, or 5000 for local VS Code
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)