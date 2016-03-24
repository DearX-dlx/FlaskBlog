# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort,render_template, flash

app = Flask(__name__)

#设置配置内容，这里一般用另一个文件进行写
#然后使用下面这句代码导入
#app.config.from_envvar('FLASKR_SETTINGS',silent=True)
app.config.update(
    dict(
        #app.root_path来获取根目录属性
        DATABASE=(os.path.join(app.root_path,'FlaskBlog.db')),
        DEBUG=True,
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='123456'
    )
)

#连接数据库，之前还要创建数据库
def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    if rv:
        print 'sqlite3数据库连接成功', rv
    rv.row_factory = sqlite3.Row
    return rv

#传入sql语句来初始化数据库
def init_db():
    print '初始化数据库'
    with app.app_context():
        db = get_db()
        print '获取到数据库',db
        #打开文件，然后读取文件‘r’ ,然后装载到f里面执行
        with app.open_resource('schema.sql',mode='r') as f:
            db.cursor().executescript(f.read())
            print '执行sql语句文件成功'

        #提交执行
        db.commit()
        print 'sql语句执行完毕'

def get_db():
    """
    为当前程序打开一个新的数据库连接（如果没有数据库连接）.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


#--------- 展示视图模板 ---------
@app.route('/')
def show_entries():


    #执行sql语句、从数据库里面获取数据
    cur = g.db.execute('select title, text from entries order by id desc')

    # 获取到数据然后转存到entries数组中，数组中每一个都是一个字典
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    #返回数据模板和数据，现在我们并没有把模板写好，写好了自然就有了
    return render_template('show_entries.html', entries=entries)

#--------添加内容懂啊数据库，然后刷新模板进行展示 -------
@app.route('/add', methods=['POST'])
def add_entry():
    #logged_in 是全局的变量，标识是否登录了
    if not session.get('logged_in'):
        abort(401)

    #执行sql插入语句，把数据插入到数据库中
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

#登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            #重定向到显示数据模板
            return redirect(url_for('show_entries'))
    # GET请求无反应
    return render_template('login.html', error=error)


#登出
@app.route('/logout')
def logout():
    #pop是指如果有这个键就删除这个键值，否则什么都不做
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

# ------------------------------------------------------------

# @app.cli.command('initdb')
# def initdb_command():
#     """Creates the database tables."""
#     init_db()
#     print('Initialized the database.')
#
#
# def get_db():
#     """Opens a new database connection if there is none yet for the
#     current application context.
#     """
#     if not hasattr(g, 'sqlite_db'):
#         g.sqlite_db = connect_db()
#     return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.before_request
def before_request():
    g.db = connect_db()


# ------------------------------------------------------------

if __name__ == '__main__':

    app.run(debug=True)

