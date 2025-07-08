# app/forms/__init__.py
from .auth_forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm
from .blog_forms import BlogPostForm, BlogCategoryForm, CategoryFilterForm
from .portfolio_forms import PortfolioForm, CategorySelectForm, CategorySelectItem
from .contact_forms import ContactForm
from .shared_forms import CommentForm, DeleteForm, UserUpdateForm,CvEditForm