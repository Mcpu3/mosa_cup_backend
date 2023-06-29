import os
import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_CONNECTION_STRING = urllib.parse.quote_plus("Driver={ODBC Driver 18 for SQL Server};Server=tcp:mosa-cup-backend.database.windows.net,1433;Database=mosa_cup_backend;Uid=mosa_cup_backend;Pwd={%s};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;" % DATABASE_PASSWORD)
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={DATABASE_CONNECTION_STRING}"

engine = create_engine(DATABASE_URL)
LocalSession = sessionmaker(engine)

Base = declarative_base()
