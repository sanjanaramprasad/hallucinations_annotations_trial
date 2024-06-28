from typing import Dict, Tuple, Sequence

from flask import Flask, jsonify, request, render_template, url_for, redirect, send_from_directory, flash
import json 
import re
import sqlalchemy
from sqlalchemy import text, create_engine, Index, MetaData, Table, select, exists
from sqlalchemy.sql import and_

from random import shuffle
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import math
import spacy
# import psycopg2
import os
nlp = spacy.load('en_core_web_sm')

application = Flask(__name__)



def init_database_connection(postgres_link):
    db_engine = sqlalchemy.create_engine(postgres_link)

    metadata = MetaData(bind=db_engine)
    metadata.reflect()
    print(metadata)
    generated_summaries = metadata.tables['generated_summaries']
    label = metadata.tables['label']
    return db_engine, metadata


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080)