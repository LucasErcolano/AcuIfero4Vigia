import os
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.orm import sessionmaker

# We'll use two databases: edge.db for local state, central.db for sync simulation
EDGE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/edge.db"))
CENTRAL_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/central.db"))

edge_engine = create_engine(f"sqlite:///{EDGE_DB_PATH}", echo=False)
central_engine = create_engine(f"sqlite:///{CENTRAL_DB_PATH}", echo=False)

def init_db():
    SQLModel.metadata.create_all(edge_engine)
    SQLModel.metadata.create_all(central_engine)

def get_session():
    with Session(edge_engine) as session:
        yield session

def get_central_session():
    with Session(central_engine) as session:
        yield session
