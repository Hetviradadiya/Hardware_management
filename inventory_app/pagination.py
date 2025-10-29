from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PaginationWithPageCount(PageNumberPagination):
    """
    Base pagination that adds page info (count, total_pages, etc.)
    to the response.
    """
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'rows_per_page': self.page_size,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'status': True,
            'results': data,
        })


class ListPagination(PaginationWithPageCount):
    """
    Standard pagination for GET-based APIs.
    Supports dynamic 'page_size' and 'row_per_page' query params.
    """
    page_size = 10
    max_page_size = 100
    page_query_param = 'page'

    def get_page_size(self, request):
        page_size = super().get_page_size(request)
        if 'row_per_page' in request.query_params:
            page_size = int(request.query_params['row_per_page'])
        if 'page_size' in request.query_params:
            page_size = int(request.query_params['page_size'])
        return page_size
