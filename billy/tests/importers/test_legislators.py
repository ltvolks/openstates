import datetime

from nose.tools import with_setup

from billy import db
from billy.importers import legislators, utils


def setup_func():
    db.legislators.drop()
    db.metadata.drop()

    db.metadata.insert({'_id': 'ex',
                        'terms': [{'name': '2009-2010',
                                   'sessions': ['2009', '2010'],
                                   'start_year': 2009, 'end_year': 2010},
                                  {'name': '2011-2012',
                                   'sessions': ['2011'],
                                   'start_year': 2011, 'end_year': 2012}]})


@with_setup(setup_func)
def test_activate_legislators():
    # Previous term
    leg1 = {'_type': 'person', 'state': 'ex',
            'roles': [{'type': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2009-2010', 'district': '1',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}]}

    # Current term, no end date
    leg2 = {'_type': 'person', 'state': 'ex',
            'roles': [{'type': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2011-2012', 'district': '2',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}]}

    # Current term, end date
    leg3 = {'_type': 'person', 'state': 'ex',
            'roles': [{'type': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2011-2012', 'district': '3',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': datetime.datetime.now()}]}

    id1 = utils.insert_with_id(leg1)
    id2 = utils.insert_with_id(leg2)
    id3 = utils.insert_with_id(leg3)

    legislators.activate_legislators('ex', '2011-2012')
    assert 'active' not in leg1
    assert 'district' not in leg1
    assert 'chamber' not in leg1
    assert 'party' not in leg1

    leg2 = db.legislators.find_one({'_id': id2})
    assert leg2['active'] == True
    assert leg2['district'] == '2'
    assert leg2['chamber'] == 'upper'
    assert leg2['party'] == 'Democrat'

    leg3 = db.legislators.find_one({'_id': id3})
    assert 'active' not in leg3
    assert 'district' not in leg3
    assert 'chamber' not in leg3
    assert 'party' not in leg3


@with_setup(setup_func)
def test_deactivate_legislators():
    # Previous term
    leg1 = {'_type': 'person', 'state': 'ex',
            'roles': [{'type': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2009-2010', 'district': '1',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}],
            'active': True,
            'district': '1',
            'chamber': 'upper',
            'party': 'Democrat'}
    leg1_roles = leg1['roles']

    # Current term, no end date
    leg2 = {'_type': 'person', 'state': 'ex',
            'roles': [{'type': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2011-2012', 'district': '2',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}],
            'active': True,
            'district': '2',
            'chamber': 'upper',
            'party': 'Democrat'}
    leg2_roles = leg2['roles']

    id1 = utils.insert_with_id(leg1)
    id2 = utils.insert_with_id(leg2)

    legislators.deactivate_legislators('ex', '2011-2012')

    leg1 = db.legislators.find_one({'_id': id1})
    assert leg1['active'] == False
    assert 'chamber' not in leg1
    assert 'district' not in leg1
    assert 'party' not in leg1
    assert leg1['roles'] == []
    assert leg1['old_roles']['2009-2010'] == leg1_roles

    leg2 = db.legislators.find_one({'_id': id2})
    assert leg2['active'] == True
    assert leg2['chamber'] == 'upper'
    assert leg2['district'] == '2'
    assert leg2['party'] == 'Democrat'
    assert leg2['roles'] == leg2_roles
    assert 'old_roles' not in leg2


@with_setup(setup_func)
def test_get_previous_term():
    prev = legislators.get_previous_term('ex', '2011-2012')
    assert prev == '2009-2010'


@with_setup(setup_func)
def test_get_next_term():
    next_term = legislators.get_next_term('ex', '2009-2010')
    assert next_term == '2011-2012'


@with_setup(setup_func)
def test_import_legislator():
    leg1 = {'_type': 'person', 'state': 'ex',
            'full_name': 'T. Rex Hagan',
            'roles': [{'role': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2009-2010', 'district': '1',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}]}
    leg1_roles = leg1['roles']

    leg2 = {'_type': 'person', 'state': 'ex',
            'full_name': 'T. Rex Hagan',
            'roles': [{'role': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2011-2012', 'district': '1',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}]}

    leg3 = {'_type': 'person', 'state': 'ex',
            'full_name': 'Joe Heck',
            'roles': [{'role': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2009-2010', 'district': '2',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}]}

    leg4 = {'_type': 'person', 'state': 'ex',
            'full_name': 'Bob Dold',
            'roles': [{'role': 'member', 'chamber': 'upper', 'state': 'ex',
                       'term': '2011-2012', 'district': '2',
                       'party': 'Democrat',
                       'start_date': None, 'end_date': None}]}


    legislators.import_legislator(leg1)
    assert db.legislators.count() == 1

    legislators.import_legislator(leg2)
    t_rex = db.legislators.find_one({'_scraped_name': 'T. Rex Hagan'})
    assert db.legislators.count() == 1
    assert t_rex['roles'][0]['term'] == '2011-2012'
    assert '2009-2010' in t_rex['old_roles']

    legislators.import_legislator(leg3)
    assert db.legislators.count() == 2


    legislators.import_legislator(leg4)
    assert db.legislators.count() == 3
