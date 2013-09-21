from flask.ext.script import Manager
from gute import db, Work, Agent, Alias, app
from datetime import datetime

manager = Manager(app)

@manager.command
def test_db():
    db.drop_all()
    db.create_all()

    author = Agent(name='Stephen Zweibel', birth_date=datetime.strptime('1985', '%Y'), aliases=[Alias(name='Laurence'), Alias(name='Fred')])
    another_author = Agent(name='Joe Wilner', birth_date=datetime.strptime('1986', '%Y'), aliases=[Alias(name='Willie'), Alias(name='Potato')])
    a_work = Work(title='My Autobiography', agents=[author, another_author])

    db.session.add(a_work)
    db.session.commit()


@manager.command
def init():
    db.drop_all()
    db.create_all()
#    import db_load_serialized_agents


if __name__ == "__main__":
    manager.run()
