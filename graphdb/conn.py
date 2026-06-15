"""Neo4j 접속 단일 진입점. .env 의 NEO4J_* 를 읽어 드라이버를 만든다."""
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_driver():
    uri = os.environ["NEO4J_URI"]
    auth = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    return GraphDatabase.driver(uri, auth=auth)
