import os
from app import create_app
from models.models import db, User, Event, EventRegistration, EventRating
from sqlalchemy import inspect

    # Create the Flask application instance
app = create_app()

    # Ensure we are operating within the application context
with app.app_context():
    print("Attempting to inspect database...")
    try:
            # Get the inspector object for the current database engine
            inspector = inspect(db.engine)

            # Get and print all table names
            table_names = inspector.get_table_names()
            if table_names:
                print("\nTables found in the database:")
                for table_name in table_names:
                    print(f"- {table_name}")
            else:
                print("\nNo tables found in the database.")

            # Check if 'user' table exists and print its columns
            if 'user' in table_names:
                print("\nColumns in the 'user' table:")
                columns = inspector.get_columns('user')
                for column in columns:
                    print(f"- {column['name']} ({column['type']}) {'(Primary Key)' if column['primary_key'] else ''}")
            else:
                print("\n'user' table not found in the database.")

    except Exception as e:
            print(f"\nAn error occurred while inspecting the database: {e}")

    print("\nDatabase inspection complete.")
    