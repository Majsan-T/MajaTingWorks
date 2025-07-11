# app/models.py
from flask_login import UserMixin
from sqlalchemy import DateTime, Column, String, Text, Integer, ForeignKey, Boolean, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from sqlalchemy.dialects.mysql import LONGTEXT, TIMESTAMP, DATETIME
from sqlalchemy.schema import FetchedValue
from app.extensions import db
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from app.utils.time import get_local_now, DEFAULT_TZ

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # is_password_set = db.Column(db.Boolean, default=False)  # 👈 nytt fält
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 👈 Lägg till denna rad
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    subtitle = Column(String(250), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)  # Viktigt: nullable=True för CLI-kommandon
    body = Column(LONGTEXT, nullable=False)
    img_url = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey("blog_categories.id"))
    category = relationship("BlogCategory", back_populates="posts")
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_post", cascade="all, delete-orphan")
    email_sent = Column(Boolean, default=False)

class BlogCategory(db.Model):
    __tablename__ = 'blog_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # URL-vänligt namn
    title = db.Column(db.String(100), nullable=False)             # Visningsnamn
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(250), nullable=True)
    posts = db.relationship("BlogPost", back_populates="category", cascade="all, delete")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(ZoneInfo("Europe/Stockholm"))
    )
    visible = db.Column(db.Boolean, default=True)
    flagged = db.Column(db.Boolean, default=False)

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = db.relationship("BlogPost", back_populates="comments")

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = db.relationship("User")

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(100), nullable=True)  # Genrebild för kategorin

    items = db.relationship('PortfolioItem', back_populates='category_obj', lazy=True)

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(LONGTEXT, nullable=False)
    image = db.Column(db.String(100))  # Unik bild för varje projekt
    date = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category_obj = db.relationship('Category', back_populates='items')

class CVContent(db.Model):
    __tablename__ = 'cv_content'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    about = db.Column(db.Text)
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    awards = db.Column(db.Text)
    skills = db.Column(db.Text)
    interests = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
