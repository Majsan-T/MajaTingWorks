# app/utils/search.py
"""
Centraliserad sökfunktionalitet för hela applikationen.

Användning:
    from app.utils.search import search_posts, SearchFilter
    
    # Enkel sökning:
    query = BlogPost.query
    query = search_posts(query, BlogPost, search_term="flask python")
    
    # Avancerad sökning med filter:
    filters = SearchFilter(
        term="flask",
        fields=['title', 'subtitle', 'body'],
        match_all_words=True
    )
    query = apply_search_filter(query, BlogPost, filters)
"""

from sqlalchemy import or_, and_
from typing import List, Optional, Type
from dataclasses import dataclass


@dataclass
class SearchFilter:
    """
    Konfiguration för sökfilter.
    
    Attributes:
        term: Söksträng
        fields: Lista med fältnamn att söka i
        match_all_words: Om True, alla ord måste matcha (AND). 
                        Om False, minst ett ord måste matcha (OR)
        case_sensitive: Om True, skiftlägeskänslig sökning
    """
    term: str
    fields: List[str]
    match_all_words: bool = False
    case_sensitive: bool = False


def search_posts(
    query, 
    model: Type,
    search_term: str,
    fields: Optional[List[str]] = None,
    match_all_words: bool = False
):
    """
    Enkel sökfunktion - söker i flera fält.
    
    Args:
        query: SQLAlchemy query-objekt
        model: Modellklass (t.ex. BlogPost)
        search_term: Söksträng från användaren
        fields: Lista med fältnamn att söka i (default: ['title', 'body'])
        match_all_words: Om True, alla ord måste matcha
    
    Returns:
        Filtrerad query
    
    Example:
        >>> from app.models import BlogPost
        >>> query = BlogPost.query
        >>> query = search_posts(query, BlogPost, "flask python", 
        ...                      fields=['title', 'subtitle', 'body'])
        >>> posts = query.all()
    """
    if not search_term or not search_term.strip():
        return query
    
    if fields is None:
        fields = ['title', 'body']
    
    # Dela upp söktermen i ord
    words = search_term.strip().split()
    
    if match_all_words:
        # Alla ord måste matcha (AND)
        for word in words:
            pattern = f"%{word}%"
            conditions = [
                getattr(model, field).ilike(pattern) 
                for field in fields 
                if hasattr(model, field)
            ]
            if conditions:
                query = query.filter(or_(*conditions))
    else:
        # Minst ett ord måste matcha (OR)
        all_conditions = []
        for word in words:
            pattern = f"%{word}%"
            word_conditions = [
                getattr(model, field).ilike(pattern) 
                for field in fields 
                if hasattr(model, field)
            ]
            all_conditions.extend(word_conditions)
        
        if all_conditions:
            query = query.filter(or_(*all_conditions))
    
    return query


def apply_search_filter(query, model: Type, filters: SearchFilter):
    """
    Applicerar mer avancerade sökfilter.
    
    Args:
        query: SQLAlchemy query-objekt
        model: Modellklass
        filters: SearchFilter-objekt med konfiguration
    
    Returns:
        Filtrerad query
    """
    if not filters.term or not filters.term.strip():
        return query
    
    words = filters.term.strip().split()
    
    # Välj rätt operator beroende på case_sensitive
    def make_condition(field, pattern):
        if filters.case_sensitive:
            return getattr(model, field).like(pattern)
        else:
            return getattr(model, field).ilike(pattern)
    
    if filters.match_all_words:
        # AND - alla ord måste finnas
        for word in words:
            pattern = f"%{word}%"
            conditions = [
                make_condition(field, pattern)
                for field in filters.fields
                if hasattr(model, field)
            ]
            if conditions:
                query = query.filter(or_(*conditions))
    else:
        # OR - minst ett ord måste finnas
        all_conditions = []
        for word in words:
            pattern = f"%{word}%"
            for field in filters.fields:
                if hasattr(model, field):
                    all_conditions.append(make_condition(field, pattern))
        
        if all_conditions:
            query = query.filter(or_(*all_conditions))
    
    return query


def highlight_search_terms(text: str, search_term: str, 
                          highlight_class: str = "highlight") -> str:
    """
    Highlightar söktermer i texten (för visning).
    
    Args:
        text: Ursprunglig text
        search_term: Sökterm
        highlight_class: CSS-klass för highlighting
    
    Returns:
        Text med <span class="highlight">term</span> runt söktermer
    
    Example:
        >>> text = "Flask är ett Python-ramverk"
        >>> result = highlight_search_terms(text, "flask python")
        >>> print(result)
        <span class="highlight">Flask</span> är ett 
        <span class="highlight">Python</span>-ramverk
    """
    import re
    from markupsafe import Markup, escape
    
    if not search_term or not text:
        return text
    
    # Escape texten först
    safe_text = escape(text)
    
    words = search_term.split()
    for word in words:
        # Skapa regex-pattern (case-insensitive)
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        safe_text = pattern.sub(
            lambda m: f'<span class="{highlight_class}">{m.group(0)}</span>',
            str(safe_text)
        )
    
    return Markup(safe_text)


# Exempel på användning i en view:
"""
from app.utils.search import search_posts, SearchFilter
from app.utils.pagination import paginate_query

@blog_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    search_term = request.args.get("search", "").strip()
    
    # Bas-query
    query = BlogPost.query
    
    # Applicera sökning om det finns en sökterm
    if search_term:
        query = search_posts(
            query, 
            BlogPost, 
            search_term,
            fields=['title', 'subtitle', 'body']
        )
    
    # Sortera
    query = query.order_by(BlogPost.created_at.desc())
    
    # Paginera
    result = paginate_query(query, page=page, per_page=12)
    
    return render_template(
        'blog/blog.html',
        posts=result.items,
        pagination=result,
        search_term=search_term
    )
"""