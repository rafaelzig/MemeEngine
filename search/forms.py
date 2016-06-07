from django.forms import Form, CharField, TextInput
from nltk import PorterStemmer, RegexpTokenizer
from nltk.corpus import stopwords


class SearchForm(Form):
	tokenizer = RegexpTokenizer("\w+")
	stemmer = PorterStemmer()
	filtered = set()
	tokens = []
	query_id = ""

	query = CharField(min_length=1, max_length=100, label='',
					  widget=TextInput(attrs={"type": "search", "placeholder": "Enter your search query here !",
											  "class": "form-control", "size": "100%"}))

	def is_valid(self):
		self.normalize()
		return super(SearchForm, self).is_valid() and self.filtered is not None and len(self.filtered) > 0

	def normalize(self):
		while True:
			try:
				self.tokens = [self.stemmer.stem(token) for token in
							   self.tokenizer.tokenize(self.data["query"].lower())]
				self.filtered = set(self.tokens) - set(stopwords.words("english"))
			except LookupError:
				download("stopwords")
			else:
				break

	def get_query_info(self):
		return '+'.join(sorted(self.tokens)), {key: self.tokens.count(key) for key in self.filtered}
