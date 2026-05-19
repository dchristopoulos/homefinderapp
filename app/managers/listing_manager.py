import re

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session

from app.db.models.listing import Listing, ListingPriceHistory
from app.schemas.listing import ListingCreate, ListingFilter


def create_listing_in_db(db: Session, listing_in: ListingCreate) -> Listing:
    listing = Listing(**listing_in.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)

    # Record initial price in history
    price_history = ListingPriceHistory(listing_id=listing.id, price=listing.price)
    db.add(price_history)
    db.commit()

    return listing


def get_all_listings(db: Session) -> list[Listing]:
    return db.query(Listing).filter(*_has_listing_image()).all()


def _has_listing_image():
    return (
        Listing.image_url.isnot(None),
        func.trim(Listing.image_url) != "",
        Listing.image_url != "/static/listing-placeholder.svg",
    )


def _apply_listing_filters(query, listing_filter: ListingFilter):
    query = query.filter(*_has_listing_image())
    extracted_max_price = listing_filter.max_price
    extracted_min_beds = listing_filter.min_bedrooms
    extracted_type = listing_filter.property_type
    extracted_loc = listing_filter.location
    q_str = listing_filter.query

    if q_str:
        q_lower = q_str.lower()
        
        # 1. Parse Price: "under 5000", "< 1m", "max 200k"
        price_match = re.search(r'(?:under|max|<)\s*\$?\s*(\d+(?:\.\d+)?)\s*([km]?)', q_lower)
        if price_match and extracted_max_price is None:
            val = float(price_match.group(1))
            mult = price_match.group(2)
            if mult == 'k':
                val *= 1000
            elif mult == 'm':
                val *= 1000000
            extracted_max_price = int(val)
            
        # 2. Parse Beds
        bed_match = re.search(r'(\d+)\s*(?:bed|beds|bedroom|bedrooms)', q_lower)
        if bed_match and extracted_min_beds is None:
            extracted_min_beds = int(bed_match.group(1))
            
        # 3. Parse Type
        type_match = re.search(r'\b(villa|house|apartment|studio|duplex|loft)\b', q_lower)
        if type_match and not extracted_type:
            extracted_type = type_match.group(1)
            
        # 4. Parse Location
        loc_match = re.search(r'\bin\s+([a-z\s]+?)(?:\s+(?:under|max|<|\d+ beds?)|$)', q_lower)
        if loc_match and not extracted_loc:
            extracted_loc = loc_match.group(1).strip()

    if listing_filter.min_price is not None:
        query = query.filter(Listing.price >= listing_filter.min_price)
    if extracted_max_price is not None:
        query = query.filter(Listing.price <= extracted_max_price)
    if listing_filter.min_size is not None:
        query = query.filter(Listing.size >= listing_filter.min_size)
    if listing_filter.max_size is not None:
        query = query.filter(Listing.size <= listing_filter.max_size)
    if extracted_min_beds is not None:
        query = query.filter(Listing.bedrooms >= extracted_min_beds)
    if listing_filter.max_bedrooms is not None:
        query = query.filter(Listing.bedrooms <= listing_filter.max_bedrooms)
    if listing_filter.min_bathrooms is not None:
        query = query.filter(Listing.bathrooms >= listing_filter.min_bathrooms)
    if listing_filter.max_bathrooms is not None:
        query = query.filter(Listing.bathrooms <= listing_filter.max_bathrooms)
    if extracted_type:
        query = query.filter(Listing.property_type.ilike(f"%{extracted_type}%"))
    if listing_filter.furnished:
        query = query.filter(Listing.furnished == listing_filter.furnished)
    if extracted_loc:
        query = query.filter(Listing.location.ilike(f"%{extracted_loc}%"))
        
    if q_str:
        q = f"%{q_str}%"
        query = query.filter(
            or_(
                Listing.title.ilike(q),
                Listing.location.ilike(q),
                Listing.description.ilike(q),
            )
        )
    return query


def _apply_listing_sort(query, listing_filter: ListingFilter):
    order = asc if listing_filter.sort_order == "asc" else desc
    sort_column = {
        "price": Listing.price,
        "size": Listing.size,
        "bedrooms": Listing.bedrooms,
        "bathrooms": Listing.bathrooms,
        "created": Listing.id,
        "title": Listing.title,
    }.get(listing_filter.sort_by or "created", Listing.id)
    return query.order_by(order(sort_column), desc(Listing.id))


def get_filtered_listings(db: Session, listing_filter: ListingFilter) -> list[Listing]:
    query = _apply_listing_filters(db.query(Listing), listing_filter)
    query = _apply_listing_sort(query, listing_filter)
    return query.all()


def get_filtered_listings_paginated(
    db: Session,
    listing_filter: ListingFilter,
    *,
    page: int,
    page_size: int,
) -> tuple[list[Listing], int]:
    query = _apply_listing_filters(db.query(Listing), listing_filter)
    query = _apply_listing_sort(query, listing_filter)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_filtered_listings_summary(db: Session, listing_filter: ListingFilter) -> dict[str, int | float | None]:
    base_query = _apply_listing_filters(db.query(Listing), listing_filter)
    total, min_price, max_price, avg_price, avg_size = base_query.with_entities(
        func.count(Listing.id),
        func.min(Listing.price),
        func.max(Listing.price),
        func.avg(Listing.price),
        func.avg(Listing.size),
    ).one()
    return {
        "total": int(total or 0),
        "min_price": int(min_price) if min_price is not None else None,
        "max_price": int(max_price) if max_price is not None else None,
        "avg_price": round(float(avg_price), 2) if avg_price is not None else None,
        "avg_size": round(float(avg_size), 2) if avg_size is not None else None,
    }


def get_similar_listings(db: Session, listing: Listing, limit: int = 5) -> list[Listing]:
    return (
        db.query(Listing)
        .filter(*_has_listing_image())
        .filter(Listing.id != listing.id)
        .filter(Listing.location == listing.location)
        .order_by((Listing.price - listing.price).asc())
        .limit(limit)
        .all()
    )


def get_listing_by_id(db: Session, listing_id: int) -> Listing | None:
    return db.query(Listing).filter(*_has_listing_image(), Listing.id == listing_id).first()


def get_recommendation_candidates(
    db: Session,
    *,
    excluded_ids: set[int],
    preferred_locations: list[str],
    preferred_types: list[str],
    limit: int = 100,
) -> list[Listing]:
    query = db.query(Listing).filter(*_has_listing_image(), Listing.id.notin_(list(excluded_ids) or [-1]))
    if preferred_locations or preferred_types:
        query = query.filter(
            or_(
                Listing.location.in_(preferred_locations),
                Listing.property_type.in_(preferred_types),
            )
        )
    return query.limit(limit).all()


def delete_listing_by_id(db: Session, listing_id: int) -> bool:
    listing = get_listing_by_id(db, listing_id)
    if listing is None:
        return False
    db.delete(listing)
    db.commit()
    return True


def get_listing_market_pulse_data(db: Session) -> dict:
    total = db.query(func.count(Listing.id)).scalar() or 0
    if total == 0:
        return {
            "total": 0,
            "avg_price": 0.0,
            "avg_size": 0.0,
            "budget_count": 0,
            "mid_count": 0,
            "premium_count": 0,
            "luxury_count": 0,
            "top_locations": [],
        }

    stats = db.query(
        func.avg(Listing.price).label("avg_price"),
        func.avg(Listing.size).label("avg_size"),
    ).first()

    budget_count = db.query(func.count(Listing.id)).filter(Listing.price < 1000).scalar() or 0
    mid_count = db.query(func.count(Listing.id)).filter(Listing.price >= 1000, Listing.price < 2000).scalar() or 0
    premium_count = db.query(func.count(Listing.id)).filter(Listing.price >= 2000, Listing.price < 3500).scalar() or 0
    luxury_count = db.query(func.count(Listing.id)).filter(Listing.price >= 3500).scalar() or 0

    top_locations = (
        db.query(Listing.location, func.count(Listing.id).label("count"))
        .group_by(Listing.location)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    return {
        "total": total,
        "avg_price": round(float(stats.avg_price or 0.0), 2),
        "avg_size": round(float(stats.avg_size or 0.0), 2),
        "budget_count": budget_count,
        "mid_count": mid_count,
        "premium_count": premium_count,
        "luxury_count": luxury_count,
        "top_locations": [{"location": loc, "count": count} for loc, count in top_locations],
    }


def update_listing_by_id(
    db: Session,
    *,
    listing_id: int,
    title: str,
    price: int,
    location: str,
    size: int,
    bedrooms: int,
    bathrooms: int,
    property_type: str,
    furnished: str,
    description: str,
) -> Listing | None:
    listing = get_listing_by_id(db, listing_id)
    if listing is None:
        return None
    
    # Record price change if applicable
    if listing.price != price:
        price_history = ListingPriceHistory(listing_id=listing.id, price=price)
        db.add(price_history)

    listing.title = title
    listing.price = price
    listing.location = location
    listing.size = size
    listing.bedrooms = bedrooms
    listing.bathrooms = bathrooms
    listing.property_type = property_type
    listing.furnished = furnished
    listing.description = description
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def get_listing_price_history(db: Session, listing_id: int) -> list[ListingPriceHistory]:
    return (
        db.query(ListingPriceHistory)
        .filter(ListingPriceHistory.listing_id == listing_id)
        .order_by(asc(ListingPriceHistory.changed_at))
        .all()
    )
