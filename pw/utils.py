# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, request


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)


def xstr(s):
    return s or ''


def calc_page_num(current_page_number, total_page_number):
    if total_page_number <= 7:
        start_page_number, end_page_number = 1, total_page_number
    elif current_page_number - 3 < 1:
        start_page_number, end_page_number = 1, 7
    elif current_page_number + 3 > total_page_number:
        start_page_number, end_page_number = total_page_number - 6, total_page_number
    else:
        start_page_number, end_page_number = current_page_number - 3, current_page_number + 3

    return start_page_number, end_page_number


def get_pagination_kwargs(d, current_page_number, total_page_number):
    d['current_page_number'] = current_page_number
    d['total_page_number'] = total_page_number
    d['start_page_number'], d['end_page_number'] = \
        calc_page_num(d['current_page_number'], d['total_page_number'])


def paginate(query_set):
    current_page_number=request.args.get('page', default=1, type=int)
    number_per_page = 100
    results = query_set.paginate(current_page_number, paginate_by=number_per_page)
    total_page_number = results.pages
    kwargs = dict(data=results, number_per_page=number_per_page)
    get_pagination_kwargs(kwargs, current_page_number, total_page_number)
    return kwargs


def convert_user_ids_to_dict(user_ids):
    # session['user_id'] = '<wiki_group_1>-<wiki_user_id_1>,<wiki_group_2>-<wiki_user_id_2>,...'
    user_id_dict = dict()
    if user_ids is not None:
        user_id_list = user_ids.split(',')
        for user_str in user_id_list:
            wiki_group, _id = user_str.split('-')
            user_id_dict[wiki_group] = _id
    return user_id_dict


def convert_dict_to_user_ids(user_id_dict):
    user_id_list = list()
    for wiki_group, _id in user_id_dict.items():
        user_id_list.append('{0}-{1}'.format(wiki_group, _id))
    return ','.join(user_id_list)