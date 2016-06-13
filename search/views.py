from math import log

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.shortcuts import render

from forms import SearchForm
from models import Meme, Entry, Query, SearchResult, MemeId

L = 0.5  # Constant for BM25
B = 0.75  # Constant for BM25 - usually 0.75
K1 = 1.5  # Constant for BM25 - between 1.0 to 2.0)
K3 = 500  # Constant for BM25 - between 0 to 1000)
PAGE_RANGE = 5
DOCS_PER_PAGE = 21


def index(request):
	query = request.GET.get("query")
	if query:
		search_form = SearchForm({"query": query})
		context = {"search_form": search_form}
		if search_form.is_valid():
			cleaned_query, query_postings = search_form.get_query_info()
			context["query"] = query
			results = get_search_results(cleaned_query, query_postings)
			context["page_results"], context["page_range"] = get_page_results(results, request.GET.get("page", '1'))
	else:
		context = {"search_form": SearchForm()}
	return render(request, "index.html", context)


def get_page_results(results, page):
	paginator = Paginator(results, DOCS_PER_PAGE)
	try:
		page_results = paginator.page(page)
	except(PageNotAnInteger, EmptyPage):
		page_results = paginator.page(1)
	except InvalidPage:
		page_results = paginator.page(paginator.num_pages)

	index = page_results.number
	max_index = len(paginator.page_range)
	start_index = index - PAGE_RANGE if index >= PAGE_RANGE else 0
	end_index = index + PAGE_RANGE if index <= max_index - PAGE_RANGE else max_index
	page_range = list(paginator.page_range)[start_index:end_index]
	return page_results, page_range


def get_search_results(query_id, query_postings):
	# Check previously calculated queries for changes in the corpus
	query = Query.objects(id=query_id).only("results", "total_frequency").first()
	total_frequency = Entry.objects(id__in=query_postings.iterkeys()).only("total_frequency").sum("total_frequency")
	if not query or total_frequency != query.total_frequency:
		results = []
		avg_length = Meme.objects.only("length").aggregate_average("length")
		idf, relevant_docs = get_idf_relevant_docs(query_postings)
		for meme in relevant_docs:  # Iterate through relevant documents to calculate its score
			bm25 = calculate_bm25(avg_length, idf, meme, query_postings)
			result = SearchResult(id=MemeId(source=meme.id.source, meme_id=meme.id.meme_id),
								  name=meme.name, title=meme.title, caption=meme.caption,
								  score=meme.score, url=meme.url, image=meme.image, bm25=bm25)
			results.append(result)
		results = sorted(results, key=lambda result: result.bm25, reverse=True)[:200]
		query = Query(id=query_id, results=results, total_frequency=total_frequency)
		query.save()
	return query.results


def calculate_bm25(avg_length, idf, meme, query_postings):
	bm25 = 0
	K = (K1 * ((1 - B) + B * (meme.length / avg_length)))
	for term, query_freq in query_postings.iteritems():
		doc_freq = meme.postings.get(term)
		if doc_freq:  # If term exists in the document
			bm25 += idf[term] * (((K1 + 1) * doc_freq) / (K + doc_freq)) * (
				((K3 + 1) * query_freq) / (K3 + query_freq))
	return bm25


def get_idf_relevant_docs(query_postings):
	relevant_docs = {}
	idf = {}
	total_docs = Meme.objects.count()
	for term in query_postings:
		term_docs = 0
		dict_entry = Entry.objects(id=term).only("total_documents").first()
		if dict_entry:
			term_docs = dict_entry.total_documents
			relevant_docs.update({repr(meme.id): meme for meme in
								  Meme.objects(__raw__={"postings." + term: {"$exists": "true"}})})
		idf[term] = log((total_docs - term_docs + L) / (term_docs + L), 10)
	return idf, relevant_docs.values()
