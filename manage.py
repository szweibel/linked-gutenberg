from flask.ext.script import Manager
from gute import *
from datetime import datetime

manager = Manager(app)

@manager.command
def restart_db():
    db.drop_all()
    db.create_all()

    author = Agent(name='Stephen Zweibel', birth_date=datetime.strptime('1985', '%Y'), aliases=[Alias(name='Laurence'), Alias(name='Fred')])
    an_author = Agent(name='Joe Wilner', birth_date=datetime.strptime('1986', '%Y'), aliases=[Alias(name='Willie'), Alias(name='Potato')])
    a_work = Work(title='My Autobiography', agents=[author, an_author])

    db.session.add(a_work)

    db.session.commit()


@manager.command
def rdf_import(which):
    db.session.commit()




if __name__ == "__main__":
    manager.run()
