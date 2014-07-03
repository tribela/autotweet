import logging
import threading
from flask import Flask, jsonify, render_template, request
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

app = Flask(__name__)

pipe = Queue()

app.config.update({
    'use_worker': True,
    'worker_running': False,
    })


def worker():
    logging.info('worker started')
    app.config.update(worker_running=True)
    atm = app.config['atm']
    changed_grams = set()
    while 1:
        (question, answer) = pipe.get()
        grams = atm._add_doc(question, answer)
        changed_grams.update(grams)
        pipe.task_done()

        if not pipe.qsize():
            atm._recalc_idfs(changed_grams)


def spawn_worker():
    thread = threading.Thread(target=worker)
    thread.setDaemon(True)
    thread.start()


@app.before_first_request
def initialize():
    if app.config['use_worker']:
        spawn_worker()


def set_logging_level(level):
    if level is None:
        level = 0
    logging.basicConfig(level=level*10)


@app.route('/')
def form():
    atm = app.config['atm']
    count = len(atm)
    return render_template('form.html', count=count)


@app.route('/query/')
def result():
    atm = app.config['atm']
    query = request.args['query']
    answer = atm.get_best_answer(query)
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
        if app.config['worker_running']:
            pipe.put((question, answer))
            return ('', 202)
        else:
            app.config['atm'].add_document(question, answer)
            return ''

    return ('', 400)
