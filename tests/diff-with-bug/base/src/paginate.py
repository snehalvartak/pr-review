def page_bounds(page, page_size):
    start = page * page_size
    end = start + page_size
    return start, end
