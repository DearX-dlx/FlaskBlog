###1、搭建flask项目结构
&emsp;&emsp;我使用的是PyCharm，直接可以创建flask的项目工程，于是我们创建之后的项目是这样的，暂且我们把项目叫做FlaskBlog。如果我们直接运行这个项目，我们就可以在http://127.0.0.1:5000/访问flask的服务器了，而且我们可以看到“hello world”的字段。对！就是这么简单，这样我们就可以访问hello_world方法了，flask会根据url后面的参数定义相对应的方法。

###2、用来存储微博条目的数据库SQLite
&emsp;&emsp;我们把其命名为schema.sql文件，直接放在我们的主目录下，里面的内容如下，我们想要执行的sql语句都在这里。
```
DROP TABLE if EXISTS entries;
CREATE TABLE entries(
  id INTEGER PRIMARY KEY autoincrement,
  title string NOT NULL ,
  text string NOT NULL
)
```

###3. 添加配置文件
&emsp;&emsp;app配置文件会配置一些路径以及一些系统的关键字，我们可以在APP中写如下配置内容:
```
app.config.update(dict(
    DATABASE=(os.path.join(app.root_path,'FlaskBlog.db')),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='123456'
))
```
当然我们也可以把这些配置文件内容写在一个文件当中，然后通过
```
app.config.from_envvar('FLASKR_SETTINGS',silent=True)
```
代码来加载此文件，FLASKR_SETTING为这个的文件名字。

###4. 连接数据库
&emsp;&emsp;在连接数据库的时候还需要创建一个数据库链接对象，我们直接在根目录下创建一个FlaskBlog.db文件，这就是我们的数据库文件，这里文件路径就写在配置文件里面的DATABASE属性里面。
```
#连接数据库
def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    if rv:
        print 'sqlite3数据库连接成功', rv
    rv.row_factory = sqlite3.Row
    return rv
```

然后实例化一个数据库对象来执行我们的sql语句
```
#传入sql语句来初始化数据库
def init_db():
    print '初始化数据库'
    with app.app_context():
        db = get_db()
        print '获取到数据库',db
        #打开文件，然后读取文件‘r’ ,然后装载到f里面执行
        with app.open_resource('schema.sql',mode='r') as f:
            db.cursor().executescript(f.read())
        
        #提交执行
        db.commit()

def get_db():
    """
    为当前程序打开一个新的数据库连接（如果没有数据库连接）.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
```
###5. 编写视图
- 编写模板：模板使用 Jinja2 语法并默认开启自动转义，当然你也得先去了解一下Jinja2语法。模板文件需要放在templated文件夹中，以便我们进行管理和重用。

layout.html:这个模块会包含HTML主体结构、标题和一个登入链接。css我们会在后面添加。
```
<!doctype html>
<title>Flaskr</title>
<link rel=stylesheet type=text/css href="{{ url_for('static', filename='style.css') }}">
<div class=page>
  <h1>Flaskr</h1>
  <div class=metanav>
  {% if not session.logged_in %}
    <a href="{{ url_for('login') }}">log in</a>
  {% else %}
    <a href="{{ url_for('logout') }}">log out</a>
  {% endif %}
  </div>
  {% for message in get_flashed_messages() %}
    <div class=flash>{{ message }}</div>
  {% endfor %}
  {% block body %}{% endblock %}
</div>
```
show_entries.html:继承layout.html模板。
```
{% extends "layout.html" %}
{% block body %}
  {% if session.logged_in %}
    <form action="{{ url_for('add_entry') }}" method=post class=add-entry>
      <dl>
        <dt>Title:
        <dd><input type=text size=30 name=title>
        <dt>Text:
        <dd><textarea name=text rows=5 cols=40></textarea>
        <dd><input type=submit value=Share>
      </dl>
    </form>
  {% endif %}
  <ul class=entries>
  {% for entry in entries %}
    <li><h2>{{ entry.title }}</h2>{{ entry.text|safe }}
  {% else %}
    <li><em>Unbelievable.  No entries here so far</em>
  {% endfor %}
  </ul>
{% endblock %}
```
login.html:继承layout.html模板，显示一个允许用户登入的表单。
```
{% extends "layout.html" %}
{% block body %}
  <h2>Login</h2>
  {% if error %}<p class=error><strong>Error:</strong> {{ error }}{% endif %}
  <form action="{{ url_for('login') }}" method=post>
    <dl>
      <dt>Username:
      <dd><input type=text name=username>
      <dt>Password:
      <dd><input type=password name=password>
      <dd><input type=submit value=Login>
    </dl>
  </form>
{% endblock %}
```
style.css:这当然就是我们的样式表，样式是不能缺的。
```
body    {font-family: sans-serif;background: #eee;}
a,h1,h2 {color: #377BAB;}
h1,h2   {font-family: 'Georgia', sefif;margin: 0;}
h1      {border-bottom: 2px solid:#eee;}
h2      {font-size: 1.2em;}

.page   {margin: 2em auto;width: 35em; border:5px solid #ccc; padding: 0.8em;background: white;}
.entries    {list-style: none;margin: 0;padding: 0;}
.entries li {margin: 0.8em 1.2em;}
.entries li h2 {margin-left: -1em;}
.add-entry {font-size: 0.9em;border-bottom: 1px solid #ccc;}
.add-entry dl   {font-weight: bold;}
.metanav    {text-align: right;font-size: 0.8em;padding: 0.3em;  margin-bottom: 1em;background: #fafafa;}
.flash  {background: #CEE5F5;  padding: 0.5em;  border: 1px solid #AACBE2;}
.error  {background: #F0D6D6;padding: 0.5em;}
```
- 编写业务逻辑：我们需要定义函数来展示我们的模板，我们显示条目、添加条目、登录以及登出四个功能，并且返回对于的展示页面。
```
#--------- 显示条目 ---------
@app.route('/')
def show_entries():
    #执行sql语句、从数据库里面获取数据
    cur = g.db.execute('select title, text from entries order by id desc')
    # 获取到数据然后转存到entries数组中，数组中每一个都是一个字典
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    #返回数据模板和数据，现在我们并没有把模板写好，写好了自然就有了
    return render_template('show_entries.html', entries=entries)
```
```
#------- 添加条目，然后刷新模板进行展示 -------
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
```
```
#------- 登录 -----------------
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
```
```
#------ 登出 ----------------
@app.route('/logout')
def logout():
    #pop是指如果有这个键就删除这个键值，否则什么都不做
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))
```
###6. 运行程序
&emsp;&emsp;经过上面的代码程序就可以运行起来了嘛？按照官方文档上面给的确实就没有了，我以为程序也是可以运行起来的了，但是还是运行不起来，我们还要做如下事情：
```
#before_request :在请求收到之前绑定一个函数做一些事情。
#after_request: 每一个请求之后绑定一个函数，如果请求没有异常。
#teardown_request: 每一个请求之后绑定一个函数，即使遇到了异常。

@app.before_request
def before_request():
    #在发送请求先连接到数据库
    g.db = connect_db()
    
@app.teardown_appcontext
def close_db(error):
    #请求完成后关闭数据库
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
```
&emsp;&emsp;现在点击运行就能够看到我们的第一个flask项目完成了。登陆的账户和密码就是我们在配置代码中写的内容，登录进去能够发表内容，查看内容以后退出登录，至此我们的小博客平台已经完成了。
