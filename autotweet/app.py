from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


@app.route('/')
def form():
    atm = app.config['atm']
    count = len(atm)
    return render_template('form.html', count=count)


@app.route('/query/')
def result():
    atm = app.config['atm']
    query = request.args['query']
    result = atm.get_best_answer(query)
    if not result:
        r = jsonify()
        r.status_code = 404
        return r

    answer, ratio = result

    return jsonify({
        'answer': answer,
        'ratio': ratio,
        })


@app.route('/teach/', methods=['POST'])
def teach():
    question = request.form['question'].strip()
    answer = request.form['answer'].strip()

    if question and answer:
        app.config['atm'].add_document(question, answer)
        return ''

    return ('', 400)
