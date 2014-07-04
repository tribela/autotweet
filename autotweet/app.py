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
        app.config['atm'].add_document(question, answer)
        return ''

    return ('', 400)
