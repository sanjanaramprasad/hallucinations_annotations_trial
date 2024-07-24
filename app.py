from typing import Dict, Tuple, Sequence

from flask import Flask, jsonify, request, render_template, url_for, redirect, send_from_directory, flash
import json 
import requests
import re
import sqlalchemy
from sqlalchemy import text, create_engine, Index, MetaData, Table, select, exists
from sqlalchemy.sql import and_
from nltk.tokenize import sent_tokenize
from random import shuffle
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import math
import spacy
import os
import nltk
nltk.download('punkt')
nlp = spacy.load('en_core_web_sm')

application = Flask(__name__)
application.secret_key = 'super_secret_key' 

db_engine = sqlalchemy.create_engine('postgresql://u38ot3voqlb8of:p9ee14081ae1d13ffb707b10ddc331c8191f057d2be74b53921911da9e426ca4c@cd3vj4tb0qabuf.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dgks84evs3khk')

metadata = MetaData(bind=db_engine)
metadata.reflect()
print(metadata)
model_summaries = metadata.tables['model_summaries']
label = metadata.tables['label']

n_labels_per_doc = 6
n_docs = 5

login_manager = LoginManager()
login_manager.init_app(application)

# User class example
class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

def get_users():
    users = {
        "sanjana": User(1, "sanjana", "sanjana"),
        "elisa": User(2, "elisa", "elisa"),
        "pranav": User(3, "pranav", "pranav"),
        "rachel_usher": User(4, "rachel_usher", "rachel_usher")
    }
    return users

@login_manager.user_loader
def load_user(username):
    return get_users().get(username)

@login_required
@application.route('/')
def hello():
    return redirect(url_for('login'))

@application.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return next()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = load_user(username)
        
        if user is not None and user.check_password(password):
            login_user(user)
            return next()
        
        # flash('Invalid username or password')
    
    return render_template('login.html')

@login_required
@application.route('/next')
def next():
    username = current_user.username 
    model_summaries = metadata.tables['model_summaries']
    connection = db_engine.connect()
    query = select([model_summaries.c.docid])
    result = connection.execute(query)
    ids = [row[0] for row in result]

    label_table = metadata.tables['label']
    query_annotated_ids = select([label_table.c.docid]).where(label_table.c.user_id == username).distinct()
    result_annotated_ids = connection.execute(query_annotated_ids)
    annotated_ids = {row[0] for row in result_annotated_ids}

    connection.close()
    return render_template('annotate.html', ids=ids, annotated_ids=annotated_ids)

# @application.route('/annotate_action', methods=['POST'])
# @login_required
# def annotate_action():
#     selected_id = request.form['id']

#     model_summaries = metadata.tables['model_summaries']

#     with db_engine.connect() as connection:
#         query = sqlalchemy.select([model_summaries]).where(model_summaries.c.docid == selected_id)
#         result = connection.execute(query).fetchone()
#         print(result)
#         source = result['source']
#         summary = result['summary']
#         model = result['model']
#         origin = result['origin']
#         benchmark_dataset_name = result['benchmark_dataset_name']
#     return render_template('annotation_detail.html',
#                             source=source,
#                             summary=summary,
#                             model=model,
#                             origin=origin,
#                             benchmark_dataset_name=benchmark_dataset_name,
#                             docid=selected_id)

@application.route('/annotate_action', methods=['POST'])
@login_required
def annotate_action():
    selected_id = request.form['id']
    username = current_user.username 
    model_summaries = metadata.tables['model_summaries']

    with db_engine.connect() as connection:
        # Fetch the document details
        query = sqlalchemy.select([model_summaries]).where(model_summaries.c.docid == selected_id)
        result = connection.execute(query).fetchone()
        source = result['source']
        summary = result['summary']
        model = result['model']
        origin = result['origin']
        benchmark_dataset_name = result['benchmark_dataset_name']

        # Fetch existing annotations for the selected ID
        label_table = metadata.tables['label']
        query_annotations = sqlalchemy.select([label_table]).where(
                                and_(
                                    label_table.c.docid == selected_id,
                                    label_table.c.user_id == username
                                )
                            )
        annotations = []
        for row in connection.execute(query_annotations):
            annotation = {
                'nonfactual_span': row['nonfactual_span'],
                'error_type': row['error_type'],
                'mistake_severity': row['mistake_severity'],
                'inference_likelihood': row['inference_likelihood'],
                'inference_knowledge': row['inference_knowledge']
            }
            annotations.append(annotation)
        # annotations = str(annotations)
        print('ANN', annotations, type(annotations))
        source_sentences = sent_tokenize(source)
        source_sentences = [each.capitalize() for each in source_sentences]
        source = "\n".join(source_sentences).strip()
        print(source)
        return render_template('annotation_detail.html',
                           source=source,
                           summary=summary,
                           model=model,
                           origin=origin,
                           benchmark_dataset_name=benchmark_dataset_name,
                           docid=selected_id,
                           annotations=annotations)


@application.route('/save_annotations', methods=['POST'])
@login_required
def save_annotations():
    data = request.get_json()
    username = current_user.username
    print("Data received:", data)
    with db_engine.connect() as connection:
        label_table = metadata.tables['label']
        query_annotated = sqlalchemy.select([label_table]).where(
                                and_(
                                    model_summaries.c.docid == data['docid'],
                                    label_table.c.user_id == username
                                )
                            )
        existing_annotations = connection.execute(query_annotated).fetchall()
        attempt_number = 1 if existing_annotations else 0
        if existing_annotations:
            delete_stmt = label_table.delete().where(
                and_(
                    label_table.c.docid == data['docid'],
                    label_table.c.user_id == username
                )
            )
            connection.execute(delete_stmt)
            print(f"Deleted existing")
        # Insert annotations into the label table
        # with db_engine.connect() as connection:
        if not data['annotations']:
            try:
                stmt = label.insert().values(
                    user_id=username,
                    docid=data['docid'],
                    source=data['source'],
                    summary=data['summary'],
                    model=data['model'],
                    benchmark_dataset_name=data['benchmark_dataset_name'],
                    origin=data['origin'],
                    nonfactual_span=None,
                    error_type=None,
                    mistake_severity=None,
                    inference_likelihood=None,
                    inference_knowledge=None,
                    attempt_number = 1

                )
                connection.execute(stmt)
            except KeyError as e:
                print(f"KeyError: Missing key {e} in annotation {annotation}")

        else:
            for annotation in data['annotations']:
                print("Annotation received:", annotation)
                try:
                    stmt = label.insert().values(
                        user_id=username,
                        docid=data['docid'],
                        source=data['source'],
                        summary=data['summary'],
                        model=data['model'],
                        benchmark_dataset_name=data['benchmark_dataset_name'],
                        origin=data['origin'],
                        nonfactual_span=annotation['nonfactual_span'],
                        error_type=annotation['error_type'],
                        mistake_severity=annotation['mistake_severity'],
                        inference_likelihood=annotation['inference_likelihood'],
                        inference_knowledge=annotation['inference_knowledge'],
                        attempt_number = 1

                    )
                    connection.execute(stmt)
                except KeyError as e:
                    print(f"KeyError: Missing key {e} in annotation {annotation}")

    return jsonify({"success": True})

if __name__ == "__main__":
    application.run(debug = True)
