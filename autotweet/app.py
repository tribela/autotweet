import threading
from flask import Flask, jsonify, render_template, request
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from .database import _add_doc, _recalc_idfs, Document, get_best_answer

app = Flask(__name__)

pipe = Queue()


def worker():
    session = app.config['session']
    while 1:
        (question, answer) = pipe.get()
        _add_doc(session, question, answer)
        pipe.task_done()

        if not pipe.qsize():
            _recalc_idfs(session)


def spawn_worker():
    thread = threading.Thread(target=worker)
    thread.setDaemon(True)
    thread.start()


spawn_worker()


@app.route('/')
def form():
    session = app.config['session']
    count = session.query(Document).count()
    return render_template('form.html', count=count)


@app.route('/query/')
def result():
    session = app.config['session']
    query = request.args['query']
    answer = get_best_answer(session, query)
    if not answer:
        r = jsonify()
        r.status_code = 404
        return r

    return jsonify({
        'answer': answer[0],
        'ratio': answer[1],
        })


@app.route('/teach/', methods=['POST'])
def teach():
    question = request.form['question'].strip()
    answer = request.form['answer'].strip()

    if question and answer:
        pipe.put((question, answer))
        return ('', 202)

    return ('', 400)
