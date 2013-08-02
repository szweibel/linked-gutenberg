import os
from flask import Flask, request, redirect, url_for, render_template, flash, make_response, jsonify, send_file
from flask.ext.sqlalchemy import SQLAlchemy
# import flask.ext.restless

# create application
app = Flask('gute')

app.config.from_pyfile('settings.cfg')

# connect to database
db = SQLAlchemy(app)


"""
MODELS
"""


agents = db.Table('agents',
    db.Column('agent_id', db.Integer, db.ForeignKey('agent.id')),
    db.Column('work_id', db.Integer, db.ForeignKey('work.id'))
)

headings = db.Table('headings',
    db.Column('LCSH_id', db.Integer, db.ForeignKey('LCSH.id')),
    db.Column('work_id', db.Integer, db.ForeignKey('work.id'))
)

tokens = db.Table('tokens',
    db.Column('token_id', db.Integer, db.ForeignKey('token.id'), primary_key=True),
    db.Column('work_id', db.Integer, db.ForeignKey('work.id'), primary_key=True),
    db.Column('position', db.Integer)
)

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agents = db.relationship('Agent', secondary=agents,
            backref=db.backref('works', lazy='dynamic'))
    title = db.Column(db.Text)
    publication_date = db.Column(db.DateTime)
    call_number = db.Column(db.Text)
    LCSH = db.relationship('LCSH', secondary=headings,
            backref=db.backref('works', lazy='dynamic'))

    def __repr__(self):
        return '<%r: %r>' % (self.call_number, self.title)


class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    birth_date = db.Column(db.DateTime)
    death_date = db.Column(db.DateTime)
    wiki_page = db.Column(db.Text)
    aliases = db.relationship('Alias', backref='agent',
                                    lazy='dynamic')

    def __repr__(self):
        return '<Agent %r>' % self.name

    def __init__(self,id=id,name=name,birth_date=birth_date,death_date=death_date,wiki_page=wiki_page):
        self.id = id
        self.name = name
        self.birth_date = birth_date
        self.death_date = death_date
        self.wiki_page = wiki_page



class Alias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))

    def __repr__(self):
        return '<Alias %r>' % self.name

class LCSH(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_heading = db.Column(db.Text)

    def __repr__(self):
        return '<LCSH %r>' % self.subject_heading


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    toke = db.Column(db.String(80))

    def __repr__(self):
        return '<Library %r>' % self.toke


"""
LOGIC
"""


@app.after_request
def shutdown_session(response):
    db.session.remove()
    return response


"""
URLS/VIEWS
"""


# View for the Homepage
@app.route('/', methods=['GET', 'POST'])
def front_page():
    library = request.cookies.get('library_id') or Library.query.first().id
    return redirect(url_for('home', library_id=library))

@app.route('/agent/<name>')
def show_agent(name):
	agent = Agent.query.filter_by(Agent.name.like(name)).first_or_404()
	return render_template('show_agent.html',agent=agent)

@app.route('/agents')
def show_agents():
	agents = Agent.query.order_by(Agent.name)
	return render_template('agents.html',agents=agents)
	
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # app.debug = True
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run()
