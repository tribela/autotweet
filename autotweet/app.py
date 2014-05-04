from flask import Flask, render_template, request

from .database import get_best_answer, add_document, Document

app = Flask(__name__)


@app.route('/')
def form():
    session = app.config['session']
    count = session.query(Document).count()
    return render_template('form.html', count=count)


@app.route('/query/', methods=['POST'])
def result():
    session = app.config['session']
    query = request.form['query']
    answer = get_best_answer(session, query)
    return answer or ''


@app.route('/teach/', methods=['POST'])
def teach():
    session = app.config['session']
    question = request.form['question'].strip()
    answer = request.form['answer'].strip()

    if question and answer:
        add_document(session, question, answer)

    return ''
