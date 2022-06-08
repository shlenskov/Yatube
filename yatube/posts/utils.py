from django.core.paginator import Paginator

COUNT_POST = 10


def get_page(queryset, request):
    paginator = Paginator(queryset, COUNT_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
