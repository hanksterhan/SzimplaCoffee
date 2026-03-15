from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    canonical_domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    homepage_url: Mapped[str] = mapped_column(String(500))
    platform_type: Mapped[str] = mapped_column(String(50), default="unknown", index=True)
    country_code: Mapped[str] = mapped_column(String(8), default="US")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    crawl_tier: Mapped[str] = mapped_column(String(1), default="B", index=True)
    trust_tier: Mapped[str] = mapped_column(String(32), default="candidate", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    quality_profile: Mapped[Optional["MerchantQualityProfile"]] = relationship(back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    personal_profile: Mapped[Optional["MerchantPersonalProfile"]] = relationship(back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    shipping_policies: Mapped[list["ShippingPolicy"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    promos: Mapped[list["PromoSnapshot"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    current_promos: Mapped[list["MerchantPromo"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    purchases: Mapped[list["PurchaseHistory"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    crawl_runs: Mapped[list["CrawlRun"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    field_patterns: Mapped[list["MerchantFieldPattern"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    metadata_overrides: Mapped[list["ProductMetadataOverride"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")


class MerchantCandidate(Base):
    __tablename__ = "merchant_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    merchant_name: Mapped[str] = mapped_column(String(255))
    homepage_url: Mapped[str] = mapped_column(String(500))
    source_query: Mapped[str] = mapped_column(String(255), default="")
    platform_type: Mapped[str] = mapped_column(String(50), default="unknown")
    confidence: Mapped[float] = mapped_column(Float, default=0.3)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class MerchantSource(Base):
    __tablename__ = "merchant_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    source_type: Mapped[str] = mapped_column(String(32))
    source_value: Mapped[str] = mapped_column(String(500))
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class MerchantQualityProfile(Base):
    __tablename__ = "merchant_quality_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), unique=True)
    freshness_transparency_score: Mapped[float] = mapped_column(Float, default=0.5)
    shipping_clarity_score: Mapped[float] = mapped_column(Float, default=0.5)
    metadata_quality_score: Mapped[float] = mapped_column(Float, default=0.5)
    espresso_relevance_score: Mapped[float] = mapped_column(Float, default=0.5)
    service_confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    overall_quality_score: Mapped[float] = mapped_column(Float, default=0.5)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    merchant: Mapped[Merchant] = relationship(back_populates="quality_profile")


class MerchantPersonalProfile(Base):
    __tablename__ = "merchant_personal_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), unique=True)
    has_order_history: Mapped[bool] = mapped_column(Boolean, default=False)
    would_reorder: Mapped[bool] = mapped_column(Boolean, default=True)
    personal_trust_score: Mapped[float] = mapped_column(Float, default=0.5)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, default="")
    last_ordered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    merchant: Mapped[Merchant] = relationship(back_populates="personal_profile")


class ShippingPolicy(Base):
    __tablename__ = "shipping_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    free_shipping_threshold_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shipping_notes: Mapped[str] = mapped_column(Text, default="")
    estimated_delivery_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(String(500))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    merchant: Mapped[Merchant] = relationship(back_populates="shipping_policies")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("merchant_id", "external_product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    external_product_id: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(255), index=True)
    product_url: Mapped[str] = mapped_column(String(500))
    image_url: Mapped[str] = mapped_column(String(1000), default="")
    origin_text: Mapped[str] = mapped_column(Text, default="")
    origin_country: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    origin_region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    process_text: Mapped[str] = mapped_column(Text, default="")
    process_family: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    variety_text: Mapped[str] = mapped_column(Text, default="")
    roast_cues: Mapped[str] = mapped_column(Text, default="")
    roast_level: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    tasting_notes_text: Mapped[str] = mapped_column(Text, default="")
    metadata_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_source: Mapped[str] = mapped_column(String(32), default="unknown")
    product_category: Mapped[str] = mapped_column(String(32), default="coffee", index=True)
    is_single_origin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_espresso_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    merchant: Mapped[Merchant] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class MerchantFieldPattern(Base):
    __tablename__ = "merchant_field_patterns"
    __table_args__ = (UniqueConstraint("merchant_id", "field_name", "pattern"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(64), index=True)
    pattern: Mapped[str] = mapped_column(Text)
    normalized_value: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, default=0.95)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    merchant: Mapped[Merchant] = relationship(back_populates="field_patterns")


class ProductMetadataOverride(Base):
    __tablename__ = "product_metadata_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    external_product_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255), default="", index=True)
    origin_text: Mapped[str] = mapped_column(Text, default="")
    origin_country: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    origin_region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    process_text: Mapped[str] = mapped_column(Text, default="")
    process_family: Mapped[str] = mapped_column(String(32), default="unknown")
    variety_text: Mapped[str] = mapped_column(Text, default="")
    roast_cues: Mapped[str] = mapped_column(Text, default="")
    roast_level: Mapped[str] = mapped_column(String(32), default="unknown")
    tasting_notes_text: Mapped[str] = mapped_column(Text, default="")
    is_single_origin: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_espresso_recommended: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    metadata_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_source: Mapped[str] = mapped_column(String(32), default="override")
    note: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    merchant: Mapped[Merchant] = relationship(back_populates="metadata_overrides")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "external_variant_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    external_variant_id: Mapped[str] = mapped_column(String(128))
    label: Mapped[str] = mapped_column(String(255))
    weight_grams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    is_whole_bean: Mapped[bool] = mapped_column(Boolean, default=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    product: Mapped[Product] = relationship(back_populates="variants")
    offers: Mapped[list["OfferSnapshot"]] = relationship(back_populates="variant", cascade="all, delete-orphan")


class OfferSnapshot(Base):
    __tablename__ = "offer_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    price_cents: Mapped[int] = mapped_column(Integer)
    compare_at_price_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    subscription_price_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    source_url: Mapped[str] = mapped_column(String(500))

    variant: Mapped[ProductVariant] = relationship(back_populates="offers")


class PromoSnapshot(Base):
    __tablename__ = "promo_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    promo_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    details: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    estimated_value_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(String(500))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    merchant: Mapped[Merchant] = relationship(back_populates="promos")


class MerchantPromo(Base):
    __tablename__ = "merchant_promos"
    __table_args__ = (UniqueConstraint("merchant_id", "promo_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    promo_key: Mapped[str] = mapped_column(String(128), index=True)
    promo_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    details: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    estimated_value_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_urls: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    merchant: Mapped[Merchant] = relationship(back_populates="current_promos")


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    origin_text: Mapped[str] = mapped_column(Text, default="")
    process_text: Mapped[str] = mapped_column(Text, default="")
    price_cents: Mapped[int] = mapped_column(Integer)
    weight_grams: Mapped[int] = mapped_column(Integer)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source_system: Mapped[str] = mapped_column(String(64), default="seed")
    source_ref: Mapped[str] = mapped_column(String(255), default="")

    merchant: Mapped[Merchant] = relationship(back_populates="purchases")
    brew_feedback: Mapped[list["BrewFeedback"]] = relationship(back_populates="purchase", cascade="all, delete-orphan")


class BrewFeedback(Base):
    __tablename__ = "brew_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchase_history.id"), index=True)
    shot_style: Mapped[str] = mapped_column(String(64))
    grinder: Mapped[str] = mapped_column(String(128), default="")
    basket: Mapped[str] = mapped_column(String(128), default="")
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    would_rebuy: Mapped[bool] = mapped_column(Boolean, default=True)
    difficulty_score: Mapped[float] = mapped_column(Float, default=0.5)
    notes: Mapped[str] = mapped_column(Text, default="")

    purchase: Mapped[PurchaseHistory] = relationship(back_populates="brew_feedback")


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    run_type: Mapped[str] = mapped_column(String(64))
    adapter_name: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="started")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    records_written: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str] = mapped_column(Text, default="")

    merchant: Mapped[Merchant] = relationship(back_populates="crawl_runs")


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    request_json: Mapped[str] = mapped_column(Text, default="")
    top_result_json: Mapped[str] = mapped_column(Text, default="")
    alternatives_json: Mapped[str] = mapped_column(Text, default="")
    wait_recommendation: Mapped[bool] = mapped_column(Boolean, default=False)
    model_version: Mapped[str] = mapped_column(String(32), default="v1")
