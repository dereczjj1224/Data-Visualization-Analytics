# coding: utf-8
from flask import url_for
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from bipolo import db

Base = declarative_base()
metadata = Base.metadata


def get_user_url(id):
    return url_for('get_user', id=id, reviews='Y', tips='Y')


def get_business_url(id):
    return url_for('get_business', id=id, reviews='Y',
                   attributes='Y',
                   hours='Y',
                   checkins='Y',
                   categories='Y')


class BasicMixin(object):

    @classmethod
    def get(cls, id):
        return db.session.query(cls).get(id)

    @classmethod
    def first(cls):
        return db.session.query(cls).first()

    @classmethod
    def list(cls):
        return db.session.query(cls).all()


class Cities_And_Counties(Base, BasicMixin):
    __tablename__ = 'CitiesAndCounties'
    city = Column(Text)
    city_ascii = Column(Text)
    state_id = Column(Text)
    state_name = Column(Text)
    county_name = Column(Text)
    county_fips = Column(Integer)
    zip = Column(Text)
    lat = Column(Float(asdecimal=True))
    lng = Column(Float(asdecimal=True))
    population = Column(Integer)
    source = Column(Text)
    id = Column(Integer, primary_key=True)

    def to_json(self):
        return {
            'city': self.city,
            'city_ascii': self.city_ascii,
            'state_id': self.state_id,
            'state_name': self.state_name,
            'county_name': self.county_name,
            'county_fips': self.county_fips,
            'zip': self.zip,
            'lat': self.lat,
            'lng': self.lng,
            'population': self.population,
            'source': self.source,
            'id': self.id
        }


class Attribute(Base, BasicMixin):
    __tablename__ = 'attribute'
    business_id = Column(String, ForeignKey(u'business.id'), nullable=False, index=True, primary_key=True)
    name = Column(String(255), primary_key=True)
    value = Column(Text)

    def to_json(self):
        return {
            #'business_id': self.business_id,
            #'business_url': get_business_url(self.business_id),
            'name': self.name,
            'value': self.value  # TODO - may need to convert to json as this can be value or dict
        }


class Business(Base, BasicMixin):
    __tablename__ = 'business'
    id = Column(String(22), primary_key=True)
    name = Column(String(255))
    neighborhood = Column(String(255))
    address = Column(String(255))
    city = Column(String(255))
    state = Column(String(255))
    postal_code = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    stars = Column(Float)
    review_count = Column(Integer)
    is_open = Column(Integer)

    categories = relationship('Category')
    checkins = relationship('Checkin')
    hours = relationship('Hours')
    reviews = relationship('Review')
    tips = relationship('Tip')
    attributes = relationship('Attribute')

    def to_json(self, inc_reviews=True,
                inc_attrs=True,
                inc_hours=False,
                inc_checkins=False,
                inc_categories=True):
        result = {
            'id': self.id,
            'business_url': get_business_url(self.id),
            'name': self.name,
            'neighborhood': self.neighborhood,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'stars': self.stars,
            'review_count': self.review_count,
            'is_open': self.is_open
        }

        if inc_reviews:
            result['reviews'] = [r.to_json() for r in self.reviews]
        if inc_attrs:
            result['attributes'] = [a.to_json() for a in self.attributes]
        if inc_hours:
            result['hours'] = [h.to_json() for h in self.hours]
        if inc_checkins:
            result['checkins'] = [a.to_json() for a in self.checkins]
        if inc_categories:
            result['categories'] = [a.to_json() for a in self.categories]
        return result

    def __str__(self):
        return "Business({}, name={}, postal={})".format(self.id, self.name, self.postal_code)


class Category(Base, BasicMixin):
    __tablename__ = 'category'
    business_id = Column(String, ForeignKey(u'business.id'), nullable=False, index=True, primary_key=True)
    category = Column(String(255), primary_key=True)

    def to_json(self):
        return {
            # 'business_id': self.business_id,
            # 'business_url': get_business_url(self.business_id),
            'category': self.category
        }


class Checkin(Base, BasicMixin):
    __tablename__ = 'checkin'
    business_id = Column(String, ForeignKey(u'business.id'), nullable=False, index=True, primary_key=True)
    date = Column(String(255), primary_key=True)
    count = Column(Integer)

    def to_json(self):
        return {
            # 'business_id': self.business_id,
            # 'business_url': get_business_url(self.business_id),
            'date': self.date,
            'count': self.count
        }


class EliteYears(Base, BasicMixin):
    __tablename__ = 'elite_years'
    user_id = Column(String, ForeignKey(u'user.id'), nullable=False, index=True, primary_key=True)
    year = Column(String(4), primary_key=True)

    def to_json(self):
        return {
            'user_id': self.user_id,
            'user_url': get_user_url(self.user_id),
            'year': self.year,
        }


class Hours(Base, BasicMixin):
    __tablename__ = 'hours'
    hours = Column(String(255), primary_key=True)
    business_id = Column(String, ForeignKey(u'business.id'), nullable=False, index=True, primary_key=True)

    def to_json(self):
        return {
            'hours': self.hours,
            # 'business_url': get_business_url(self.business_id),
            # 'business_id': self.business_id
        }


class Photo(Base, BasicMixin):
    __tablename__ = 'photo'
    id = Column(String(22), primary_key=True)
    business_id = Column(String, ForeignKey(u'business.id'), nullable=False, index=True)
    caption = Column(String(255))
    label = Column(String(255))

    def to_json(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'business_url': get_business_url(self.business_id),
            'caption': self.caption,
            'label': self.label
        }


class Review(Base, BasicMixin):
    __tablename__ = 'review'
    id = Column(String(22), primary_key=True)
    stars = Column(Integer)
    date = Column(DateTime)
    text = Column(Text)
    useful = Column(Integer)
    funny = Column(Integer)
    cool = Column(Integer)
    business_id = Column(String, ForeignKey(u'business.id'), nullable=False, index=True)
    business = relationship('Business', back_populates='reviews')
    user_id = Column(String, ForeignKey(u'user.id'), nullable=False, index=True)
    user = relationship('User', back_populates='reviews')

    def __str__(self):
        return "Review({}, business_id={}, user_id={})".format(self.id, self.business_id, self.user_id)

    def to_json(self):
        return {
            'id': self.id,
            'stars': self.stars,
            'date': self.date,
            'text': self.text,
            'useful': self.useful,
            'funny': self.funny,
            'cool': self.cool,
            'business_id': self.business_id,
            #'business_url': get_business_url(self.business_id),
            'user_id': self.user_id,
            #'user_url': get_user_url(self.user_id),
        }


class Tip(Base, BasicMixin):
    __tablename__ = 'tip'
    business_id = Column(String, ForeignKey(u'business.id'), nullable=False, index=True, primary_key=True)
    user_id = Column(String, ForeignKey(u'user.id'), nullable=False, index=True, primary_key=True)
    text = Column(Text)
    date = Column(DateTime, primary_key=True)
    likes = Column(Integer)

    def to_json(self):
        return {
            'business_id': self.business_id,
            'business_url': get_business_url(self.business_id),
            'user_id': self.user_id,
            'user_url': get_user_url(self.user_id),
            'text': self.text,
            'date': self.date,
            'likes': self.likes
        }


class User(Base, BasicMixin):
    __tablename__ = 'user'
    id = Column(String(22), primary_key=True)
    name = Column(String(255))
    review_count = Column(Integer)
    yelping_since = Column(DateTime)
    useful = Column(Integer)
    funny = Column(Integer)
    cool = Column(Integer)
    fans = Column(Integer)
    average_stars = Column(Float)
    compliment_hot = Column(Integer)
    compliment_more = Column(Integer)
    compliment_profile = Column(Integer)
    compliment_cute = Column(Integer)
    compliment_list = Column(Integer)
    compliment_note = Column(Integer)
    compliment_plain = Column(Integer)
    compliment_cool = Column(Integer)
    compliment_funny = Column(Integer)
    compliment_writer = Column(Integer)
    compliment_photos = Column(Integer)

    elite_years = relationship(EliteYears)
    reviews = relationship(Review)
    tips = relationship(Tip)

    def get_review_by_id(self, review_id):
        for r in self.reviews:
            if r.id == review_id:
                return r

    def to_json(self, inc_reviews=False, inc_tips=False):
        result = {
            'id': self.id,
            'name': self.name,
            'review_count': self.review_count,
            'yelping_since': self.yelping_since,
            'useful': self.useful,
            'funny': self.funny,
            'cool': self.cool,
            'fans': self.fans,
            'average_stars': self.average_stars,
            'compliment_hot': self.compliment_hot,
            'compliment_more': self.compliment_more,
            'compliment_profile': self.compliment_profile,
            'compliment_cute': self.compliment_cute,
            'compliment_list': self.compliment_list,
            'compliment_note': self.compliment_note,
            'compliment_plain': self.compliment_plain,
            'compliment_cool': self.compliment_cool,
            'compliment_funny': self.compliment_funny,
            'compliment_writer': self.compliment_writer,
            'compliment_photos': self.compliment_photos,
        }
        if inc_reviews:
            result['reviews'] = [r.to_json() for r in self.reviews]
        if inc_tips:
            result['tips'] = [t.to_json() for t in self.tips]
        return result

    def get_reviewed_businesses(self):
        return set([r.business for r in self.reviews])

    def __str__(self):
        return "User({})".format(self.id)


class Friend(Base, BasicMixin):
    __tablename__ = 'friend'
    user_id = Column(String, ForeignKey(u'user.id'), nullable=False, index=True, primary_key=True)
    user = relationship("User", primaryjoin=user_id == User.id, backref='friends')

    # Don't join this with a friend just yet
    friend_id = Column(String(22), ForeignKey('user.id'), primary_key=True, nullable=True)
    friend = relationship("User", primaryjoin=friend_id == User.id)

    def to_json(self):
        return {
            'user_id': self.user_id,
            'user_url': get_user_url(self.user_id),
            'friend_id': self.friend_id,
            'friend_url': get_user_url(self.friend_id),
        }

    def __str__(self):
        return "Friend({}, friend={})".format(self.user_id, self.friend_id)


cities_and_counties = Cities_And_Counties.__table__
attribute = Attribute.__table__
business = Business.__table__
category = Category.__table__
checkin = Checkin.__table__
elite_years = EliteYears.__table__
friend = Friend.__table__
hours = Hours.__table__
photo = Photo.__table__
review = Review.__table__
tip = Tip.__table__
user = User.__table__
