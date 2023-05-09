import datetime

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func
from flask import Flask, render_template

from config import DevConfig

app = Flask(__name__)
app.config.from_object(DevConfig)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

tags = db.Table('post_tags',
                db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                )


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(
        'id',
        db.Integer(),
        primary_key=True)
    username = db.Column(
        'user_name',
        db.String(255),
        nullable=False,
        index=True,
        unique=True,)
    password = db.Column(
        'password',
        db.String(255))
    posts = db.relationship(
        'Post',
        backref='user',
        lazy='dynamic')

    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return "<User '{}'>".format(self.username)


class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(
        'id',
        db.Integer(),
        primary_key=True)
    name = db.Column(
        'name',
        db.String(255),
        nullable=False,)
    text = db.Column(
        'text',
        db.Text())
    date = db.Column(
        'date',
        db.DateTime(),
        default=datetime.datetime.now)
    post_id = db.Column(
        'post_id',
        db.Integer(),
        db.ForeignKey('post.id'))

    def __repr__(self):
        return "<Comment '{}'>".format(self.text[:15])


class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(
        'id',
        db.Integer(),
        primary_key=True)
    title = db.Column(
        'title',
        db.String(255),
        nullable=False,)
    text = db.Column(
        'text',
        db.Text())
    publish_date = db.Column(
        'publish_date',
        db.DateTime(),
        default=datetime.datetime.now)
    comments = db.relationship(
        'Comment',
        backref='post',
        lazy='dynamic')
    user_id = db.Column(
        'user_id',
        db.Integer(),
        db.ForeignKey('user.id'))
    tags = db.relationship(
        'Tag',
        secondary=tags,
        backref=db.backref('posts', lazy='dynamic')
        )

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return "<Post '{}'>".format(self.title)


class Tag(db.Model):
    __tablename__ = 'tag'

    id = db.Column(
        'id',
        db.Integer(),
        primary_key=True)
    title = db.Column(
        'title',
        db.String(255),
        nullable=True,
        unique=True)

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return "<Tag '{}'>".format(self.title)


def sidebar_data():
    recent = Post.query.order_by(Post.publish_date.desc()).limit(5).all()
    top_tags = db.session.query(
        Tag, func.count(tags.c.post_id).label('total')
    ).join(tags).group_by(Tag).order_by(desc('total')).limit(5).all()
    return recent, top_tags


@app.route('/')
@app.route('/<int:page>')
def home(page=1):
    posts = (
        Post.query.order_by(Post.publish_date.desc())
        .paginate(page=page, per_page=app.config['POSTS_PER_PAGE'],
                  error_out=False, max_per_page=None))
    recent, top_tags = sidebar_data()

    return render_template(
        'blog/home.html',
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    tags = post.tags
    comments = post.comments.order_by(Comment.date.desc()).all()
    recent, top_tags = sidebar_data()
    return render_template(
        'post.html',
        post=post,
        tags=tags,
        comments=comments,
        recent=recent,
        top_tags=top_tags,
    )


@app.route('/posts_by_tag/<string:tag_name>')
def posts_by_tag(tag_name):
    tag = Tag.query.filter_by(title=tag_name).first_or_404()
    posts = tag.posts.order_by(Post.publish_date.desc()).all()
    recent, top_tags = sidebar_data()
    return render_template(
        'blog/tag.html',
        tag=tag,
        posts=posts,
        recent=recent,
        top_tags=top_tags
    )


@app.route('/posts_by_user/<string:username>')
def posts_by_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.publish_date.desc()).all()
    recent, top_tags = sidebar_data()
    return render_template(
        'blog/user.html',
        user=user,
        posts=posts,
        recent=recent,
        top_tags=top_tags
        )


if __name__ == '__main__':
    app.run()
