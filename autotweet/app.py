import threading
from flask import Flask, jsonify, render_template, request
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

app = Flask(__name__)

pipe = Queue()


def worker():
    atm = app.config['atm']
    while 1:
        (question, answer) = pipe.get()
        atm._add_doc(question, answer)
        pipe.task_done()

        if not pipe.qsize():
            atm._recalc_idfs()


def spawn_worker():
    thread = threading.Thread(target=worker)
    thread.setDaemon(True)
    thread.start()


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
        pipe.put((question, answer))
        return ('', 202)

    return ('', 400)
