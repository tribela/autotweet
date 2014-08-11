import logging
from flask import Flask, g, jsonify, render_template, request
from . import database

app = Flask(__name__)

logger = logging.getLogger('web')


@app.before_first_request
def initialize():
    database.init_db(app.config['DB_URI'])

    log_file = app.config.get('LOG_FILE', None)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        logger.addHandler(file_handler)


@app.before_request
def before_request():
    g.db_session = database.get_session(app.config['DB_URI'])


@app.teardown_appcontext
def shutdown_session(exception=None):
    g.db_session.remove()


@app.route('/')
def form():
    count = database.get_count(g.db_session)
    return render_template('form.html', count=count)


@app.route('/query/')
def result():
    query = request.args['query']
    result = database.get_best_answer(g.db_session, query)
    if not result:
        r = jsonify()
        r.status_code = 404
        return r

    answer, ratio = result

    logger.info(u'{0} -> {1} ({2})'.format(query, answer, ratio))

    return jsonify({
        'answer': answer,
        'ratio': ratio,
        })


@app.route('/teach/', methods=['POST'])
def teach():
    question = request.form['question'].strip()
    answer = request.form['answer'].strip()

    if question and answer:
        database.add_document(g.db_session, question, answer)
        return ''

    return ('', 400)
