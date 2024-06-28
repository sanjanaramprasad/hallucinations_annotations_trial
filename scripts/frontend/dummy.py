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
# import flask_monitoringdashboard as dashboard

#app = Flask(__name__)
application = Flask(__name__)
# dashboard.bind(app)

application.secret_key = 'your_secret_key_here'




#directory = '/home/sanjana/explainable_factual_evaluation/datasets/short_dialogue/model_generated/annotations'
# cwd = os.getcwd()
# directory = f"{cwd}/data/"
# database_name = 'gpt4_summaries_short_qualifying.db'
# db_path = '/%s/%s'%(directory, database_name)
db_engine = sqlalchemy.create_engine('postgresql://sgqokpuggkrkve:ff59f8ca03f950cef2e98fb4ae4ff44bdf7136ff37da62215672902c613297d6@ec2-18-211-172-50.compute-1.amazonaws.com:5432/d3mhp3r7jhume9')

metadata = MetaData(bind=db_engine)
metadata.reflect()
print(metadata)
generated_summaries = metadata.tables['generated_summaries']
label = metadata.tables['label']
# index1 = Index('idx_generated_summaries', generated_summaries.c.summary_uuid)
# index2 = Index('idx_label', label.c.summary_uuid)
# index3 = Index('idx_label', label.c.summary_uuid)
# index1.create(bind=db_engine)
# index2.create(bind=db_engine)

# con = db_engine.connect()

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
    "sanjana": User(1, "sanjana", "zR46"),
    "elisa": User(2, "elisa", "fJ89"),
    "ann_japq": User(4, "ann_japq", "bcxw"),
    "ann_tpfo": User(5, "ann_tpfo", "ydvl"),
    "ann_hkfy": User(6, "ann_hkfy", "f3iKK3"),
    "ann_xnvp": User(7, "ann_xnvp", "m9A7kD"),
    "ann_uulx": User(8, "ann_uulx", "cniZC3"),
    "ann_cpts": User(9, "ann_cpts", "PuaduO"),
    "ann_slct": User(10, "ann_slct", "WGzrCv"),
    "ann_poem": User(11, "ann_poem", "jb69hV"),
    "ann_vimn": User(12, "ann_vimn", "JsLYbe"),
    "ann_ccry": User(13, "ann_ccry", "CoZAmc"),
    "ann_wjbp": User(14, "ann_wjbp", "MbSTIv"),
    "ann_yzof": User(15, "ann_yzof", "TpfNvf"),
    "ann_jqnj": User(16, "ann_jqnj", "TYMjE1"),
    "ann_hzdu": User(17, "ann_hzdu", "HGMj13"),
    "ann_muna": User(18, "ann_muna", "eNv3VF"),
    "ann_hoau": User(19, "ann_hoau", "xSK3kg"),
    "ann_epbi": User(20, "ann_epbi", "t2y4mC"),
    "ann_kprt": User(21, "ann_kprt", "fjQHZL"),
    "ann_hvxx": User(22, "ann_hvxx", "2XfMYz"),
    "ann_eiup": User(23, "ann_eiup", "DkenFx"),
    "ann_kruj": User(24, "ann_kruj", "Ev3lRK"),
    "ann_ladr": User(25, "ann_ladr", "F9EcZM"),
    "ann_xqih": User(26, "ann_xqih", "93eXUT"),
    "ann_wqxe": User(27, "ann_wqxe", "KIe1K6"),
    "ann_cdhi": User(28, "ann_cdhi", "hzwgEU"),
    "ann_skdq": User(29, "ann_skdq", "ou1Er8"),
    "sanjana_dummy": User(1, "sanjana_dummy", "zR46669"),
    }
    return users

@login_manager.user_loader
def load_user(username):
    return get_users().get(username)


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
@application.route('/')
def hello():
    return redirect(url_for('login'))





@application.route("/download")
def download_file():
    return send_from_directory(
        directory, database_name, as_attachment=True
    )


@application.route('/logout')
@login_required
def logout():
    login_link = url_for('login')
    print(login_link)
    logout_user()
    return render_template('logout.html', login_lin = login_link)


def get_summary_article_for_uid(docid) -> Tuple[str]:
    with db_engine.connect() as con:
        stmt = select([generated_summaries.c.dialogue, generated_summaries.c.summary, generated_summaries.c.docid, generated_summaries.c.model]).where(generated_summaries.c.docid == docid)
        
        dialogue, summary, docid, model = con.execute(stmt).fetchone()
    return dialogue, summary, docid, model

@login_required
@application.route('/annotate/<docid>')
def annotate(docid):
    # uid is a unique identifier for a *generated*
    # summary. 
    username = current_user.username
    dialogue, summary, docid, model= get_summary_article_for_uid(docid)
    summ_sents = list(nlp(summary).sents)

    dialogue_whole = dialogue
    
    dialogue = [] 
    print(dialogue)
    if ':' in  dialogue_whole:
        for each in dialogue_whole.split('\n'):
            dialogue.append((each.split(':')[0], ' '.join(each.split(':')[1:])))
    else: 
        for each in dialogue_whole.split('\n'):
            dialogue.append((each.split(' ')[0], ' '.join(each.split(' ')[1:])))
    # print(dialogue)
    speaker_list = list(set([each[0] for each in dialogue]))
    print(list(set(speaker_list)))
    return render_template("annotate.html", username = username, dialogue= dialogue, summary = summary, summ_sents = summ_sents,  docid = docid,  model = model, dialogue_whole = dialogue_whole, speaker_list = speaker_list)

@login_required
def back(current_uuid):
        with db_engine.connect() as con:
        
            username = current_user.username
            stmt = select(label.c.docid).where(label.c.user_id == username).order_by(label.c.docid)
            uuids = con.execute(stmt).fetchall()
            uuids = [each[0] for each in uuids]
            # print('ALL LABELED', uuids)
            if current_uuid in uuids:
                current_uuid_idx = uuids.index(current_uuid)
                back_uuid = uuids[current_uuid_idx - 1]
            elif uuids:
                back_uuid =  uuids[-1]
            else:
                back_uuid = current_uuid
            
            return annotate(back_uuid)

@login_required
@application.route('/next',)

def next():
        
        username = current_user.username 
        subquery = select([label]).where(and_(generated_summaries.c.docid == label.c.docid, label.c.user_id == username))
        
        stmt = select(generated_summaries.c.docid).where(~exists(subquery)).order_by(generated_summaries.c.docid).limit(1)
        with db_engine.connect() as con:
            summary_uuid = con.execute(stmt).fetchone()
            print(con.execute(stmt).fetchall() )
        if summary_uuid is None:
            return render_template("all_done.html")
        
        print('NEXT', summary_uuid[0], username, )
        return annotate(summary_uuid[0])


def process_summ_annotations(request_data_summ):
    print('REQ SUMM', request_data_summ)
    # processed_request_data_summ = {v : {}  for each_req in request_data_summ for k , v in each_req.items() if 'Evidence' in v and k == 'type' }
    # print(processed_request_data_summ)

    processed_request_data_summ = {}
    annotation_types = []
    for each_req in request_data_summ:
        annotation_type = each_req['type']
        text_span = each_req['text']
        if 'Found' in  annotation_type:
            annotation_type = f'{annotation_type}_{text_span}'
            processed_request_data_summ[annotation_type] = {}
            
        elif 'Evidence' in annotation_type:
            processed_request_data_summ[annotation_type] = {}
                
            
            
    print(processed_request_data_summ)
                
            
    for label_num in list(processed_request_data_summ.keys()):
        for each_request in request_data_summ:
            if label_num in each_request['type'] or 'Found' in label_num:
                
                if 'Found' in label_num:
                    nonfactual_spans = label_num.split('_')[-1].strip()
                
                else:
                    nonfactual_spans = each_request['text']
                error_type = None
                for other_request in request_data_summ:
                    if (nonfactual_spans == other_request['text']) and ('Error' in other_request['type']):
                        # print('here')
                        error_type = other_request['type']
                processed_request_data_summ[label_num]['nonfactual_spans'] = nonfactual_spans
                processed_request_data_summ[label_num]['error_type'] = error_type
                if 'Found' in label_num:
                    processed_request_data_summ[label_num]['Evidence'] = 'Not found'
                        
 
    return processed_request_data_summ
    
@login_required
@application.route('/save_annotation', methods=['POST'])
def save_annotation():
    print(request.form)

    button_val = str(request.form['button'])
    print(button_val, button_val == 'submit')
    summ_uuid = request.form['summ_uuid']
    if button_val == 'Submit':
        username = request.form['username']
        
        system_id = request.form['system_id']
        summary = request.form['summary']
        dialogue = request.form['dlg_whole']
        request_data_summ = request.form['annotations_summ']
        request_data_dlg = request.form['annotations_dlg']
        processed_request_data_summ = {}
        
        if (request_data_summ or request_data_dlg):
            if request_data_summ:
                request_data_summ = eval(request_data_summ)
                
                processed_request_data_summ = process_summ_annotations(request_data_summ)
            
            evidence_map = {}
            if request_data_dlg.strip():
                request_data_dlg = eval(request_data_dlg)
                for each_request in request_data_dlg:
                    text = each_request['text']
                    type = each_request['type']
                    
                    if (type not in evidence_map) :
                            evidence_map[type] = []
                    evidence_map[type].append(text)

            for type , type_evdx in evidence_map.items():
                if 'Found' not in type:
                    if type in  processed_request_data_summ:
                            processed_request_data_summ[type]['Evidence'] = '\n'.join(type_evdx)
            print('ANNOTATIONS', processed_request_data_summ, )
            print('EVIDENCE MAP', evidence_map)

            if evidence_map and not processed_request_data_summ:
                flash("Error not chosen for evidence, please select the appropriate span")
                return annotate(summ_uuid)
            if processed_request_data_summ and not evidence_map:
                flash('Evidence not chosen for error span, please select the appropriate evidence or select "NOT FOUND" for no evidence')
                return annotate(summ_uuid)
    
        with db_engine.connect() as con:
                summary = re.sub( "'", r"''", summary)
                dialogue = re.sub( "'", r"''", dialogue)
                if not processed_request_data_summ:
                    error_span = None
                    error_type = None
                    evidence = None
                    q_str = """INSERT INTO label (user_id, docid, model, nonfactual_spans, evidence, error_type, summary, dialogue) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                    
                    con.execute(q_str, (username, summ_uuid, system_id, error_span, evidence, error_type, summary, dialogue))

                else:
                    
                    for error_key, error_val in processed_request_data_summ.items():
                        print(username)
                        error_span = error_val['nonfactual_spans']
                        error_type = error_val['error_type']
                        evidence = error_val['Evidence']
                        q_str = """INSERT INTO label (user_id, docid, model, nonfactual_spans, evidence, error_type, summary, dialogue) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                        con.execute(q_str, (username, summ_uuid, system_id, error_span, evidence, error_type, summary, dialogue))
            #     con.commit()
                
            # print(username, summ_uuid)
            # print('LABELS', con.execute('SELECT * FROM label').fetchone())
    
        return next()

    elif button_val == 'Back':
        return back(summ_uuid)
    


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080)