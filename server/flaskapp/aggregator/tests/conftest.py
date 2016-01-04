# -*- coding: utf-8 -*-

import pytest
from py2neo import Graph


@pytest.fixture(scope='module')
def graph(request):
    return Graph("http://localhost:7474/db/data")
