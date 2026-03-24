# app/utils/pagination.py
"""
Centraliserad paginering för hela applikationen.

Användning:
    from app.utils.pagination import paginate_query
    
    # I din view:
    result = paginate_query(BlogPost.query, page=page, per_page=12)
    
    # I template:
    {% for post in result.items %}
        ...
    {% endfor %}
    
    # Paginering-kontroller:
    {% if result.has_prev %}
        <a href="{{ url_for('blog.index', page=result.page-1) }}">Föregående</a>
    {% endif %}
    
    Sida {{ result.page }} av {{ result.total_pages }}
    
    {% if result.has_next %}
        <a href="{{ url_for('blog.index', page=result.page+1) }}">Nästa</a>
    {% endif %}
"""

from dataclasses import dataclass
from typing import List, Any, Optional
from sqlalchemy.orm import Query


@dataclass
class PaginationResult:
    """
    Resultat från paginering.
    
    Attributes:
        items: Lista med objekt för nuvarande sida
        page: Nuvarande sidnummer (1-indexerad)
        per_page: Antal objekt per sida
        total: Totalt antal objekt
        total_pages: Totalt antal sidor
        has_prev: True om det finns en föregående sida
        has_next: True om det finns en nästa sida
        prev_page: Föregående sidnummer (None om första sidan)
        next_page: Nästa sidnummer (None om sista sidan)
    """
    items: List[Any]
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    prev_page: Optional[int] = None
    next_page: Optional[int] = None


def paginate_query(
    query: Query, 
    page: int, 
    per_page: int = 12,
    error_out: bool = True
) -> PaginationResult:
    """
    Paginerar en SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query-objekt att paginera
        page: Nuvarande sidnummer (1-indexerad)
        per_page: Antal objekt per sida (default: 12)
        error_out: Om True, raise 404 vid ogiltig sida (default: True)
    
    Returns:
        PaginationResult med all pagineringsdata
    
    Raises:
        werkzeug.exceptions.NotFound: Om page är ogiltig och error_out=True
    
    Example:
        >>> from app.models import BlogPost
        >>> result = paginate_query(BlogPost.query, page=2, per_page=10)
        >>> print(f"Visar {len(result.items)} av {result.total} inlägg")
        Visar 10 av 45 inlägg
        >>> print(f"Sida {result.page} av {result.total_pages}")
        Sida 2 av 5
    """
    if page < 1:
        if error_out:
            from flask import abort
            abort(404, description="Ogiltig sida")
        page = 1
    
    # Räkna totalt antal
    total = query.count()
    
    # Beräkna totalt antal sidor
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # Om page är större än total_pages
    if page > total_pages and error_out and total > 0:
        from flask import abort
        abort(404, description="Sidan finns inte")
    
    # Hämta items för denna sida
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    # Beräkna has_prev/has_next
    has_prev = page > 1
    has_next = page < total_pages
    
    # Beräkna prev_page/next_page
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    return PaginationResult(
        items=items,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        prev_page=prev_page,
        next_page=next_page
    )


def get_page_range(
    current_page: int, 
    total_pages: int, 
    max_pages: int = 5
) -> List[int]:
    """
    Genererar en lista med sidnummer för paginering-kontroller.
    
    Användbart för att visa "1 2 3 ... 8 9 10" istället för alla 100 sidor.
    
    Args:
        current_page: Nuvarande sida
        total_pages: Totalt antal sidor
        max_pages: Max antal sidnummer att visa (default: 5)
    
    Returns:
        Lista med sidnummer att visa
    
    Example:
        >>> get_page_range(5, 10, max_pages=5)
        [3, 4, 5, 6, 7]
        
        >>> get_page_range(1, 10, max_pages=5)
        [1, 2, 3, 4, 5]
        
        >>> get_page_range(10, 10, max_pages=5)
        [6, 7, 8, 9, 10]
    """
    if total_pages <= max_pages:
        return list(range(1, total_pages + 1))
    
    # Beräkna start och slut
    half = max_pages // 2
    
    if current_page <= half:
        # Början av listan
        return list(range(1, max_pages + 1))
    elif current_page >= total_pages - half:
        # Slutet av listan
        return list(range(total_pages - max_pages + 1, total_pages + 1))
    else:
        # Mitt i listan
        return list(range(current_page - half, current_page + half + 1))