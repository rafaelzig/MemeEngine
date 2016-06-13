from __future__ import unicode_literals

from mongoengine import Document, StringField, IntField, FloatField, URLField, EmbeddedDocumentField, EmbeddedDocument, \
	MapField, LongField, ListField


# Create your models here.


class MemeId(EmbeddedDocument):
	meta = {"allow_inheritance": False}
	source = StringField(required=True)
	meme_id = StringField(required=True)

	def __repr__(self):
		return self.meme_id + "@" + self.source


class Meme(Document):
	meta = {"collection": "memes", "allow_inheritance": False}
	id = EmbeddedDocumentField(MemeId, db_field="_id", required=True, primary_key=True)
	postings = MapField(field=IntField(), required=True)
	name = StringField(required=True)
	title = StringField(required=True)
	caption = StringField(required=True)
	length = IntField(required=True, min_value=1)
	score = IntField(required=True)
	url = URLField(required=True)
	image = URLField(required=True)

	def __repr__(self):
		return self.to_json()


class SearchResult(EmbeddedDocument):
	meta = {"collection": "results", "allow_inheritance": False}
	id = EmbeddedDocumentField(MemeId, db_field="_id", required=True, primary_key=True)
	name = StringField(required=True)
	title = StringField(required=True)
	caption = StringField(required=True)
	score = IntField(required=True)
	url = URLField(required=True)
	image = URLField(required=True)
	bm25 = FloatField(required=True, min_value=0.0)


class Entry(Document):
	meta = {"collection": "dictionary", "allow_inheritance": False}
	id = StringField(required=True, db_field="_id", primary_key=True)
	total_frequency = IntField(required=True, min_value=1)
	total_documents = IntField(required=True, min_value=1)


class Query(Document):
	meta = {"collection": "queries", "allow_inheritance": False}
	id = StringField(required=True, db_field="_id", primary_key=True)
	results = ListField(EmbeddedDocumentField(SearchResult), ordering="bm25", reverse=True)
	total_frequency = LongField(required=True, min_value=0)
