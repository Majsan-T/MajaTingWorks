# app/models.py
from flask_login import UserMixin
from sqlalchemy import DateTime, Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from app.extensions import db
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# ================================================
# ✅ KOPPLINGSTABELL MELLAN ANVÄNDARE OCH ROLLER
# ================================================
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True)
)

# ================================================
# ✅ ROLER (admin, user, subscriber)
# ================================================
class Role(db.Model):
    """Representerar en roll (t.ex. admin, user, subscriber)."""
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"

# ================================================
# ✅ ANVÄNDARE
# ================================================
class User(UserMixin, db.Model):
    """Användare med roller, inlägg och kommentarer."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    _is_active = db.Column("is_active", db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_password_set = db.Column(db.Boolean, default=False)

    # Relationer
    posts = db.relationship("BlogPost", back_populates="author", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="comment_author", cascade="all, delete-orphan")

    # ✅ Flera roller per användare, många-till-många
    roles = db.relationship("Role", secondary=user_roles, backref="users")

    @property
    def is_active(self):
        """Flask-Login: En användare anses aktiv om den inte är raderad."""
        return not self.is_deleted and self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    # === Rollhantering ===
    def has_role(self, role_name):
        """Kolla om användaren har en viss roll."""
        return any(role.name == role_name for role in self.roles)

    def add_role(self, role_name):
        """Lägg till en roll om den inte finns."""
        role = Role.query.filter_by(name=role_name).first()
        if role and role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role_name):
        """Ta bort en roll om den finns."""
        self.roles = [r for r in self.roles if r.name != role_name]

    def anonymize(self):
        """Radera allt associerat innehåll och sedan användaren."""
        self.email = f"anonymized_{self.id}@example.com"
        self.name = "Raderad användare"
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self._is_active = False

    def delete_permanently(self):
        from app.extensions import db
        for comment in self.comments:
            db.session.delete(comment)
        for post in self.posts:
            db.session.delete(post)
        db.session.delete(self)

# ================================================
# ✅ BLOGGINLÄGG
# ================================================
class BlogPost(db.Model):
    """Ett blogginlägg med titel, text, kategori och kommentarer."""
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    subtitle = Column(String(250), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)  # Viktigt: nullable=True för CLI-kommandon
    views = db.Column(db.Integer, default=0, nullable=False)
    body = Column(LONGTEXT, nullable=False)
    img_url = Column(String(250), nullable=False)
    email_sent = Column(Boolean, default=False)

    # Relationer
    category_id = Column(Integer, ForeignKey("blog_categories.id"))
    category = relationship("BlogCategory", back_populates="posts")
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan")

# ================================================
# ✅ BLOGGKATEGORIER
# ================================================
class BlogCategory(db.Model):
    """Kategorier för blogginlägg."""
    __tablename__ = 'blog_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # URL-vänligt namn
    title = db.Column(db.String(100), nullable=False)             # Visningsnamn
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(250), nullable=True)

    # Relation
    posts = db.relationship("BlogPost", back_populates="category", cascade="all, delete")

# ================================================
# ✅ KOMMENTARER
# ================================================
class Comment(db.Model):
    """Kommentarer på blogginlägg."""
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

    # Relationer
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    post = db.relationship("BlogPost", back_populates="comments")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = db.relationship("User")

# ================================================
# ✅ PORTFOLIO-KATEGORIER
# ================================================
class Category(db.Model):
    """Kategorier för portfolio-projekt."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(100), nullable=True)  # Genrebild för kategorin

    # Relation
    items = db.relationship('PortfolioItem', back_populates='category_obj', lazy=True)

# ================================================
# ✅ PORTFOLIO-PROJEKT
# ================================================
class PortfolioItem(db.Model):
    """Enskilt portfolio-projekt."""
    __tablename__ = 'portfolio_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(LONGTEXT, nullable=False)
    image = db.Column(db.String(100))  # Unik bild för varje projekt
    date = db.Column(db.DateTime)

    # Relation
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category_obj = db.relationship('Category', back_populates='items')

# ================================================
# ✅ CV-INNEHÅLL
# ================================================
class CVContent(db.Model):
    """CV-sektioner (för statisk CV-sida)."""
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

# ================================================
# ✅ SIDVISNINGAR
# ================================================
class PageView(db.Model):
    """Räknar sidvisningar (för statistik)."""
    __tablename__ = "page_views"

    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(255), unique=True, nullable=False)
    views = db.Column(db.Integer, default=0, nullable=False)