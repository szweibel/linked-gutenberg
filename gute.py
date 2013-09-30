import os
from flask import Flask, request, redirect, url_for, render_template, flash, make_response, jsonify, send_file
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask.ext.restless import APIManager

# create application
app = Flask('gute')

app.config.from_pyfile('settings.cfg')

# connect to database
db = SQLAlchemy(app)
# Instatiate API
manager = APIManager(app, flask_sqlalchemy_db=db)

"""
MODELS
"""

agent_work = db.Table('agent_work',
    db.Column('agent_id', db.Integer, db.ForeignKey('agent.id')),
    db.Column('work_id', db.Integer, db.ForeignKey('work.id'))
)

LCSH_work = db.Table('LCSH_work',
    db.Column('subject_heading', db.String(100), db.ForeignKey('LCSH.subject_heading')),
    db.Column('work_id', db.Integer, db.ForeignKey('work.id'))
)

tokens = db.Table('tokens',
    db.Column('token_id', db.Integer, db.ForeignKey('token.id'), primary_key=True),
    db.Column('work_id', db.Integer, db.ForeignKey('work.id'), primary_key=True),
    db.Column('position', db.Integer)
)

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agents = db.relationship('Agent', secondary=agent_work,
            backref=db.backref('works', lazy='dynamic'))
    title = db.Column(db.Text)
    publication_date = db.Column(db.DateTime)
    call_number = db.Column(db.Text)
    LCSH = db.relationship('LCSH', secondary=LCSH_work,
            backref=db.backref('works', lazy='dynamic'))
    texts = db.relationship('Text',backref='work',lazy='dynamic')
    corpus = db.Column(db.Text(length=4294967295))
    def corp(self):
        return self.corpus[:200]

    def __repr__(self):
        return '<%r: %r>' % (self.call_number, self.title)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    birth_date = db.Column(db.String(30))
    death_date = db.Column(db.String(30))
    wiki_page = db.Column(db.Text)
    aliases = db.relationship('Alias', backref='agent',
                                    lazy='dynamic')

    def __repr__(self):
        return '<Agent %r>' % self.name

class Alias(db.Model):
    name = db.Column(db.String(150),primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'),primary_key=True)

    def __repr__(self):
        return '<Alias %r>' % self.name

class Text(db.Model):
    url = db.Column(db.String(200),primary_key=True)
    work_id = db.Column(db.Integer,db.ForeignKey('work.id'),primary_key=True)

    def __repr__(self):
        return '<Text %r>' % self.url

class LCSH(db.Model):
    subject_heading = db.Column(db.String(100),primary_key=True)

    def __repr__(self):
        return '<LCSH %r>' % self.subject_heading

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    toke = db.Column(db.String(80))

    def __repr__(self):
        return '<Library %r>' % self.toke


# create API locations
manager.create_api(Agent, methods=['GET'])
manager.create_api(Alias, methods=['GET'])
manager.create_api(Work, methods=['GET'])
manager.create_api(LCSH, methods=['GET'])
manager.create_api(Text, methods=['GET'])

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
@app.route('/')
def front_page():
    return render_template('index.html',
                        **{name : db.session.query(func.count('*')).select_from(table).scalar() for name,table in (('agent',Agent),('work',Work),('lcsh',LCSH))})

@app.route('/agent/<name>')
def show_agent(name):
    agent = Agent.query.filter(Agent.name==name).first_or_404()
    return render_template('show_agent.html',agent=agent)

@app.route('/agents', methods = ['GET', 'POST'])
@app.route('/agents/<int:page>', methods=['GET', 'POST'])
@app.route('/agents/<name>/<int:page>',methods=['POST','GET'])
@app.route('/agents/<name>',methods=['POST','GET'])
def show_agents(name='',page=1):
    if name == '':
        agents = Agent.query.filter(Agent.name != None).order_by(Agent.name).paginate(page, 50)
    else: #essentially a search mode
        agents = Agent.query.filter(Agent.name.like('%'+name+'%')).order_by(Agent.name).paginate(page,50)
    return render_template('agents.html',agents=agents,name=name) if agents.total > 0 else (render_template('404.html'),404)

@app.route('/work/<title>',methods=['GET','POST'])
def show_work(title):
    work = Work.query.filter(Work.title.like('%'+title+'%')).first_or_404()
    return render_template('show_work.html', work=work)

@app.route('/works',methods=['GET','POST'])
@app.route('/works/<int:page>', methods=['GET', 'POST'])
@app.route('/works/<title>/<int:page>',methods=['POST','GET'])
@app.route('/works/<title>',methods=['POST','GET'])
def show_works(title='',page=1):
    if title == '':
        works = Work.query.filter(Work.title != None).order_by(Work.title).paginate(page,50)
    else: #search mode
        works = Work.query.filter(Work.title.like('%'+title+'%')).order_by(Work.title).paginate(page,50)
    return render_template('works.html',works=works,title=title) if works.total > 0 else render_template('404.html'),404

@app.route('/corpus/<title>',methods=['POST','GET'])
def show_corpus(title=''):
    work = Work.query.filter(Work.title == title).first_or_404()
    return render_template('show_corpus.html',work=work)

@app.route('/LCSH/<subject_heading>',methods=['GET','POST'])
def show_LCSH(subject_heading):
    lcsh = LCSH.query.filter(LCSH.subject_heading.like('%'+subject_heading+'%')).first_or_404()
    return render_template('show_LCSH.html',lcsh=lcsh)

@app.route('/LCSHs',methods=['GET','POST'])
@app.route('/LCSHs/<int:page>',methods=['GET','POST'])
@app.route('/LCSHs/<subject_heading>/<int:page>',methods=['POST','GET'])
@app.route('/LCSHs/<subject_heading>',methods=['POST','GET'])
def show_LCSHs(page=1,subject_heading=''):
    if subject_heading == '':
        lcshs = LCSH.query.order_by(LCSH.subject_heading).paginate(page,50)
    else: #search mode
        lcshs = LCSH.query.filter(LCSH.subject_heading.like('%'+subject_heading+'%')).order_by(LCSH.subject_heading).paginate(page,50)
    return render_template('LCSHs.html',lcshs=lcshs,subject_heading=subject_heading) if lcshs.total > 0 else render_template('404.html'),404

@app.route('/search')
def search_form():
    form_redirects = {
            'agents' : ('show_agents','name'),
            'works' : ('show_works','title'),
            'lcshs' : ('show_LCSHs','subject_heading')
            }
    print {key:request.values[key] for key in form_redirects[request.values['class_type']][1:]}
    try:
        return redirect(url_for(form_redirects[request.values['class_type']][0],
                **{key:request.values[key].strip() for key in form_redirects[request.values['class_type']][1:]}))
    except AttributeError:
        flash('There was a problem with the search')
        return redirect(url_for(page_not_found))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.debug = True
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run()
