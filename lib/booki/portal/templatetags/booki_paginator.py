from django import template
 
register = template.Library()
 
LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
NUM_PAGES_OUTSIDE_RANGE = 2 
ADJACENT_PAGES = 4
 
#ADJACENT_PAGES = 3
#NUM_PAGES_OUTSIDE_RANGE = 3
#WIDTH = 2*ADJACENT_PAGES + NUM_PAGES_OUTSIDE_RANGE
#LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = WIDTH + 2
#LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = WIDTH

# does not really work, must check it
def booki_paginator(context, pages):
    in_leading_range = in_trailing_range = False
    pages_outside_leading_range = pages_outside_trailing_range = range(0)
    current =  2

    if (pages.paginator.num_pages <= LEADING_PAGE_RANGE_DISPLAYED+NUM_PAGES_OUTSIDE_RANGE + 1):
        in_leading_range = in_trailing_range = True
        page_numbers = [n for n in range(1, pages.paginator.num_pages + 1) if n > 0 and n <= pages.paginator.num_pages]           
    elif (pages.number <= LEADING_PAGE_RANGE):
        in_leading_range = True
        page_numbers = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1) if n > 0 and n <= pages.paginator.num_pages]
        pages_outside_leading_range = [n + pages.paginator.num_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
    elif (pages.number > pages.paginator.num_pages - TRAILING_PAGE_RANGE):
        in_trailing_range = True
        page_numbers = [n for n in range(pages.paginator.num_pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, pages.paginator.num_pages + 1) if n > 0 and n <= pages.paginator.num_pages]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    else: 
        page_numbers = [n for n in range(pages.number - ADJACENT_PAGES, pages.number + ADJACENT_PAGES + 1) if n > 0 and n <= pages.paginator.num_pages]
        pages_outside_leading_range = [n + pages.paginator.num_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

    return {
        "previous": pages.previous_page_number(),
        "has_previous": pages.has_previous(),
        "next": pages.next_page_number(),
        "has_next": pages.has_next(),
        "page": pages.number,
        "results_per_page": 50,
        "page_numbers": page_numbers,
        "in_leading_range" : in_leading_range,
        "in_trailing_range" : in_trailing_range,
        "pages_outside_leading_range": pages_outside_leading_range,
        "pages_outside_trailing_range": pages_outside_trailing_range
        }

register.inclusion_tag("booki_paginator.html", takes_context=True)(booki_paginator)
